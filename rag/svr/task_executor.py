"""
RAG系统的任务执行器模块

该模块是RAG(检索增强生成)系统的核心组件之一，主要负责:
1. 文档处理：将输入文档切分成合适大小的文本块(chunks)
2. 向量化：使用嵌入模型将文本块转换为向量
3. 索引：将向量化后的文本块存储到向量数据库中
4. 支持多种处理模式：
   - 标准分块模式：普通文档分块和向量化
   - RAPTOR模式：使用递归抽象处理进行文档组织
   - GraphRAG模式：使用图结构组织文档知识
5. 任务管理：支持任务取消、进度跟踪、错误处理等

系统架构:
1. 基础架构
   - Redis任务队列: 存储和分发待处理任务
   - 异步执行引擎: 使用trio库实现高效的异步处理
   - 文档存储: 支持Elasticsearch/Infinity作为向量数据库
   - 监控系统: 通过Redis实现实时状态报告

2. 核心配置
   - MAX_CONCURRENT_TASKS: 最大并发任务数(默认5)
   - MAX_CONCURRENT_CHUNK_BUILDERS: 最大并发分块处理数(默认1)
   - BATCH_SIZE: 批处理大小(默认64)
   - DOC_MAXIMUM_SIZE: 文档最大大小限制

3. 性能优化
   - 并发控制: 使用CapacityLimiter控制任务并发
   - 批量处理: 文档、向量化和存储都采用批处理
   - 内存管理: 支持内存使用跟踪和监控

4. 错误处理
   - 完整的异常捕获和处理机制
   - 详细的错误日志记录
   - 任务状态实时更新

使用建议:
1. 配置调优
   - 根据服务器资源调整并发数
   - 根据文档大小调整批处理参数
   - 监控系统资源使用情况

2. 开发建议
   - 遵循代码中的错误处理模式
   - 保持日志记录的完整性
   - 注意并发控制和资源管理

3. 调试技巧
   - 使用TRACE_MALLOC_ENABLED跟踪内存
   - 通过Redis监控任务状态
   - 观察日志中的性能指标
"""

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

# from beartype import BeartypeConf
# from beartype.claw import beartype_all  # <-- you didn't sign up for this
# beartype_all(conf=BeartypeConf(violation_type=UserWarning))    # <-- emit warnings from all code
import random
import sys

from api.utils.log_utils import initRootLogger, get_project_base_directory
from graphrag.general.index import run_graphrag
from graphrag.utils import get_llm_cache, set_llm_cache, get_tags_from_cache, set_tags_to_cache
from rag.prompts import keyword_extraction, question_proposal, content_tagging

import logging
import os
from datetime import datetime
import json
import xxhash
import copy
import re
from functools import partial
from io import BytesIO
from multiprocessing.context import TimeoutError
from timeit import default_timer as timer
import tracemalloc
import signal
import trio
import exceptiongroup
import faulthandler

import numpy as np
from peewee import DoesNotExist

from api.db import LLMType, ParserType, TaskStatus
from api.db.services.document_service import DocumentService
from api.db.services.llm_service import LLMBundle
from api.db.services.task_service import TaskService
from api.db.services.file2document_service import File2DocumentService
from api import settings
from api.versions import get_ragflow_version
from api.db.db_models import close_connection
from rag.app import laws, paper, presentation, manual, qa, table, book, resume, picture, naive, one, audio, \
    email, tag
from rag.nlp import search, rag_tokenizer
from rag.raptor import RecursiveAbstractiveProcessing4TreeOrganizedRetrieval as Raptor
from rag.settings import DOC_MAXIMUM_SIZE, SVR_CONSUMER_GROUP_NAME, get_svr_queue_name, get_svr_queue_names, print_rag_settings, TAG_FLD, PAGERANK_FLD
from rag.utils import num_tokens_from_string, truncate
from rag.utils.redis_conn import REDIS_CONN
from rag.utils.storage_factory import STORAGE_IMPL
from graphrag.utils import chat_limiter

BATCH_SIZE = 64

FACTORY = {
    "general": naive,
    ParserType.NAIVE.value: naive,
    ParserType.PAPER.value: paper,
    ParserType.BOOK.value: book,
    ParserType.PRESENTATION.value: presentation,
    ParserType.MANUAL.value: manual,
    ParserType.LAWS.value: laws,
    ParserType.QA.value: qa,
    ParserType.TABLE.value: table,
    ParserType.RESUME.value: resume,
    ParserType.PICTURE.value: picture,
    ParserType.ONE.value: one,
    ParserType.AUDIO.value: audio,
    ParserType.EMAIL.value: email,
    ParserType.KG.value: naive,
    ParserType.TAG.value: tag
}

UNACKED_ITERATOR = None

CONSUMER_NO = "0" if len(sys.argv) < 2 else sys.argv[1]
CONSUMER_NAME = "task_executor_" + CONSUMER_NO
BOOT_AT = datetime.now().astimezone().isoformat(timespec="milliseconds")
PENDING_TASKS = 0
LAG_TASKS = 0
DONE_TASKS = 0
FAILED_TASKS = 0

CURRENT_TASKS = {}

MAX_CONCURRENT_TASKS = int(os.environ.get('MAX_CONCURRENT_TASKS', "5"))
MAX_CONCURRENT_CHUNK_BUILDERS = int(os.environ.get('MAX_CONCURRENT_CHUNK_BUILDERS', "1"))
task_limiter = trio.CapacityLimiter(MAX_CONCURRENT_TASKS)
chunk_limiter = trio.CapacityLimiter(MAX_CONCURRENT_CHUNK_BUILDERS)


