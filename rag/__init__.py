"""
RAG (检索增强生成) 流程系统
========================

本项目实现了一个先进的RAG系统，将文档检索与语言模型生成相结合，
以提供准确且具有上下文感知的响应。

核心组件：
- 文档处理和嵌入
- 向量存储和检索
- LLM集成与生成
- 递归抽象处理
- 聚类和摘要生成

系统使用beartype进行运行时类型检查以确保类型安全。
"""

#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
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

from beartype.claw import beartype_this_package
beartype_this_package()
