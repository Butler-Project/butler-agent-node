import sys
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from high_level_reasoning_interface.action import OllamaChatInteraction


class FrontendCli(Node):
    def __init__(self):
        super().__init__('frontend_cli')
        self.cli = ActionClient(self, OllamaChatInteraction, '/ollama/chat')
        while not self.cli.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('Esperando action /ollama/chat ...')

    def call(self, prompt: str, model: str = "") -> int:
        goal = OllamaChatInteraction.Goal()
        goal.prompt = prompt
        goal.model = model

        goal_future = self.cli.send_goal_async(
            goal,
            feedback_callback=self._feedback_callback,
        )
        rclpy.spin_until_future_complete(self, goal_future)

        goal_handle = goal_future.result()
        if goal_handle is None or not goal_handle.accepted:
            print("Action goal rejected")
            return 1

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        wrapped_result = result_future.result()
        if wrapped_result is None or wrapped_result.result is None:
            print("Action result failed")
            return 1

        res = wrapped_result.result
        if not res.success:
            print(f"[ERROR] {res.error}")
            return 1

        print(f"\033[32m{res.response}\033[0m")
        if res.command_string != "none":
            print(f"[COMMAND] {res.command_string}")
            print(f"[EXECUTION] {res.execution_status}")
        return 0

    def _feedback_callback(self, feedback_msg) -> None:
        status = feedback_msg.feedback.current_status.strip()
        if status:
            print(f"[STATUS] {status}")


def main():
    rclpy.init()
    node = FrontendCli()

    model = sys.argv[1] if len(sys.argv) > 1 else ""

    print('Interactive Ollama CLI. Type "exit" or "quit" to exit.')
    try:
        while True:
            prompt = input("Prompt> ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit"):
                break
            node.call(prompt, model)
    except (KeyboardInterrupt, EOFError):
        print()

    node.destroy_node()
    rclpy.shutdown()
