"""
RAG工具函数模块
=============

本模块提供了RAG系统所需的各种工具函数，包括：
- 单例模式装饰器
- 文本处理工具
- 时间戳处理
- Token计数和截断
- Markdown清理
- 数值转换工具

这些工具函数被系统的其他模块广泛使用，提供了基础的功能支持。
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
#

import os
import re

import tiktoken

from api.utils.file_utils import get_project_base_directory


def singleton(cls, *args, **kw):
    """
    单例模式装饰器，确保一个类只有一个实例。
    使用进程ID作为键来支持多进程环境。
    """
    instances = {}

    def _singleton():
        key = str(cls) + str(os.getpid())
        if key not in instances:
            instances[key] = cls(*args, **kw)
        return instances[key]

    return _singleton


def rmSpace(txt):
    """
    移除文本中的多余空格，优化文本格式。
    保留标点符号和特殊字符周围的必要空格。
    """
    txt = re.sub(r"([^a-z0-9.,\)>]) +([^ ])", r"\1\2", txt, flags=re.IGNORECASE)
    return re.sub(r"([^ ]) +([^a-z0-9.,\(<])", r"\1\2", txt, flags=re.IGNORECASE)


def findMaxDt(fnm):
    """
    从文件中查找最大日期时间字符串。
    忽略无效值（nan），返回找到的最大日期时间。
    """
    m = "1970-01-01 00:00:00"
    try:
        with open(fnm, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip("\n")
                if line == 'nan':
                    continue
                if line > m:
                    m = line
    except Exception:
        pass
    return m


def findMaxTm(fnm):
    """
    从文件中查找最大时间戳值。
    忽略无效值（nan），返回找到的最大时间戳。
    """
    m = 0
    try:
        with open(fnm, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip("\n")
                if line == 'nan':
                    continue
                if int(line) > m:
                    m = int(line)
    except Exception:
        pass
    return m


# 设置tiktoken缓存目录
tiktoken_cache_dir = get_project_base_directory()
os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir
# encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
encoder = tiktoken.get_encoding("cl100k_base")


def num_tokens_from_string(string: str) -> int:
    """计算文本字符串中的token数量。"""
    try:
        return len(encoder.encode(string))
    except Exception:
        return 0


def truncate(string: str, max_len: int) -> str:
    """如果文本长度超过max_len，则截断文本。"""
    return encoder.decode(encoder.encode(string)[:max_len])

  
def clean_markdown_block(text):
    """清理Markdown代码块，移除开始和结束标记。"""
    text = re.sub(r'^\s*```markdown\s*\n?', '', text)
    text = re.sub(r'\n?\s*```\s*$', '', text)
    return text.strip()

  
def get_float(v):
    """
    安全地将值转换为浮点数。
    如果转换失败，返回负无穷大。
    """
    if v is None:
        return float('-inf')
    try:
        return float(v)
    except Exception:
        return float('-inf')

