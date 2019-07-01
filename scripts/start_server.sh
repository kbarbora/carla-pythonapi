#!/bin/bash

echo "Starting server"
bash /opt/9.5Carla/CarlaUE4.sh &
sleep 3
echo "Starting client with wheel and pedals support"
bash /opt/PythonAPI/script/start_joystick.py
