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

import io

import numpy as np
from PIL import Image

from api.db import LLMType
from api.db.services.llm_service import LLMBundle
from deepdoc.vision import OCR
from rag.nlp import tokenize
from rag.utils import clean_markdown_block

ocr = OCR()

# 主要功能:处理图片文件
# - 使用OCR提取图片中的文本
# - 使用图像理解模型生成图片描述
# - 支持多种图片格式
# - 处理图片中的表格和图表
def chunk(filename, binary, tenant_id, lang, callback=None, **kwargs):
    """图片处理和分析主函数
    
    处理流程:
    1. 加载并预处理图片
    2. 使用OCR提取文本
    3. 使用计算机视觉模型分析图片内容
    4. 合并文本和视觉分析结果
    
    Args:
        filename: 图片文件名
        binary: 图片二进制数据
        tenant_id: 租户ID
        lang: 处理语言
        callback: 进度回调函数
        **kwargs: 额外参数
        
    Returns:
        list: 包含处理结果的文档块列表,每个块包含:
        - 文本内容(OCR结果)
        - 图片描述
        - 图片对象
        - 元数据
    """
    img = Image.open(io.BytesIO(binary)).convert('RGB')
    doc = {
        "docnm_kwd": filename,
        "image": img
    }
    
    # 使用OCR提取文本
    bxs = ocr(np.array(img))
    txt = "\n".join([t[0] for _, t in bxs if t[0]])
    eng = lang.lower() == "english"
    callback(0.4, "Finish OCR: (%s ...)" % txt[:12])
    
    # 如果OCR文本足够长,直接使用OCR结果
    if (eng and len(txt.split()) > 32) or len(txt) > 32:
        tokenize(doc, txt, eng)
        callback(0.8, "OCR results is too long to use CV LLM.")
        return [doc]

    try:
        # 使用计算机视觉模型分析图片
        callback(0.4, "Use CV LLM to describe the picture.")
        cv_mdl = LLMBundle(tenant_id, LLMType.IMAGE2TEXT, lang=lang)
        img_binary = io.BytesIO()
        img.save(img_binary, format='JPEG')
        img_binary.seek(0)
        
        # 获取图片描述
        ans = cv_mdl.describe(img_binary.read())
        callback(0.8, "CV LLM respond: %s ..." % ans[:32])
        
        # 合并OCR文本和图片描述
        txt += "\n" + ans
        tokenize(doc, txt, eng)
        return [doc]
    except Exception as e:
        callback(prog=-1, msg=str(e))

    return []


def vision_llm_chunk(binary, vision_model, prompt=None, callback=None):
    """使用视觉语言模型处理图片
    
    这是一个简单的包装器,用于:
    1. 将图片转换为markdown格式的文本描述
    2. 支持自定义提示词引导生成
    3. 处理异常情况
    
    Args:
        binary: 图片二进制数据
        vision_model: 视觉语言模型实例
        prompt: 自定义提示词(可选)
        callback: 进度回调函数
        
    Returns:
        str: 生成的markdown格式文本描述
    """
    callback = callback or (lambda prog, msg: None)

    img = binary
    txt = ""

    try:
        # 准备图片数据
        img_binary = io.BytesIO()
        img.save(img_binary, format='JPEG')
        img_binary.seek(0)

        # 使用视觉模型生成描述
        ans = clean_markdown_block(vision_model.describe_with_prompt(img_binary.read(), prompt))
        txt += "\n" + ans
        return txt

    except Exception as e:
        callback(-1, str(e))

    return ""
