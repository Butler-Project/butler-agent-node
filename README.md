# Interface Directory
This directory contains all ROS 2 interface definitions (messages, services, and actions) shared across Butler robot packages.

# HowTo
1.- Create the directory that you want to share interfaces with

---

## high_level_reasoning

ROS 2 interface package for the High Level Reasoning node. Defines the communication contracts between the HLR node, the LLM, and the rest of the robot stack.

### Actions

| File | Description |
|---|---|
| `ExecuteCommand.action` | Sends a navigation command (`command` + `landmarks_to_visit`) to the robot. Returns execution status and error description if it cannot be executed. |
| `OllamaChatInteraction.action` | Sends a `prompt` to a given Ollama `model`. Returns the model response, success flag, and parsed command string. |
| `SystemOperativeCheck.action` | Triggers a system readiness check (no goal fields). Returns whether the robot is operative and a list of issues if not. |

### Messages

| File | Description |
|---|---|
| `Pddl.msg` | Carries a PDDL planning state: timestamp, list of goals, and list of predicates. |
| `SystemState.msg` | Bitmask-based snapshot of robot subsystem health. Reports the state of map, localization, lidar, odometry, landmarks, Nav2, and AMCL using integer constants (OK/NOK). |

### Services

| File | Description |
|---|---|
| `OllamaChatInteraction.srv` | Synchronous version of the Ollama interaction: sends a `prompt` + `model`, returns `response`, `success`, and `error`. |