# SIGUSR1 handler: start tracemalloc and take snapshot
def start_tracemalloc_and_snapshot(signum, frame):
    if not tracemalloc.is_tracing():
        logging.info("start tracemalloc")
        tracemalloc.start()
    else:
        logging.info("tracemalloc is already running")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_file = f"snapshot_{timestamp}.trace"
    snapshot_file = os.path.abspath(os.path.join(get_project_base_directory(), "logs", f"{os.getpid()}_snapshot_{timestamp}.trace"))

    snapshot = tracemalloc.take_snapshot()
    snapshot.dump(snapshot_file)
    current, peak = tracemalloc.get_traced_memory()
    if sys.platform == "win32":
        import  psutil
        process = psutil.Process()
        max_rss = process.memory_info().rss / 1024
    else:
        import resource
        max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    logging.info(f"taken snapshot {snapshot_file}. max RSS={max_rss / 1000:.2f} MB, current memory usage: {current / 10**6:.2f} MB, Peak memory usage: {peak / 10**6:.2f} MB")

# SIGUSR2 handler: stop tracemalloc
def stop_tracemalloc(signum, frame):
    if tracemalloc.is_tracing():
        logging.info("stop tracemalloc")
        tracemalloc.stop()
    else:
        logging.info("tracemalloc not running")

class TaskCanceledException(Exception):
    """任务取消异常类"""
    def __init__(self, msg):
        self.msg = msg


def set_progress(task_id, from_page=0, to_page=-1, prog=None, msg="Processing..."):
    """
    更新任务进度和状态
    
    参数:
        task_id: 任务ID
        from_page: 起始页码
        to_page: 结束页码
        prog: 进度值(0-1), 负值表示错误
        msg: 状态消息
    
    功能:
        1. 错误状态处理
        2. 任务取消检查
        3. 进度信息格式化
        4. 数据库更新
        5. 异常处理
    """
    try:
        # 处理错误状态
        if prog is not None and prog < 0:
            msg = "[ERROR]" + msg
            
        # 检查任务是否被取消
        cancel = TaskService.do_cancel(task_id)
        if cancel:
            msg += " [Canceled]"
            prog = -1

        # 格式化页码信息
        if to_page > 0 and msg and from_page < to_page:
            msg = f"Page({from_page + 1}~{to_page + 1}): " + msg
            
        # 添加时间戳
        if msg:
            msg = datetime.now().strftime("%H:%M:%S") + " " + msg
            
        # 准备更新数据
        d = {"progress_msg": msg}
        if prog is not None:
            d["progress"] = prog

        # 更新数据库
        TaskService.update_progress(task_id, d)
        close_connection()
        
        # 处理取消情况
        if cancel:
            raise TaskCanceledException(msg)
            
        # 记录日志
        logging.info(f"set_progress({task_id}), progress: {prog}, progress_msg: {msg}")
        
    except DoesNotExist:
        logging.warning(f"set_progress({task_id}) got exception DoesNotExist")
    except Exception:
        logging.exception(f"set_progress({task_id}), progress: {prog}, progress_msg: {msg}, got exception")

async def collect():
    """
    从Redis队列中获取待处理任务
    
    工作流程:
    1. 检查未确认任务
       - 通过UNACKED_ITERATOR获取之前未完成的任务
    2. 获取新任务
       - 如果没有未完成任务，从Redis队列获取新任务
    3. 任务验证
       - 检查任务是否存在
       - 检查任务是否已取消
       - 验证文档状态
    
    返回:
        tuple: (redis_msg, task) - 包含两个元素的元组，第一个元素是Redis消息对象，第二个元素是任务信息字典。
               如果没有获取到任务，则返回 (None, None)
    """
    global CONSUMER_NAME, DONE_TASKS, FAILED_TASKS
    global UNACKED_ITERATOR
    svr_queue_names = get_svr_queue_names()
    try:
        # 第一步：获取任务消息
        # 首先检查是否有未确认的消息需要处理
        if not UNACKED_ITERATOR:
            # 如果迭代器不存在，初始化一个新的未确认消息迭代器
            # 这个迭代器会返回之前获取但未确认处理完成的消息
            UNACKED_ITERATOR = REDIS_CONN.get_unacked_iterator(svr_queue_names, SVR_CONSUMER_GROUP_NAME, CONSUMER_NAME)
        try:
            # 尝试从未确认消息迭代器中获取下一个消息
            redis_msg = next(UNACKED_ITERATOR)
        except StopIteration:
            # 如果没有未确认的消息，则从各个队列中获取新消息
            # 按优先级顺序遍历所有队列名称
            redis_msg = None
            for svr_queue_name in svr_queue_names:
                # 从当前队列获取一个新消息
                redis_msg = REDIS_CONN.queue_consumer(svr_queue_name, SVR_CONSUMER_GROUP_NAME, CONSUMER_NAME)
                if redis_msg:
                    # 一旦获取到消息就跳出循环
                    break
    except Exception:
        # 捕获并记录任何异常，确保任务收集过程不会中断整个系统
        logging.exception("collect got exception")
        return None, None

    # 第二步：验证消息有效性
    # 如果没有获取到消息，返回空结果
    if not redis_msg:
        return None, None
    
    # 从Redis消息对象中提取实际的消息内容
    msg = redis_msg.get_message()
    if not msg:
        # 如果消息内容为空，记录错误并确认该消息（从队列中移除）
        logging.error(f"collect got empty message of {redis_msg.get_msg_id()}")
        redis_msg.ack()
        return None, None

    # 第三步：验证任务状态
    canceled = False
    # 根据消息中的任务ID从数据库获取完整的任务信息
    task = TaskService.get_task(msg["id"])
    if task:
        # 如果任务存在，检查关联文档的状态
        _, doc = DocumentService.get_by_id(task["doc_id"])
        # 判断任务是否已被取消：文档状态为取消或进度为负值
        canceled = doc.run == TaskStatus.CANCEL.value or doc.progress < 0
    
    # 如果任务不存在或已被取消，则不处理该任务
    if not task or canceled:
        # 确定任务状态描述
        state = "is unknown" if not task else "has been cancelled"
        # 增加失败任务计数
        FAILED_TASKS += 1
        # 记录警告日志
        logging.warning(f"collect task {msg['id']} {state}")
        # 确认消息已处理（从队列中移除）
        redis_msg.ack()
        return None, None
    
    # 第四步：准备返回有效任务
    # 添加任务类型信息到任务对象
    task["task_type"] = msg.get("task_type", "")
    # 返回Redis消息对象和任务信息
    return redis_msg, task


