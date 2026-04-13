import json
import re
import time
from typing import Any, Dict, List, Tuple

import rclpy
from rclpy.action import ActionClient, ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
import requests

from high_level_reasoning_interface.action import ExecuteCommand
from high_level_reasoning_interface.action import OllamaChatInteraction as OllamaChatAction


class FrontendServer(Node):
    """
    FrontendServer: ROS 2 action server that calls Ollama and optionally routes
    command execution through the executive action server.

    Design goals (per your request):
    - The client never receives raw JSON from Ollama.
    - The LLM returns plain text in a strict two-line protocol:
        CLIENT_MESSAGE: ...
        COMMAND_STRING: <none|show_me_around|...>
    - The client gets execution feedback via the frontend action feedback channel.
    """

    def __init__(self):
        super().__init__("frontend_server")

        # Parameters
        self.declare_parameter("ollama_url", "http://localhost:11434")
        self.declare_parameter("default_model", "robot-router:latest")
        self.declare_parameter("timeout_sec", 120.0)

        self._callback_group = ReentrantCallbackGroup()

        self._execute_command_client = ActionClient(
            self,
            ExecuteCommand,
            "execute_command",
            callback_group=self._callback_group,
        )

        self._chat_action_server = ActionServer(
            self,
            OllamaChatAction,
            "/ollama/chat",
            self.handle_chat,
            callback_group=self._callback_group,
        )

        self.get_logger().info("frontend_server ready. Action: /ollama/chat")
        self.get_logger().info('Forwarding commands to action server: "execute_command"')

    # =========================
    # Public ROS2 entrypoint
    # =========================
    def handle_chat(self, goal_handle):
        """
        Pipeline:
          1) Read config + normalize request
          2) Call Ollama
          3) Parse strict router output (two-line protocol)
          4) If needed, send the parsed command to execute_command
          5) Return the final text + execution state to the action client
        """
        result = OllamaChatAction.Result()

        try:
            cfg = self.__read_config()
            prompt, model = self.__normalize_request(goal_handle.request, cfg["default_model"])

            self.__ensure_prompt(prompt)

            self.__publish_feedback(goal_handle, "querying_ollama")
            payload = self.__build_ollama_payload(model, prompt)
            self.get_logger().info(f'Ollama request -> model="{payload.get("model")}" prompt="{prompt}"')

            data = self.__call_ollama(cfg["ollama_url"], payload, cfg["timeout_sec"])
            llm_text = self.__extract_llm_text(data)

            # Parse the router output (plain text protocol)
            client_msg, command_string, landmarks_to_visit = self.__parse_router_output(llm_text)

            execution_status = "no_command"
            error = ""
            success = True

            if command_string != "none":
                self.__publish_feedback(goal_handle, f"command_detected:{command_string}")
                execute_result = self.__execute_command(
                    goal_handle,
                    command_string,
                    landmarks_to_visit,
                )
                execution_status = execute_result.status
                error = execute_result.error_description or ""
                success = execute_result.status == "completed"
            else:
                self.__publish_feedback(goal_handle, "no_command_detected")

            if success:
                goal_handle.succeed()
            else:
                goal_handle.abort()

            return self.__fill_result(
                result=result,
                success=success,
                error=error,
                text=client_msg,
                command_string=command_string,
                execution_status=execution_status,
            )

        except requests.exceptions.Timeout:
            goal_handle.abort()
            return self.__fill_result(
                result=result,
                success=False,
                error="Timeout calling Ollama",
                text="",
                command_string="none",
                execution_status="failed",
            )
        except requests.exceptions.ConnectionError:
            goal_handle.abort()
            return self.__fill_result(
                result=result,
                success=False,
                error="HighLevel Ollama Docker is not online",
                text="",
                command_string="none",
                execution_status="failed",
            )
        except Exception as e:
            goal_handle.abort()
            return self.__fill_result(
                result=result,
                success=False,
                error=str(e),
                text="",
                command_string="none",
                execution_status="failed",
            )

    # =========================
    # Private helpers (config + request)
    # =========================
    def __read_config(self) -> Dict[str, Any]:
        return {
            "ollama_url": self.get_parameter("ollama_url").value,
            "default_model": self.get_parameter("default_model").value,
            "timeout_sec": float(self.get_parameter("timeout_sec").value),
        }

    def __normalize_request(self, request, default_model: str) -> Tuple[str, str]:
        prompt = (request.prompt or "").strip()
        req_model = (request.model or "").strip()
        model = req_model if req_model else default_model
        return prompt, model

    def __ensure_prompt(self, prompt: str) -> None:
        if not prompt:
            raise ValueError("Empty prompt")

    def __publish_feedback(self, goal_handle, status: str) -> None:
        feedback = OllamaChatAction.Feedback()
        feedback.current_status = status
        goal_handle.publish_feedback(feedback)

    def __wait_for_future(self, future, timeout_sec: float, wait_label: str):
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and not future.done():
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timeout waiting for {wait_label}")
            time.sleep(0.05)
        return future.result()

    # =========================
    # Ollama call
    # =========================
    def __build_ollama_payload(self, model: str, prompt: str) -> Dict[str, Any]:
        # NOTE:
        # - Use /api/generate (simple completion)
        # - stream False for single JSON response
        return {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

    def __call_ollama(self, ollama_url: str, payload: Dict[str, Any], timeout_sec: float) -> Dict[str, Any]:
        r = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=timeout_sec,
        )

        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

        return r.json()

    def __extract_llm_text(self, data: Dict[str, Any]) -> str:
        # Ollama /api/generate returns: {"response": "...", ...}
        return (data.get("response") or "").strip()

    def __execute_command(
        self,
        goal_handle,
        command_string: str,
        landmarks_to_visit: List[str],
    ):
        self.__publish_feedback(goal_handle, f"waiting_for_execute_command:{command_string}")

        if not self._execute_command_client.wait_for_server(timeout_sec=5.0):
            raise RuntimeError("execute_command action server not available")

        exec_goal = ExecuteCommand.Goal()
        exec_goal.command = command_string
        exec_goal.landmarks_to_visit = landmarks_to_visit

        send_goal_future = self._execute_command_client.send_goal_async(
            exec_goal,
            feedback_callback=lambda feedback_msg: self.__handle_execute_feedback(
                goal_handle,
                feedback_msg,
            ),
        )
        goal_response = self.__wait_for_future(
            send_goal_future,
            timeout_sec=5.0,
            wait_label="execute_command goal response",
        )

        if goal_response is None or not goal_response.accepted:
            raise RuntimeError(f"execute_command rejected command '{command_string}'")

        self.__publish_feedback(goal_handle, f"executing:{command_string}")

        result_future = goal_response.get_result_async()
        wrapped_result = self.__wait_for_future(
            result_future,
            timeout_sec=300.0,
            wait_label=f"execute_command result for '{command_string}'",
        )

        if wrapped_result is None or wrapped_result.result is None:
            raise RuntimeError(f"execute_command returned no result for '{command_string}'")

        return wrapped_result.result

    def __handle_execute_feedback(self, goal_handle, feedback_msg) -> None:
        current_status = feedback_msg.feedback.current_status.strip()
        if current_status:
            self.__publish_feedback(goal_handle, f"executor:{current_status}")

    # =========================
    # Router output parsing (NO JSON)
    # =========================
    def __parse_router_output(self, text: str) -> Tuple[str, str, List[str]]:
        """
        Preferred format (two lines, plain text, no markdown):

          CLIENT_MESSAGE: <text>
          COMMAND_STRING: <none|show_me_around|MOVE|TURN|STOP|SPEAK|SCAN|PICKUP|DROP|STATUS>

        Legacy compatibility:
        - Accepts the older JSON router payload used by the Ollama Modelfile.

        Returns: (client_message, command_string, landmarks_to_visit)

        Robustness:
        - If the LLM fails to follow the protocol, we return the full text as client_message,
          "none" as command_string, and no landmarks.
        - If there is extra text, we still try to extract the two fields.
        """
        raw = (text or "").strip()
        if not raw:
            return "", "none", []

        client_msg = ""
        command_string = "none"
        landmarks_to_visit: List[str] = []

        # We accept any ordering, but these labels must appear.
        # Use regex to tolerate minor spacing differences.
        m1 = re.search(r"^\s*CLIENT_MESSAGE\s*:\s*(.+)\s*$", raw, flags=re.MULTILINE)
        m2 = re.search(r"^\s*COMMAND_STRING\s*:\s*(.+)\s*$", raw, flags=re.MULTILINE)

        if m1:
            client_msg = m1.group(1).strip()
        if m2:
            command_string = m2.group(1).strip()

        # Fallback to the legacy JSON router payload if the plain-text protocol is absent.
        if not client_msg and not m2:
            legacy_message, legacy_command, legacy_landmarks = self.__parse_router_json_output(raw)
            if legacy_message or legacy_command != "none":
                return legacy_message or raw, legacy_command, legacy_landmarks
            return raw, "none", []

        # Normalize command string
        command_string = command_string.strip() if command_string else "none"

        return client_msg or raw, command_string or "none", landmarks_to_visit

    def __parse_router_json_output(self, raw: str) -> Tuple[str, str, List[str]]:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return "", "none", []

        if not isinstance(payload, dict):
            return "", "none", []

        client_msg = str(payload.get("message") or "").strip()
        command = payload.get("command") or {}
        if not isinstance(command, dict):
            return client_msg, "none", []

        command_name = str(command.get("name") or "").strip() or "none"
        parameters = command.get("parameters") or {}
        landmarks = parameters.get("landmarks_to_visit") if isinstance(parameters, dict) else []

        if not isinstance(landmarks, list):
            landmarks = []

        normalized_landmarks = [
            str(landmark).strip()
            for landmark in landmarks
            if str(landmark).strip()
        ]
        return client_msg, command_name, normalized_landmarks

    def __fill_result(
        self,
        result,
        success: bool,
        error: str,
        text: str,
        command_string: str,
        execution_status: str,
    ):
        result.success = bool(success)
        result.error = error or ""
        result.response = text or ""
        result.command_string = command_string or "none"
        result.execution_status = execution_status or ""
        return result


def main():
    rclpy.init()
    node = FrontendServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
