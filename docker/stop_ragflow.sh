#!/bin/bash

LOG_FILE="/var/log/ragflow_stop.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "-----------------------------------------------------------------" | tee -a "$LOG_FILE"
echo "$TIMESTAMP: Stopping RAGflow services..." | tee -a "$LOG_FILE"

# 停止前端服务
echo "$TIMESTAMP: Attempting to stop frontend service..." | tee -a "$LOG_FILE"
FRONTEND_PID=$(pgrep -f 'npm run dev')
if [ -n "$FRONTEND_PID" ]; then
  echo "$TIMESTAMP: Found frontend process with PID: $FRONTEND_PID. Attempting to kill it." | tee -a "$LOG_FILE"
  kill "$FRONTEND_PID" | tee -a "$LOG_FILE" 2>&1
  FRONTEND_STOP_STATUS=$?
  if [ "$FRONTEND_STOP_STATUS" -eq 0 ]; then
    echo "$TIMESTAMP: Frontend process stopped successfully." | tee -a "$LOG_FILE"
  else
    echo "$TIMESTAMP: ERROR: Failed to stop frontend process with PID $FRONTEND_PID, exit code $FRONTEND_STOP_STATUS." | tee -a "$LOG_FILE"
  fi
else
  echo "$TIMESTAMP: INFO: No frontend process ('npm run dev') found." | tee -a "$LOG_FILE"
fi

# 停止后端服务脚本
echo "$TIMESTAMP: Attempting to stop backend service script(s)..." | tee -a "$LOG_FILE"
BACKEND_SCRIPT_PIDS=$(pgrep -f '/root/ragflow/docker/launch_backend_service.sh')
if [ -n "$BACKEND_SCRIPT_PIDS" ]; then
  echo "$TIMESTAMP: Found backend service script processes with PIDs: $BACKEND_SCRIPT_PIDS. Sending SIGTERM signal to each." | tee -a "$LOG_FILE"
  for PID in $BACKEND_SCRIPT_PIDS; do
    echo "$TIMESTAMP: Sending SIGTERM to PID $PID..." | tee -a "$LOG_FILE"
    kill -SIGTERM "$PID" | tee -a "$LOG_FILE" 2>&1
    BACKEND_SCRIPT_STOP_STATUS=$?
    if [ "$BACKEND_SCRIPT_STOP_STATUS" -eq 0 ]; then
      echo "$TIMESTAMP: Sent SIGTERM to PID $PID successfully." | tee -a "$LOG_FILE"
    else
      echo "$TIMESTAMP: ERROR: Failed to send SIGTERM to PID $PID, exit code $BACKEND_SCRIPT_STOP_STATUS." | tee -a "$LOG_FILE"
      # 如果发送 SIGTERM 失败，可以尝试发送 SIGKILL (强制终止)
      echo "$TIMESTAMP: Attempting to send SIGKILL to PID $PID..." | tee -a "$LOG_FILE"
      kill -SIGKILL "$PID" | tee -a "$LOG_FILE" 2>&1
      BACKEND_SCRIPT_KILL_STATUS=$?
      if [ "$BACKEND_SCRIPT_KILL_STATUS" -eq 0 ]; then
        echo "$TIMESTAMP: Sent SIGKILL to PID $PID successfully." | tee -a "$LOG_FILE"
      else
        echo "$TIMESTAMP: ERROR: Failed to send SIGKILL to PID $PID, exit code $BACKEND_SCRIPT_KILL_STATUS." | tee -a "$LOG_FILE"
      fi
    fi
  done
  echo "$TIMESTAMP: Sent termination signals to all backend service script processes. Waiting for them to terminate (optional)." | tee -a "$LOG_FILE"
  sleep 5 # 可以根据需要调整等待时间
else
  echo "$TIMESTAMP: INFO: No backend service script process found." | tee -a "$LOG_FILE"
fi

# 停止后端 Docker Compose 服务
echo "$TIMESTAMP: Stopping backend Docker Compose services..." | tee -a "$LOG_FILE"
docker-compose -f /root/ragflow/docker/docker-compose-base.yml down | tee -a "$LOG_FILE" 2>&1
DOCKER_DOWN_STATUS=$?
if [ "$DOCKER_DOWN_STATUS" -eq 0 ]; then
  echo "$TIMESTAMP: Backend Docker Compose services stopped successfully." | tee -a "$LOG_FILE"
else
  echo "$TIMESTAMP: ERROR: Failed to stop backend Docker Compose services with exit code $DOCKER_DOWN_STATUS." | tee -a "$LOG_FILE"
fi

echo "$TIMESTAMP: RAGflow services stopping process completed." | tee -a "$LOG_FILE"
echo "-----------------------------------------------------------------" | tee -a "$LOG_FILE"

exit 0