async def get_storage_binary(bucket, name):
    return await trio.to_thread.run_sync(lambda: STORAGE_IMPL.get(bucket, name))


async def build_chunks(task, progress_callback):
    """
    将文档切分成文本块
    
    工作流程:
    1. 文件大小检查
       - 确保不超过最大限制
    2. 获取解析器
       - 根据文档类型选择对应的解析器
    3. 获取文件内容
       - 从存储系统(minio)获取文件
    4. 文档分块
       - 使用选定的解析器进行分块
       - 支持分页处理
    5. 块处理
       - 生成唯一ID
       - 添加元数据
       - 处理图片(如果有)
    
    参数:
        task: 任务信息，包含文档路径、解析器配置等
        progress_callback: 进度回调函数
    
    返回:
        list: 文本块列表，每个文本块包含内容、ID等信息
    """
    if task["size"] > DOC_MAXIMUM_SIZE:
        set_progress(task["id"], prog=-1, msg="File size exceeds( <= %dMb )" %
                                              (int(DOC_MAXIMUM_SIZE / 1024 / 1024)))
        return []

    chunker = FACTORY[task["parser_id"].lower()]
    try:
        st = timer()
        bucket, name = File2DocumentService.get_storage_address(doc_id=task["doc_id"])
        binary = await get_storage_binary(bucket, name)
        logging.info("From minio({}) {}/{}".format(timer() - st, task["location"], task["name"]))
    except TimeoutError:
        progress_callback(-1, "Internal server error: Fetch file from minio timeout. Could you try it again.")
        logging.exception(
            "Minio {}/{} got timeout: Fetch file from minio timeout.".format(task["location"], task["name"]))
        raise
    except Exception as e:
        if re.search("(No such file|not found)", str(e)):
            progress_callback(-1, "Can not find file <%s> from minio. Could you try it again?" % task["name"])
        else:
            progress_callback(-1, "Get file from minio: %s" % str(e).replace("'", ""))
        logging.exception("Chunking {}/{} got exception".format(task["location"], task["name"]))
        raise

    try:
        async with chunk_limiter:
            cks = await trio.to_thread.run_sync(lambda: chunker.chunk(task["name"], binary=binary, from_page=task["from_page"],
                                to_page=task["to_page"], lang=task["language"], callback=progress_callback,
                                kb_id=task["kb_id"], parser_config=task["parser_config"], tenant_id=task["tenant_id"]))
        logging.info("Chunking({}) {}/{} done".format(timer() - st, task["location"], task["name"]))
    except TaskCanceledException:
        raise
    except Exception as e:
        progress_callback(-1, "Internal server error while chunking: %s" % str(e).replace("'", ""))
        logging.exception("Chunking {}/{} got exception".format(task["location"], task["name"]))
        raise

    docs = []
    doc = {
        "doc_id": task["doc_id"],
        "kb_id": str(task["kb_id"])
    }
    if task["pagerank"]:
        doc[PAGERANK_FLD] = int(task["pagerank"])
    el = 0
    for ck in cks:
        d = copy.deepcopy(doc)
        d.update(ck)
        d["id"] = xxhash.xxh64((ck["content_with_weight"] + str(d["doc_id"])).encode("utf-8")).hexdigest()
        d["create_time"] = str(datetime.now()).replace("T", " ")[:19]
        d["create_timestamp_flt"] = datetime.now().timestamp()
        if not d.get("image"):
            _ = d.pop("image", None)
            d["img_id"] = ""
            docs.append(d)
            continue

        try:
            output_buffer = BytesIO()
            if isinstance(d["image"], bytes):
                output_buffer = BytesIO(d["image"])
            else:
                d["image"].save(output_buffer, format='JPEG')

            st = timer()
            await trio.to_thread.run_sync(lambda: STORAGE_IMPL.put(task["kb_id"], d["id"], output_buffer.getvalue()))
            el += timer() - st
        except Exception:
            logging.exception(
                "Saving image of chunk {}/{}/{} got exception".format(task["location"], task["name"], d["id"]))
            raise

        d["img_id"] = "{}-{}".format(task["kb_id"], d["id"])
        del d["image"]
        docs.append(d)
    logging.info("MINIO PUT({}):{}".format(task["name"], el))

    if task["parser_config"].get("auto_keywords", 0):
        st = timer()
        progress_callback(msg="Start to generate keywords for every chunk ...")
        chat_mdl = LLMBundle(task["tenant_id"], LLMType.CHAT, llm_name=task["llm_id"], lang=task["language"])

        async def doc_keyword_extraction(chat_mdl, d, topn):
            cached = get_llm_cache(chat_mdl.llm_name, d["content_with_weight"], "keywords", {"topn": topn})
            if not cached:
                async with chat_limiter:
                    cached = await trio.to_thread.run_sync(lambda: keyword_extraction(chat_mdl, d["content_with_weight"], topn))
                set_llm_cache(chat_mdl.llm_name, d["content_with_weight"], cached, "keywords", {"topn": topn})
            if cached:
                d["important_kwd"] = cached.split(",")
                d["important_tks"] = rag_tokenizer.tokenize(" ".join(d["important_kwd"]))
            return
        async with trio.open_nursery() as nursery:
            for d in docs:
                nursery.start_soon(lambda: doc_keyword_extraction(chat_mdl, d, task["parser_config"]["auto_keywords"]))
        progress_callback(msg="Keywords generation {} chunks completed in {:.2f}s".format(len(docs), timer() - st))

    if task["parser_config"].get("auto_questions", 0):
        st = timer()
        progress_callback(msg="Start to generate questions for every chunk ...")
        chat_mdl = LLMBundle(task["tenant_id"], LLMType.CHAT, llm_name=task["llm_id"], lang=task["language"])

        async def doc_question_proposal(chat_mdl, d, topn):
            cached = get_llm_cache(chat_mdl.llm_name, d["content_with_weight"], "question", {"topn": topn})
            if not cached:
                async with chat_limiter:
                    cached = await trio.to_thread.run_sync(lambda: question_proposal(chat_mdl, d["content_with_weight"], topn))
                set_llm_cache(chat_mdl.llm_name, d["content_with_weight"], cached, "question", {"topn": topn})
            if cached:
                d["question_kwd"] = cached.split("\n")
                d["question_tks"] = rag_tokenizer.tokenize("\n".join(d["question_kwd"]))
        async with trio.open_nursery() as nursery:
            for d in docs:
                nursery.start_soon(lambda: doc_question_proposal(chat_mdl, d, task["parser_config"]["auto_questions"]))
        progress_callback(msg="Question generation {} chunks completed in {:.2f}s".format(len(docs), timer() - st))

    if task["kb_parser_config"].get("tag_kb_ids", []):
        progress_callback(msg="Start to tag for every chunk ...")
        kb_ids = task["kb_parser_config"]["tag_kb_ids"]
        tenant_id = task["tenant_id"]
        topn_tags = task["kb_parser_config"].get("topn_tags", 3)
        S = 1000
        st = timer()
        examples = []
        all_tags = get_tags_from_cache(kb_ids)
        if not all_tags:
            all_tags = settings.retrievaler.all_tags_in_portion(tenant_id, kb_ids, S)
            set_tags_to_cache(kb_ids, all_tags)
        else:
            all_tags = json.loads(all_tags)

        chat_mdl = LLMBundle(task["tenant_id"], LLMType.CHAT, llm_name=task["llm_id"], lang=task["language"])

        docs_to_tag = []
        for d in docs:
            if settings.retrievaler.tag_content(tenant_id, kb_ids, d, all_tags, topn_tags=topn_tags, S=S):
                examples.append({"content": d["content_with_weight"], TAG_FLD: d[TAG_FLD]})
            else:
                docs_to_tag.append(d)

        async def doc_content_tagging(chat_mdl, d, topn_tags):
            cached = get_llm_cache(chat_mdl.llm_name, d["content_with_weight"], all_tags, {"topn": topn_tags})
            if not cached:
                picked_examples = random.choices(examples, k=2) if len(examples)>2 else examples
                if not picked_examples:
                    picked_examples.append({"content": "This is an example", TAG_FLD: {'example': 1}})
                async with chat_limiter:
                    cached = await trio.to_thread.run_sync(lambda: content_tagging(chat_mdl, d["content_with_weight"], all_tags, picked_examples, topn=topn_tags))
                if cached:
                    cached = json.dumps(cached)
            if cached:
                set_llm_cache(chat_mdl.llm_name, d["content_with_weight"], cached, all_tags, {"topn": topn_tags})
                d[TAG_FLD] = json.loads(cached)
        async with trio.open_nursery() as nursery:
            for d in docs_to_tag:
                nursery.start_soon(lambda: doc_content_tagging(chat_mdl, d, topn_tags))
        progress_callback(msg="Tagging {} chunks completed in {:.2f}s".format(len(docs), timer() - st))

    return docs


