#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# from beartype import BeartypeConf
# from beartype.claw import beartype_all  # <-- you didn't sign up for this
# beartype_all(conf=BeartypeConf(violation_type=UserWarning))    # <-- emit warnings from all code

from api.utils.log_utils import initRootLogger
initRootLogger("ragflow_server")

import logging
import os
import signal
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
import threading
import uuid

from werkzeug.serving import run_simple
from api import settings
from api.apps import app
from api.db.runtime_config import RuntimeConfig
from api.db.services.document_service import DocumentService
from api import utils

from api.db.db_models import init_database_tables as init_web_db
from api.db.init_data import init_web_data
from api.versions import get_ragflow_version
from api.utils import show_configs
from rag.settings import print_rag_settings
from rag.utils.redis_conn import RedisDistributedLock
# Web 服务器应用程序，主要特点包括：
# 使用 Werkzeug 作为 Web 服务器
# 采用多线程处理模式
# 集成了数据库系统
# 包含分布式锁机制（基于 Redis）
# 支持调试模式
stop_event = threading.Event()

# 是否启用远程调试，通过环境变量控制，默认不启用
RAGFLOW_DEBUGPY_LISTEN = int(os.environ.get('RAGFLOW_DEBUGPY_LISTEN', "0"))

def update_progress():
    """
    定期更新文档处理进度的后台任务
    
    工作流程:
    1. 创建分布式锁，确保在分布式环境中只有一个实例执行更新
    2. 循环执行直到收到停止信号
    3. 每次循环尝试获取锁，成功后更新进度并释放锁
    4. 每6秒执行一次，避免频繁更新造成性能问题
    5. 捕获并记录所有异常，确保线程不会意外终止
    """
    # 创建唯一的锁值，用于分布式锁识别
    lock_value = str(uuid.uuid4())
    # 创建Redis分布式锁，超时时间60秒，防止死锁
    redis_lock = RedisDistributedLock("update_progress", lock_value=lock_value, timeout=60)
    logging.info(f"update_progress lock_value: {lock_value}")
    
    # 持续运行直到收到停止信号
    while not stop_event.is_set():
        try:
            # 尝试获取锁，确保在分布式环境中只有一个实例执行更新
            if redis_lock.acquire():
                # 调用文档服务更新进度
                DocumentService.update_progress()
                # 完成后释放锁，让其他实例有机会执行
                redis_lock.release()
            # 等待6秒后再次执行，同时响应停止信号
            stop_event.wait(6)
        except Exception:
            # 记录异常但不终止线程，确保服务持续运行
            logging.exception("update_progress exception")

def signal_handler(sig, frame):
    """
    处理系统信号的函数，用于优雅关闭服务
    
    当收到SIGINT或SIGTERM信号时:
    1. 设置停止事件，通知所有后台线程停止运行
    2. 等待1秒，给线程时间完成当前工作
    3. 退出程序
    """
    logging.info("Received interrupt signal, shutting down...")
    # 设置停止事件，通知所有使用此事件的线程
    stop_event.set()
    # 等待1秒，给线程时间完成当前工作
    time.sleep(1)
    # 正常退出程序
    sys.exit(0)

if __name__ == '__main__':
    # 打印RAGFlow ASCII艺术标志
    logging.info(r"""
        ____   ___    ______ ______ __               
       / __ \ /   |  / ____// ____// /____  _      __
      / /_/ // /| | / / __ / /_   / // __ \| | /| / /
     / _, _// ___ |/ /_/ // __/  / // /_/ /| |/ |/ / 
    /_/ |_|/_/  |_|\____//_/    /_/ \____/ |__/|__/                             

    """)
    # 记录系统版本信息
    logging.info(
        f'RAGFlow version: {get_ragflow_version()}'
    )
    # 记录项目基础目录
    logging.info(
        f'project base: {utils.file_utils.get_project_base_directory()}'
    )
    # 显示配置信息
    show_configs()
    # 初始化系统设置
    settings.init_settings()
    # 打印RAG设置
    print_rag_settings()

    # 如果启用了远程调试，设置debugpy监听
    if RAGFLOW_DEBUGPY_LISTEN > 0:
        logging.info(f"debugpy listen on {RAGFLOW_DEBUGPY_LISTEN}")
        import debugpy
        # 设置debugpy在所有网络接口上监听指定端口
        debugpy.listen(("0.0.0.0", RAGFLOW_DEBUGPY_LISTEN))

    # 初始化数据库表结构
    init_web_db()
    # 初始化数据库基础数据
    init_web_data()
    
    # 解析命令行参数
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", default=False, help="RAGFlow version", action="store_true"
    )
    parser.add_argument(
        "--debug", default=False, help="debug mode", action="store_true"
    )
    args = parser.parse_args()
    # 如果指定了--version参数，打印版本号并退出
    if args.version:
        print(get_ragflow_version())
        sys.exit(0)

    # 设置调试模式
    RuntimeConfig.DEBUG = args.debug
    if RuntimeConfig.DEBUG:
        logging.info("run on debug mode")

    # 初始化运行时环境和配置
    RuntimeConfig.init_env()
    RuntimeConfig.init_config(JOB_SERVER_HOST=settings.HOST_IP, HTTP_PORT=settings.HOST_PORT)

    # 注册信号处理函数，用于优雅关闭
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建线程池并启动进度更新线程
    thread = ThreadPoolExecutor(max_workers=1)
    thread.submit(update_progress)

    # 启动HTTP服务器
    try:
        logging.info("RAGFlow HTTP server start...")
        # 使用Werkzeug的run_simple启动HTTP服务
        run_simple(
            hostname=settings.HOST_IP,
            port=settings.HOST_PORT,
            application=app,
            threaded=True,  # 启用多线程模式处理请求
            use_reloader=RuntimeConfig.DEBUG,  # 在调试模式下启用代码热重载
            use_debugger=RuntimeConfig.DEBUG,  # 在调试模式下启用调试器
        )
    except Exception:
        # 发生异常时打印堆栈跟踪
        traceback.print_exc()
        # 设置停止事件，通知所有线程停止
        stop_event.set()
        # 等待1秒，给线程时间完成当前工作
        time.sleep(1)
        # 强制终止进程
        os.kill(os.getpid(), signal.SIGKILL)
