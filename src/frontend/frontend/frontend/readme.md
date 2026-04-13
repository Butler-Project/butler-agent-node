#Execute Server:
```bash
ros2 run frontend frontend_server --ros-args   -p ollama_url:=http://localhost:11434   -p default_model:=robot-router:latest
```
# Client
```
ros2 run frontend frontend_cli
```