def init_kb(row, vector_size: int):
    idxnm = search.index_name(row["tenant_id"])
    return settings.docStoreConn.createIdx(idxnm, row.get("kb_id", ""), vector_size)


async def embedding(docs, mdl, parser_config=None, callback=None):
    """
    将文本块转换为向量表示
    
    工作流程:
    1. 文本预处理
       - 提取标题
       - 处理内容
       - 清理HTML标签
    2. 批量向量化
       - 标题向量化
       - 内容分批向量化(batch_size=16)
    3. 向量合并
       - 标题向量权重(默认0.1)
       - 内容向量权重(默认0.9)
    4. 结果处理
       - 保存向量到文档
       - 计算token数量
    
    参数:
        docs: 文本块列表
        mdl: 嵌入模型
        parser_config: 解析器配置
        callback: 进度回调函数
    
    返回:
        tuple: (token_count, vector_size) - token数量和向量维度
    """
    if parser_config is None:
        parser_config = {}
    batch_size = 16
    tts, cnts = [], []
    for d in docs:
        tts.append(d.get("docnm_kwd", "Title"))
        c = "\n".join(d.get("question_kwd", []))
        if not c:
            c = d["content_with_weight"]
        c = re.sub(r"</?(table|td|caption|tr|th)( [^<>]{0,12})?>", " ", c)
        if not c:
            c = "None"
        cnts.append(c)

    tk_count = 0
    if len(tts) == len(cnts):
        vts, c = await trio.to_thread.run_sync(lambda: mdl.encode(tts[0: 1]))
        tts = np.concatenate([vts for _ in range(len(tts))], axis=0)
        tk_count += c

    cnts_ = np.array([])
    for i in range(0, len(cnts), batch_size):
        vts, c = await trio.to_thread.run_sync(lambda: mdl.encode([truncate(c, mdl.max_length-10) for c in cnts[i: i + batch_size]]))
        if len(cnts_) == 0:
            cnts_ = vts
        else:
            cnts_ = np.concatenate((cnts_, vts), axis=0)
        tk_count += c
        callback(prog=0.7 + 0.2 * (i + 1) / len(cnts), msg="")
    cnts = cnts_

    title_w = float(parser_config.get("filename_embd_weight", 0.1))
    vects = (title_w * tts + (1 - title_w) *
             cnts) if len(tts) == len(cnts) else cnts

    assert len(vects) == len(docs)
    vector_size = 0
    for i, d in enumerate(docs):
        v = vects[i].tolist()
        vector_size = len(v)
        d["q_%d_vec" % len(v)] = v
    return tk_count, vector_size


