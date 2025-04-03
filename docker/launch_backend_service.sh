#!/bin/bash

# =============================================
# RAGFlow 后端服务启动脚本
# =============================================
# 功能说明：
# 1. 启动 RAGFlow 系统的任务执行器和主服务器
# 2. 支持多工作进程并行处理
# 3. 实现自动重试和优雅关闭机制
# 4. 使用 jemalloc 进行内存管理优化
#
# 启动流程：
# 1. 加载环境变量配置
# 2. 设置系统环境（代理、Python路径等）
# 3. 配置工作进程数量
# 4. 启动任务执行器（多个）
# 5. 启动主服务器
# 6. 等待所有进程完成
#
# 错误处理：
# - 自动重试机制（最多5次）
# - 优雅关闭处理
# - 进程监控和清理
# =============================================

# 如果任何命令返回非零状态，立即退出脚本
set -e

# 加载环境变量函数
# 从脚本所在目录的 .env 文件中加载环境变量配置
load_env_file() {
    # 获取当前脚本所在目录
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local env_file="$script_dir/.env"

    # 检查 .env 文件是否存在
    if [ -f "$env_file" ]; then
        echo "Loading environment variables from: $env_file"
        # 设置自动导出所有变量
        set -a
        source "$env_file" 
        set +a
    else
        echo "Warning: .env file not found at: $env_file"
    fi
}

# 加载环境变量
load_env_file

# 清除所有代理设置，避免 Docker 代理影响
export http_proxy=""; export https_proxy=""; export no_proxy=""; export HTTP_PROXY=""; export HTTPS_PROXY=""; export NO_PROXY=""
# 设置 Python 路径为当前目录
export PYTHONPATH=$(pwd)

# 设置系统库路径
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/
# 获取 jemalloc 内存分配器路径
JEMALLOC_PATH=$(pkg-config --variable=libdir jemalloc)/libjemalloc.so

# 设置 Python 解释器
PY=python3

# 设置工作进程数量，默认为1
if [[ -z "$WS" || $WS -lt 1 ]]; then
  WS=1
fi

# 设置最大重试次数
MAX_RETRIES=5

# 终止标志
STOP=false

# 存储子进程 PID 的数组
PIDS=()

# 清理函数：处理终止信号，优雅关闭所有进程
cleanup() {
  echo "Termination signal received. Shutting down..."
  STOP=true
  # 终止所有子进程
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      echo "Killing process $pid"
      kill "$pid"
    fi
  done
  exit 0
}

# 捕获终止信号
trap cleanup SIGINT SIGTERM

# 任务执行器函数
# 参数：task_id - 任务ID
# 功能：启动任务执行器，包含重试机制
task_exe(){
    local task_id=$1
    local retry_count=0
    while ! $STOP && [ $retry_count -lt $MAX_RETRIES ]; do
        echo "Starting task_executor.py for task $task_id (Attempt $((retry_count+1)))"
        # 使用 jemalloc 内存分配器启动任务执行器
        LD_PRELOAD=$JEMALLOC_PATH $PY rag/svr/task_executor.py "$task_id"
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo "task_executor.py for task $task_id exited successfully."
            break
        else
            echo "task_executor.py for task $task_id failed with exit code $EXIT_CODE. Retrying..." >&2
            retry_count=$((retry_count + 1))
            sleep 2
        fi
    done

    if [ $retry_count -ge $MAX_RETRIES ]; then
        echo "task_executor.py for task $task_id failed after $MAX_RETRIES attempts. Exiting..." >&2
        cleanup
    fi
}

# 服务器启动函数
# 功能：启动主服务器，包含重试机制
run_server(){
    local retry_count=0
    while ! $STOP && [ $retry_count -lt $MAX_RETRIES ]; do
        echo "Starting ragflow_server.py (Attempt $((retry_count+1)))"
        $PY api/ragflow_server.py
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo "ragflow_server.py exited successfully."
            break
        else
            echo "ragflow_server.py failed with exit code $EXIT_CODE. Retrying..." >&2
            retry_count=$((retry_count + 1))
            sleep 2
        fi
    done

    if [ $retry_count -ge $MAX_RETRIES ]; then
        echo "ragflow_server.py failed after $MAX_RETRIES attempts. Exiting..." >&2
        cleanup
    fi
}

# 启动所有任务执行器
for ((i=0;i<WS;i++))
do
  task_exe "$i" &
  PIDS+=($!)
done

# 启动主服务器
run_server &
PIDS+=($!)

# 等待所有后台进程完成
wait
