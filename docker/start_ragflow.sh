#!/bin/bash

LOG_FILE="/var/log/ragflow_startup.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "-----------------------------------------------------------------" | tee -a "$LOG_FILE"
echo "$TIMESTAMP: Starting RAGflow services..." | tee -a "$LOG_FILE"

# 启动后端服务
echo "$TIMESTAMP: Starting backend service..." | tee -a "$LOG_FILE"
docker-compose -f /root/ragflow/docker/docker-compose-base.yml up -d --force-recreate | tee -a "$LOG_FILE"
BACKEND_UP_STATUS=$?
if [ "$BACKEND_UP_STATUS" -ne 0 ]; then
  echo "$TIMESTAMP: ERROR: Failed to start backend service with docker-compose up, exit code $BACKEND_UP_STATUS." | tee -a "$LOG_FILE"
  exit 1
fi

echo "$TIMESTAMP: Checking backend service status..." | tee -a "$LOG_FILE"
# 使用更可靠的方式检查服务状态
BACKEND_CONTAINERS_SUCCESS=true
SERVICES=$(docker-compose -f /root/ragflow/docker/docker-compose-base.yml ps -q)

if [ -n "$SERVICES" ]; then
    while read -r container_id; do
        if [ -n "$container_id" ]; then
            container_state=$(docker inspect --format '{{.State.Status}}' "$container_id")
            container_name=$(docker inspect --format '{{.Name}}' "$container_id" | sed 's/^\///')
            echo "$TIMESTAMP: Service '$container_name' status: $container_state" | tee -a "$LOG_FILE"
            
            if [[ "$container_state" != "running" ]]; then
                echo "$TIMESTAMP: ERROR: Service '$container_name' is not in 'running' state." | tee -a "$LOG_FILE"
                BACKEND_CONTAINERS_SUCCESS=false
            fi
        fi
    done <<< "$SERVICES"
else
    echo "$TIMESTAMP: ERROR: No running containers found." | tee -a "$LOG_FILE"
    BACKEND_CONTAINERS_SUCCESS=false
fi

if "$BACKEND_CONTAINERS_SUCCESS"; then
  echo "$TIMESTAMP: Backend containers started successfully. Launching backend service script..." | tee -a "$LOG_FILE"
  BACKEND_OUTPUT=$(bash /root/ragflow/docker/launch_backend_service.sh 2>&1)
  LAUNCH_BACKEND_STATUS=$?
  echo "$TIMESTAMP: Backend service script output:" | tee -a "$LOG_FILE"
  echo "$BACKEND_OUTPUT" | tee -a "$LOG_FILE"

  if [[ "$BACKEND_OUTPUT" == *'RAGFlow HTTP server start...'* ]]; then
    echo "$TIMESTAMP: Backend service script executed successfully." | tee -a "$LOG_FILE"
  else
    echo "$TIMESTAMP: ERROR: Backend service script did not start the HTTP server as expected." | tee -a "$LOG_FILE"
    LAUNCH_BACKEND_STATUS=1 # 设置为非0表示启动失败
  fi

  if [ "$LAUNCH_BACKEND_STATUS" -ne 0 ]; then
    echo "$TIMESTAMP: ERROR: Backend service script failed with exit code $LAUNCH_BACKEND_STATUS or did not start correctly." | tee -a "$LOG_FILE"
    exit 1
  fi
else
  echo "$TIMESTAMP: ERROR: Backend containers did not start correctly. Skipping backend service script." | tee -a "$LOG_FILE"
  exit 1
fi

# 启动前端服务
echo "$TIMESTAMP: Starting frontend service..." | tee -a "$LOG_FILE"
cd /root/ragflow/web
FRONTEND_CD_STATUS=$?
if [ "$FRONTEND_CD_STATUS" -eq 0 ]; then
  echo "$TIMESTAMP: Changed directory to /root/ragflow/web successfully." | tee -a "$LOG_FILE"
  FRONTEND_OUTPUT=$(npm run dev 2>&1)
  NPM_STATUS=$?
  echo "$TIMESTAMP: Frontend service (npm run dev) output:" | tee -a "$LOG_FILE"
  echo "$FRONTEND_OUTPUT" | tee -a "$LOG_FILE"

  if [[ "$FRONTEND_OUTPUT" == *'App listening at:'* ]]; then
    echo "$TIMESTAMP: Frontend service started successfully." | tee -a "$LOG_FILE"
  else
    echo "$TIMESTAMP: ERROR: Frontend service did not start as expected (no 'App listening at:' message)." | tee -a "$LOG_FILE"
    NPM_STATUS=1 # 设置为非0表示启动失败
  fi

  if [ "$NPM_STATUS" -ne 0 ]; then
    echo "$TIMESTAMP: ERROR: Failed to start frontend service (npm run dev) with exit code $NPM_STATUS or did not start correctly." | tee -a "$LOG_FILE"
    exit 1
  fi
else
  echo "$TIMESTAMP: ERROR: Failed to change directory to /root/ragflow/web with exit code $FRONTEND_CD_STATUS." | tee -a "$LOG_FILE"
  exit 1 # 如果切换目录失败，可以选择退出脚本
fi

echo "$TIMESTAMP: RAGflow services startup process completed successfully." | tee -a "$LOG_FILE"
echo "-----------------------------------------------------------------" | tee -a "$LOG_FILE"

exit 0