async def run_raptor(row, chat_mdl, embd_mdl, vector_size, callback=None):
    """
    使用RAPTOR(递归抽象处理)方法处理文档
    
    工作流程:
    1. 准备工作
       - 获取现有chunks
       - 初始化RAPTOR处理器
    2. 递归处理
       - 使用chat模型生成摘要
       - 使用embedding模型生成向量
    3. 结果处理
       - 生成新的chunks
       - 添加元数据
       - 计算token数量
    
    参数:
        row: 任务信息
        chat_mdl: 对话模型
        embd_mdl: 嵌入模型
        vector_size: 向量维度
        callback: 进度回调函数
    
    返回:
        tuple: (chunks, token_count) - 处理后的文本块和token数量
    """
    chunks = []
    vctr_nm = "q_%d_vec"%vector_size
    for d in settings.retrievaler.chunk_list(row["doc_id"], row["tenant_id"], [str(row["kb_id"])],
                                             fields=["content_with_weight", vctr_nm]):
        chunks.append((d["content_with_weight"], np.array(d[vctr_nm])))

    raptor = Raptor(
        row["parser_config"]["raptor"].get("max_cluster", 64),
        chat_mdl,
        embd_mdl,
        row["parser_config"]["raptor"]["prompt"],
        row["parser_config"]["raptor"]["max_token"],
        row["parser_config"]["raptor"]["threshold"]
    )
    original_length = len(chunks)
    chunks = await raptor(chunks, row["parser_config"]["raptor"]["random_seed"], callback)
    doc = {
        "doc_id": row["doc_id"],
        "kb_id": [str(row["kb_id"])],
        "docnm_kwd": row["name"],
        "title_tks": rag_tokenizer.tokenize(row["name"])
    }
    if row["pagerank"]:
        doc[PAGERANK_FLD] = int(row["pagerank"])
    res = []
    tk_count = 0
    for content, vctr in chunks[original_length:]:
        d = copy.deepcopy(doc)
        d["id"] = xxhash.xxh64((content + str(d["doc_id"])).encode("utf-8")).hexdigest()
        d["create_time"] = str(datetime.now()).replace("T", " ")[:19]
        d["create_timestamp_flt"] = datetime.now().timestamp()
        d[vctr_nm] = vctr.tolist()
        d["content_with_weight"] = content
        d["content_ltks"] = rag_tokenizer.tokenize(content)
        d["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(d["content_ltks"])
        res.append(d)
        tk_count += num_tokens_from_string(content)
    return res, tk_count


async def do_handle_task(task):
    """
    处理单个任务的主函数
    
    工作流程:
    1. 任务参数提取
       - 解析任务配置
       - 准备回调函数
    2. 前置检查
       - 验证文档引擎兼容性
       - 检查任务状态
    3. 模型准备
       - 初始化嵌入模型
       - 初始化向量空间
    4. 文档处理
       - 根据任务类型选择处理方式
       - 生成文本块
       - 向量化处理
    5. 数据存储
       - 批量保存到文档数据库
       - 更新任务状态
    6. 完成处理
       - 更新统计信息
       - 记录处理时间
    
    参数:
        task: 任务信息字典
    """
    # 提取任务基本信息
    task_id = task["id"]                         # 任务ID
    task_from_page = task["from_page"]           # 起始页码
    task_to_page = task["to_page"]               # 结束页码
    task_tenant_id = task["tenant_id"]           # 租户ID
    task_embedding_id = task["embd_id"]          # 嵌入模型ID
    task_language = task["language"]             # 文档语言
    task_llm_id = task["llm_id"]                 # 大语言模型ID
    task_dataset_id = task["kb_id"]              # 知识库ID
    task_doc_id = task["doc_id"]                 # 文档ID
    task_document_name = task["name"]            # 文档名称
    task_parser_config = task["parser_config"]   # 解析器配置
    task_start_ts = timer()                      # 记录任务开始时间戳

    # 准备进度回调函数，用于更新任务处理进度
    progress_callback = partial(set_progress, task_id, task_from_page, task_to_page)

    # 兼容性检查：Infinity向量数据库不支持表格解析方法
    lower_case_doc_engine = settings.DOC_ENGINE.lower()
    if lower_case_doc_engine == 'infinity' and task['parser_id'].lower() == 'table':
        error_message = "Table parsing method is not supported by Infinity, please use other parsing methods or use Elasticsearch as the document engine."
        progress_callback(-1, msg=error_message)  # 更新任务状态为错误
        raise Exception(error_message)

    # 检查任务是否已被取消
    task_canceled = TaskService.do_cancel(task_id)
    if task_canceled:
        progress_callback(-1, msg="Task has been canceled.")
        return

    try:
        # 初始化嵌入模型并验证其可用性
        embedding_model = LLMBundle(task_tenant_id, LLMType.EMBEDDING, llm_name=task_embedding_id, lang=task_language)
        vts, _ = embedding_model.encode(["ok"])  # 测试编码功能
        vector_size = len(vts[0])  # 获取向量维度大小
    except Exception as e:
        # 嵌入模型初始化失败处理
        error_message = f'Fail to bind embedding model: {str(e)}'
        progress_callback(-1, msg=error_message)  # 更新任务状态为错误
        logging.exception(error_message)
        raise

    # 初始化知识库，设置向量大小
    init_kb(task, vector_size)

    # 根据任务类型选择不同的处理流程
    if task.get("task_type", "") == "raptor":
        # RAPTOR模式：递归抽象处理进行文档组织
        # 初始化聊天模型用于RAPTOR处理
        chat_model = LLMBundle(task_tenant_id, LLMType.CHAT, llm_name=task_llm_id, lang=task_language)
        # 执行RAPTOR处理流程
        chunks, token_count = await run_raptor(task, chat_model, embedding_model, vector_size, progress_callback)
    elif task.get("task_type", "") == "graphrag":
        # GraphRAG模式：使用图结构组织文档知识
        global task_limiter
        task_limiter = trio.CapacityLimiter(2)  # 限制并发任务数为2
        graphrag_conf = task_parser_config.get("graphrag", {})
        if not graphrag_conf.get("use_graphrag", False):
            return  # 如果未启用GraphRAG，则直接返回
        
        start_ts = timer()  # 记录开始时间
        # 初始化聊天模型用于GraphRAG处理
        chat_model = LLMBundle(task_tenant_id, LLMType.CHAT, llm_name=task_llm_id, lang=task_language)
        # 获取GraphRAG配置参数
        with_resolution = graphrag_conf.get("resolution", False)  # 是否启用解析
        with_community = graphrag_conf.get("community", False)    # 是否启用社区检测
        # 执行GraphRAG处理流程
        await run_graphrag(task, task_language, with_resolution, with_community, chat_model, embedding_model, progress_callback)
        # 更新任务进度为完成
        progress_callback(prog=1.0, msg="Knowledge Graph done ({:.2f}s)".format(timer() - start_ts))
        return
    else:
        # 标准分块模式：普通文档分块和向量化
        start_ts = timer()  # 记录开始时间
        # 构建文本块
        chunks = await build_chunks(task, progress_callback)
        logging.info("Build document {}: {:.2f}s".format(task_document_name, timer() - start_ts))
        
        # 检查分块结果
        if chunks is None:
            return  # 分块失败，直接返回
        if not chunks:
            # 没有生成任何文本块，更新任务状态并返回
            progress_callback(1., msg=f"No chunk built from {task_document_name}")
            return
            
        # 更新进度信息
        progress_callback(msg="Generate {} chunks".format(len(chunks)))
        
        # 开始向量化处理
        start_ts = timer()
        try:
            # 对文本块进行嵌入处理，获取token数量和向量维度
            token_count, vector_size = await embedding(chunks, embedding_model, task_parser_config, progress_callback)
        except Exception as e:
            # 向量化处理失败处理
            error_message = "Generate embedding error:{}".format(str(e))
            progress_callback(-1, error_message)  # 更新任务状态为错误
            logging.exception(error_message)
            token_count = 0
            raise
            
        # 更新嵌入完成的进度信息
        progress_message = "Embedding chunks ({:.2f}s)".format(timer() - start_ts)
        logging.info(progress_message)
        progress_callback(msg=progress_message)

    # 计算唯一文本块数量
    chunk_count = len(set([chunk["id"] for chunk in chunks]))
    
    # 开始将文本块存储到文档数据库
    start_ts = timer()
    doc_store_result = ""
    es_bulk_size = 4  # 批量插入大小
    
    # 分批处理文本块，避免一次性处理过多数据
    for b in range(0, len(chunks), es_bulk_size):
        # 将当前批次的文本块插入到文档数据库
        doc_store_result = await trio.to_thread.run_sync(
            lambda: settings.docStoreConn.insert(
                chunks[b:b + es_bulk_size], 
                search.index_name(task_tenant_id), 
                task_dataset_id
            )
        )
        
        # 定期更新进度信息
        if b % 128 == 0:
            progress_callback(prog=0.8 + 0.1 * (b + 1) / len(chunks), msg="")
            
        # 检查插入结果
        if doc_store_result:
            # 插入失败处理
            error_message = f"Insert chunk error: {doc_store_result}, please check log file and Elasticsearch/Infinity status!"
            progress_callback(-1, msg=error_message)  # 更新任务状态为错误
            raise Exception(error_message)
            
        # 获取已处理的文本块ID
        chunk_ids = [chunk["id"] for chunk in chunks[:b + es_bulk_size]]
        chunk_ids_str = " ".join(chunk_ids)
        
        try:
            # 更新任务的文本块ID信息
            TaskService.update_chunk_ids(task["id"], chunk_ids_str)
        except DoesNotExist:
            # 任务不存在，可能已被删除
            logging.warning(f"do_handle_task update_chunk_ids failed since task {task['id']} is unknown.")
            # 删除已插入的文本块，避免孤立数据
            doc_store_result = await trio.to_thread.run_sync(
                lambda: settings.docStoreConn.delete(
                    {"id": chunk_ids}, 
                    search.index_name(task_tenant_id), 
                    task_dataset_id
                )
            )
            return
            
    # 记录索引完成的日志信息
    logging.info("Indexing doc({}), page({}-{}), chunks({}), elapsed: {:.2f}".format(
        task_document_name, 
        task_from_page,
        task_to_page, 
        len(chunks),
        timer() - start_ts
    ))

    # 更新文档的文本块数量、token数量等统计信息
    DocumentService.increment_chunk_num(task_doc_id, task_dataset_id, token_count, chunk_count, 0)

    # 计算任务总耗时并更新任务状态为完成
    time_cost = timer() - start_ts
    task_time_cost = timer() - task_start_ts
    progress_callback(prog=1.0, msg="Indexing done ({:.2f}s). Task done ({:.2f}s)".format(time_cost, task_time_cost))
    
    # 记录任务完成的详细日志
    logging.info(
        "Chunk doc({}), page({}-{}), chunks({}), token({}), elapsed:{:.2f}".format(
            task_document_name, 
            task_from_page,
            task_to_page, 
            len(chunks),
            token_count, 
            task_time_cost
        )
    )


async def handle_task():
    """
    任务处理的包装函数
    
    工作流程:
    1. 任务获取
       - 从队列获取任务
       - 任务为空时等待
    2. 任务执行
       - 记录开始状态
       - 调用处理函数
    3. 状态更新
       - 更新任务计数
       - 清理任务记录
    4. 异常处理
       - 捕获所有异常
       - 更新错误状态
    5. 完成确认
       - 确认消息处理
    """
    global DONE_TASKS, FAILED_TASKS
    # 从Redis队列中获取任务消息和任务数据
    redis_msg, task = await collect()
    # 如果没有获取到任务，等待5秒后返回
    if not task:
        await trio.sleep(5)
        return
    try:
        # 记录任务开始处理的日志
        logging.info(f"handle_task begin for task {json.dumps(task)}")
        # 将当前任务添加到正在处理的任务字典中，使用深拷贝避免引用问题
        CURRENT_TASKS[task["id"]] = copy.deepcopy(task)
        # 执行实际的任务处理逻辑
        await do_handle_task(task)
        # 任务成功完成，增加完成任务计数
        DONE_TASKS += 1
        # 从当前任务字典中移除已完成的任务
        CURRENT_TASKS.pop(task["id"], None)
        # 记录任务完成的日志
        logging.info(f"handle_task done for task {json.dumps(task)}")
    except Exception as e:
        # 任务执行失败，增加失败任务计数
        FAILED_TASKS += 1
        # 从当前任务字典中移除失败的任务
        CURRENT_TASKS.pop(task["id"], None)
        try:
            # 提取异常信息
            err_msg = str(e)
            # 处理异常组情况，递归提取内部异常信息
            while isinstance(e, exceptiongroup.ExceptionGroup):
                e = e.exceptions[0]
                err_msg += ' -- ' + str(e)
            # 更新任务状态为失败，并设置错误消息
            set_progress(task["id"], prog=-1, msg=f"[Exception]: {err_msg}")
        except Exception:
            # 忽略在错误处理过程中可能发生的异常
            pass
        # 记录详细的异常堆栈信息到日志
        logging.exception(f"handle_task got exception for task {json.dumps(task)}")
    finally:
        # 无论任务成功还是失败，都确认消息已处理，从队列中移除
        redis_msg.ack()


async def report_status():
    """
    定期向Redis报告执行器状态
    
    报告内容:
    1. 基础信息
       - 执行器名称
       - 启动时间
       - 当前时间
    2. 任务统计
       - 待处理任务数
       - 已完成任务数
       - 失败任务数
    3. 性能监控
       - 当前正在处理的任务
       - 任务延迟情况
    
    工作流程:
    1. 获取统计信息
    2. 生成状态报告
    3. 更新到Redis
    4. 清理过期数据
    """
    # 声明全局变量，用于跨函数共享状态信息
    global CONSUMER_NAME, BOOT_AT, PENDING_TASKS, LAG_TASKS, DONE_TASKS, FAILED_TASKS
    # 将当前执行器名称添加到Redis的"TASKEXE"集合中，用于跟踪活跃的执行器
    REDIS_CONN.sadd("TASKEXE", CONSUMER_NAME)
    # 无限循环，持续报告状态
    while True:
        try:
            # 获取当前时间，用于时间戳和过期数据清理
            now = datetime.now()
            # 从Redis获取队列信息，查询优先级为0的队列状态
            group_info = REDIS_CONN.queue_info(get_svr_queue_name(0), SVR_CONSUMER_GROUP_NAME)
            # 如果成功获取到队列信息，更新任务统计数据
            if group_info is not None:
                # 更新待处理任务数量
                PENDING_TASKS = int(group_info.get("pending", 0))
                # 更新任务延迟数量（队列中积压的任务）
                LAG_TASKS = int(group_info.get("lag", 0))

            # 深拷贝当前任务列表，避免在状态报告期间被修改
            current = copy.deepcopy(CURRENT_TASKS)
            # 构建心跳信息JSON对象，包含执行器状态的完整快照
            heartbeat = json.dumps({
                "name": CONSUMER_NAME,          # 执行器名称
                "now": now.astimezone().isoformat(timespec="milliseconds"),  # 当前时间（ISO格式，毫秒精度）
                "boot_at": BOOT_AT,             # 启动时间
                "pending": PENDING_TASKS,       # 待处理任务数
                "lag": LAG_TASKS,               # 延迟任务数
                "done": DONE_TASKS,             # 已完成任务数
                "failed": FAILED_TASKS,         # 失败任务数
                "current": current,             # 当前正在处理的任务详情
            })
            # 将心跳信息添加到Redis的有序集合中，使用时间戳作为分数
            REDIS_CONN.zadd(CONSUMER_NAME, heartbeat, now.timestamp())
            # 记录心跳信息到日志
            logging.info(f"{CONSUMER_NAME} reported heartbeat: {heartbeat}")

            # 计算30分钟前的过期心跳记录数量
            expired = REDIS_CONN.zcount(CONSUMER_NAME, 0, now.timestamp() - 60 * 30)
            # 如果存在过期记录，从Redis中删除这些记录
            if expired > 0:
                REDIS_CONN.zpopmin(CONSUMER_NAME, expired)
        except Exception:
            # 捕获并记录所有异常，确保状态报告循环不会中断
            logging.exception("report_status got exception")
        # 等待30秒后再次报告状态，避免过于频繁的状态更新
        await trio.sleep(30)


async def main():
    """
    任务执行器的主入口函数
    
    工作流程:
    1. 系统初始化
       - 显示版本信息
       - 初始化配置
       - 设置信号处理
    2. 内存跟踪设置
       - 根据环境变量配置
    3. 启动服务
       - 启动状态报告
       - 开始任务处理循环
    
    特性:
    - 支持内存使用跟踪
    - 优雅的错误处理
    - 可配置的并发控制
    """
    # 打印ASCII艺术字体的"Task Executor"标志，提供视觉上的系统启动标识
    logging.info(r"""
  ______           __      ______                     __            
 /_  __/___ ______/ /__   / ____/  _____  _______  __/ /_____  _____
  / / / __ `/ ___/ //_/  / __/ | |/_/ _ \/ ___/ / / / __/ __ \/ ___/
 / / / /_/ (__  ) ,<    / /____>  </  __/ /__/ /_/ / /_/ /_/ / /    
/_/  \__,_/____/_/|_|  /_____/_/|_|\___/\___/\__,_/\__/\____/_/                               
    """)
    # 记录当前RAGFlow系统版本信息，便于问题排查和版本兼容性确认
    logging.info(f'TaskExecutor: RAGFlow version: {get_ragflow_version()}')
    
    # 初始化系统配置，加载必要的环境变量和配置文件
    settings.init_settings()
    
    # 打印RAG系统的关键配置参数，如最大内容长度和每用户最大文件数
    print_rag_settings()
    
    # 在非Windows平台上设置信号处理器，用于内存跟踪和调试
    # SIGUSR1: 启动内存跟踪并生成快照
    # SIGUSR2: 停止内存跟踪
    if sys.platform != "win32":
        signal.signal(signal.SIGUSR1, start_tracemalloc_and_snapshot)
        signal.signal(signal.SIGUSR2, stop_tracemalloc)
    
    # 检查是否启用内存跟踪功能，通过环境变量控制
    # 当设置为1时，系统启动时会自动开始跟踪内存使用情况
    TRACE_MALLOC_ENABLED = int(os.environ.get('TRACE_MALLOC_ENABLED', "0"))
    if TRACE_MALLOC_ENABLED:
        start_tracemalloc_and_snapshot(None, None)

    # 使用trio库创建异步任务管理器(nursery)，用于协调并发任务
    async with trio.open_nursery() as nursery:
        # 启动状态报告任务，定期向Redis发送心跳和状态信息
        nursery.start_soon(report_status)
        
        # 主任务处理循环，持续从队列获取并处理任务
        while True:
            # 使用任务限制器控制并发任务数量，避免系统过载
            # MAX_CONCURRENT_TASKS控制最大并发任务数(默认5)
            async with task_limiter:
                # 启动新的任务处理协程
                nursery.start_soon(handle_task)
    
    # 此处代码正常情况下不会执行到，因为上面的while循环是无限循环
    # 如果执行到这里，表示发生了严重错误或意外退出
    logging.error("BUG!!! You should not reach here!!!")    

if __name__ == "__main__":
    faulthandler.enable()
    initRootLogger(CONSUMER_NAME)
    trio.run(main)
