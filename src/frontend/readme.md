## Execute Ros2 Nodes for Ollama frontend
# Ollama docker
```bash
cd /home/operador/Documents/kamerdyner-dev &&
sudo docker compose -f ci-scripts/dockerfiles/ollama/docker-compose.yaml up -d --build
``` 
# Setup ROS2 Enviroment
```bash
source /opt/ros/jazzy/setup.bash
cd ~/Documents/kamerdyner-dev/ros_workspace
source install/setup.bash
```
# Ollama FrontEnd - Server
```bash
source /opt/ros/jazzy/setup.bash &&
cd /home/operador/Documents/kamerdyner-dev/ros_workspace &&
source install/setup.bash &&
ros2 run frontend frontend_server --ros-args \
  -p ollama_url:=http://localhost:11434 \
  -p default_model:=robot-router:latest
```

# Ollama FrontEnd - Client
```bash
source /opt/ros/jazzy/setup.bash &&
cd /home/operador/Documents/kamerdyner-dev/ros_workspace &&
source install/setup.bash &&
ros2 run frontend frontend_cli
```
