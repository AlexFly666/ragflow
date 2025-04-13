# RAGflow详细课程 - 第二节（上）：架构设计与核心原理

## 引言

在上一节课中，我们学习了如何部署和配置RAGflow环境。本节课将深入探讨RAGflow的系统架构和核心工作原理，帮助大家理解RAG技术的内部机制。通过本节学习，您将掌握RAGflow的设计思想，为后续的二次开发奠定坚实的理论基础。

## 1. RAGflow系统架构解析

### 1.1 整体架构与模块划分

RAGflow采用了模块化的系统架构，主要分为以下几个核心模块：

1. **Web前端**：基于React和Ant Design构建的用户界面，提供知识库管理、文件上传、对话交互等功能。

2. **API服务层**：提供HTTP和WebSocket接口，处理前端请求，协调后端各组件的工作。

3. **文档处理引擎**：包含DeepDoc引擎，负责解析、处理各种格式的文档，提取结构化信息。

4. **RAG核心**：负责文档分块、嵌入生成、检索和重排序等核心RAG功能。

5. **LLM接口层**：统一的LLM接口，支持连接各种语言模型服务。

6. **Agent框架**：提供工作流编排功能，用于构建复杂的智能应用。

7. **存储层**：包括向量数据库、关系数据库和对象存储，管理系统中的各类数据。

这些模块之间通过明确的接口进行交互，保证了系统的解耦和可扩展性。

### 1.2 前端与后端组件交互

RAGflow的前后端交互基于以下机制：

1. **HTTP REST API**：用于处理同步请求，如用户认证、配置修改等。

2. **WebSocket**：用于处理长时间运行的任务和实时通信，如文档处理进度、聊天对话等。

3. **事件驱动架构**：后端采用事件驱动设计，保证高并发处理能力。

典型的交互流程如下：

1. 用户通过Web界面上传文档
2. 前端发送HTTP请求到API服务
3. API服务将任务分发到文档处理引擎
4. 处理引擎通过WebSocket向前端报告进度
5. 处理完成后，数据存入存储层
6. 前端查询处理结果并展示

这种设计使得系统能够处理长时间运行的任务，同时保持良好的用户体验。

### 1.3 数据流转与处理流程

在RAGflow中，数据的处理流程如下：

1. **文档上传**：
   - 用户上传文档到Web界面
   - 文档存储到MinIO对象存储
   - 元数据记录在MySQL数据库中

2. **文档解析**：
   - DeepDoc引擎从MinIO获取文档
   - 根据文档类型选择合适的解析器
   - 提取文本、识别结构、处理图表和表格

3. **文档分块**：
   - 根据选定的分块模板对文档内容进行分块
   - 生成具有语义完整性的文本片段

4. **向量化**：
   - 对每个文本块使用嵌入模型生成向量表示
   - 向量存储在Elasticsearch中
   - 建立全文索引提供关键词搜索能力

5. **检索与生成**：
   - 用户查询通过混合策略进行检索
   - 关联文本块传递给LLM
   - LLM生成回答并引用相关来源

通过这种流程，RAGflow实现了从原始文档到结构化知识，再到问答交互的完整转换。

## 2. DeepDoc文档理解引擎

### 2.1 深度文档理解的技术原理

DeepDoc是RAGflow的核心引擎之一，负责深度理解和处理各种格式的文档。它基于以下技术原理：

1. **多模态融合**：结合文本、图像和布局信息进行综合理解
2. **深度学习模型**：使用专门训练的模型处理不同类型的文档
3. **领域特定规则**：结合特定领域的规则提升处理精度
4. **层次化处理**：从像素到布局、从布局到语义的层次化处理流程

DeepDoc的独特之处在于不仅提取文本内容，还理解文档的结构和语义，这使得后续的RAG过程能够更准确地保留知识。

### 2.2 OCR与布局识别技术

对于图像格式的文档或PDF，DeepDoc使用先进的OCR和布局识别技术：

1. **OCR技术**：
   - 使用深度学习模型进行文本检测和识别
   - 支持多种语言和字体类型
   - 处理文档中的图片文本

   示例命令：
   ```bash
   python deepdoc/vision/t_ocr.py --inputs=path_to_images_or_pdfs --output_dir=path_to_store_result
   ```

2. **布局识别**：
   - 识别10种基本布局组件（文本、标题、图片、图片说明、表格、表格说明、页眉、页脚、引用、公式）
   - 理解文档的结构和组织方式
   - 确定文本块之间的逻辑关系

   示例命令：
   ```bash
   python deepdoc/vision/t_recognizer.py --inputs=path_to_images_or_pdfs --threshold=0.2 --mode=layout --output_dir=path_to_store_result
   ```

通过这些技术，DeepDoc能够将非结构化文档转换为结构化数据，为后续处理奠定基础。

### 2.3 表格结构识别（TSR）与内容重组

表格是文档中常见的复杂结构，DeepDoc提供专门的表格处理能力：

1. **表格结构识别**：
   - 识别表格中的列、行、表头、行头和跨行单元格
   - 处理层次化表头和复杂的表格布局
   - 理解单元格之间的关系

   示例命令：
   ```bash
   python deepdoc/vision/t_recognizer.py --inputs=path_to_images_or_pdfs --threshold=0.2 --mode=tsr --output_dir=path_to_store_result
   ```

2. **表格内容重组**：
   - 将表格数据重组为自然语言句子
   - 保留单元格间的逻辑关系
   - 生成适合LLM理解的表述

例如，一个简单的表格：
```
| 产品 | 价格 | 销量 |
|-----|-----|-----|
| A产品 | 100元 | 500件 |
| B产品 | 200元 | 300件 |
```

会被转换为：
```
产品A的价格是100元，销量是500件。
产品B的价格是200元，销量是300件。
```

这种转换使得LLM能够更好地理解和使用表格中的信息。

### 2.4 复杂格式文档的处理流程

除了图像和表格，DeepDoc还能处理多种复杂格式的文档：

1. **PDF文档**：
   - 提取文本内容和元数据
   - 保留页面布局和结构
   - 处理内嵌图片和表格

2. **Word文档**：
   - 解析文档结构
   - 处理样式和格式
   - 提取标题、段落和列表

3. **PowerPoint**：
   - 分析幻灯片布局
   - 提取文本和图形
   - 理解幻灯片之间的关系

4. **Excel**：
   - 处理多个工作表
   - 解析复杂公式
   - 转换数据为自然语言描述

对于每种文档类型，DeepDoc都有专门的解析器和处理流程，确保提取的信息准确完整，同时保留原始文档的结构特征。这为后续的知识检索提供了高质量的数据基础。 





### 文档处理日志

```bash
2025-04-13 16:59:09,552 INFO     8887 handle_task begin for task {"id": "8fd5591a184511f0b69ea33f73a459d7", "doc_id": "b5b1431215be11f085500738a2ff0eb3", "from_page": 0, "to_page": 13, "retry_count": 0, "kb_id": "fb16287e106d11f0a4a9c73ddb33c1ac", "parser_id": "qa", "parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "graphrag": {"use_graphrag": false}, "pages": []}, "name": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "type": "pdf", "location": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "size": 643388, "tenant_id": "e24416a9106d11f0a4a9c73ddb33c1ac", "language": "English", "embd_id": "text-embedding-v2@Tongyi-Qianwen", "pagerank": 0, "kb_parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "raptor": {"use_raptor": false}, "graphrag": {"use_graphrag": false}}, "img2txt_id": "qwen-vl-plus@Tongyi-Qianwen", "asr_id": "", "llm_id": "qwq-32b@Tongyi-Qianwen", "update_time": 1744534749459, "task_type": ""}
2025-04-13 16:59:20,115 INFO     8887 HEAD http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac [status:200 duration:0.004s]
2025-04-13 16:59:20,244 INFO     8887 From minio(0.12775207999993654) 1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf/1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf
2025-04-13 16:59:20,462 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.1, progress_msg: 16:59:20 Page(1~14): Start to parse.
2025-04-13 16:59:20,465 INFO     8887 load_model /root/ragflow/rag/res/deepdoc/det.onnx reuses cached model
2025-04-13 16:59:20,480 INFO     8887 load_model /root/ragflow/rag/res/deepdoc/rec.onnx reuses cached model
2025-04-13 16:59:22,197 INFO     8887 load_model /root/ragflow/rag/res/deepdoc/layout.onnx uses CPU
2025-04-13 16:59:22,271 INFO     8887 load_model /root/ragflow/rag/res/deepdoc/tsr.onnx uses CPU
2025-04-13 16:59:22,271 INFO     8887 task_executor_0 reported heartbeat: {"name": "task_executor_0", "now": "2025-04-13T16:59:22.227+08:00", "boot_at": "2025-04-13T16:56:50.500+08:00", "pending": 1, "lag": 0, "done": 0, "failed": 0, "current": {"8fd5591a184511f0b69ea33f73a459d7": {"id": "8fd5591a184511f0b69ea33f73a459d7", "doc_id": "b5b1431215be11f085500738a2ff0eb3", "from_page": 0, "to_page": 13, "retry_count": 0, "kb_id": "fb16287e106d11f0a4a9c73ddb33c1ac", "parser_id": "qa", "parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "graphrag": {"use_graphrag": false}, "pages": []}, "name": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "type": "pdf", "location": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "size": 643388, "tenant_id": "e24416a9106d11f0a4a9c73ddb33c1ac", "language": "English", "embd_id": "text-embedding-v2@Tongyi-Qianwen", "pagerank": 0, "kb_parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "raptor": {"use_raptor": false}, "graphrag": {"use_graphrag": false}}, "img2txt_id": "qwen-vl-plus@Tongyi-Qianwen", "asr_id": "", "llm_id": "qwq-32b@Tongyi-Qianwen", "update_time": 1744534749459, "task_type": ""}}}
Fetching 3 files:   0%|                                                                                       | 0/3 [00:00<?, ?it/s]2025-04-13 16:59:33,936 WARNING  8887 /root/ragflow/.venv/lib/python3.10/site-packages/huggingface_hub/file_download.py:1204: UserWarning: `local_dir_use_symlinks` parameter is deprecated and will be ignored. The process to download files to a local folder has been updated and do not rely on symlinks anymore. You only need to pass a destination folder as`local_dir`.
For more details, check out https://huggingface.co/docs/huggingface_hub/main/en/guides/download#download-files-to-local-folder.
  warnings.warn(

README.md: 100%|████████████████████████████████████████████████████████████████████████████████████| 307/307 [00:00<00:00, 505kB/s]
updown_concat_xgb.model: 100%|█████████████████████████████████████████████████████████████████| 5.91M/5.91M [00:02<00:00, 2.21MB/s]
Fetching 3 files: 100%|███████████████████████████████████████████████████████████████████████████████| 3/3 [00:15<00:00,  5.01s/it]
2025-04-13 16:59:49,034 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: None, progress_msg: 16:59:49 Page(1~14): OCR started
2025-04-13 16:59:52,438 INFO     8887 task_executor_0 reported heartbeat: {"name": "task_executor_0", "now": "2025-04-13T16:59:52.434+08:00", "boot_at": "2025-04-13T16:56:50.500+08:00", "pending": 1, "lag": 0, "done": 0, "failed": 0, "current": {"8fd5591a184511f0b69ea33f73a459d7": {"id": "8fd5591a184511f0b69ea33f73a459d7", "doc_id": "b5b1431215be11f085500738a2ff0eb3", "from_page": 0, "to_page": 13, "retry_count": 0, "kb_id": "fb16287e106d11f0a4a9c73ddb33c1ac", "parser_id": "qa", "parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "graphrag": {"use_graphrag": false}, "pages": []}, "name": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "type": "pdf", "location": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "size": 643388, "tenant_id": "e24416a9106d11f0a4a9c73ddb33c1ac", "language": "English", "embd_id": "text-embedding-v2@Tongyi-Qianwen", "pagerank": 0, "kb_parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "raptor": {"use_raptor": false}, "graphrag": {"use_graphrag": false}}, "img2txt_id": "qwen-vl-plus@Tongyi-Qianwen", "asr_id": "", "llm_id": "qwq-32b@Tongyi-Qianwen", "update_time": 1744534749459, "task_type": ""}}}
2025-04-13 16:59:55,625 INFO     8887 __images__ dedupe_chars cost 6.589677113999869s
2025-04-13 16:59:55,632 WARNING  8887 Miss outlines
2025-04-13 16:59:56,896 INFO     8887 __ocr detecting boxes of a image cost (1.2514416450001136s)
2025-04-13 16:59:56,909 INFO     8887 __ocr sorting 690 chars cost 0.013054896000085137s
2025-04-13 16:59:56,933 INFO     8887 __ocr recognize 28 boxes cost 0.022877225999991424s
2025-04-13 16:59:57,367 INFO     8887 __ocr detecting boxes of a image cost (0.4272408429999359s)
2025-04-13 16:59:57,378 INFO     8887 __ocr sorting 863 chars cost 0.010273640000150408s
2025-04-13 16:59:57,398 INFO     8887 __ocr recognize 52 boxes cost 0.01954498099985358s
2025-04-13 16:59:57,714 INFO     8887 __ocr detecting boxes of a image cost (0.3136186120000275s)
2025-04-13 16:59:57,721 INFO     8887 __ocr sorting 640 chars cost 0.005971657000145569s
2025-04-13 16:59:57,741 INFO     8887 __ocr recognize 64 boxes cost 0.019385551000141277s
2025-04-13 16:59:58,062 INFO     8887 __ocr detecting boxes of a image cost (0.3182989639999505s)
2025-04-13 16:59:58,073 INFO     8887 __ocr sorting 1192 chars cost 0.01081610999995064s
2025-04-13 16:59:58,095 INFO     8887 __ocr recognize 33 boxes cost 0.020856687000105012s
2025-04-13 16:59:58,391 INFO     8887 __ocr detecting boxes of a image cost (0.29331887900002585s)
2025-04-13 16:59:58,399 INFO     8887 __ocr sorting 1168 chars cost 0.007227673999977924s
2025-04-13 16:59:58,418 INFO     8887 __ocr recognize 34 boxes cost 0.018993098000009923s
2025-04-13 16:59:58,753 INFO     8887 __ocr detecting boxes of a image cost (0.3307604320000337s)
2025-04-13 16:59:58,767 INFO     8887 __ocr sorting 1118 chars cost 0.013935287000094831s
2025-04-13 16:59:58,826 INFO     8887 __ocr recognize 33 boxes cost 0.0585276580000027s
2025-04-13 16:59:58,843 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.2769230769230769, progress_msg: 
2025-04-13 16:59:59,412 INFO     8887 __ocr detecting boxes of a image cost (0.5643075259999932s)
2025-04-13 16:59:59,428 INFO     8887 __ocr sorting 1179 chars cost 0.015957321999849228s
2025-04-13 16:59:59,453 INFO     8887 __ocr recognize 34 boxes cost 0.023884223000095517s
2025-04-13 16:59:59,980 INFO     8887 __ocr detecting boxes of a image cost (0.5217306179999923s)
2025-04-13 16:59:59,991 INFO     8887 __ocr sorting 1099 chars cost 0.01069579199997861s
2025-04-13 17:00:00,014 INFO     8887 __ocr recognize 32 boxes cost 0.020549737000010282s
2025-04-13 17:00:00,393 INFO     8887 __ocr detecting boxes of a image cost (0.375160711000035s)
2025-04-13 17:00:00,404 INFO     8887 __ocr sorting 1028 chars cost 0.009043359999850509s
2025-04-13 17:00:00,424 INFO     8887 __ocr recognize 31 boxes cost 0.020358155999929295s
2025-04-13 17:00:00,733 INFO     8887 __ocr detecting boxes of a image cost (0.30339712200020585s)
2025-04-13 17:00:00,742 INFO     8887 __ocr sorting 868 chars cost 0.008706123999900228s
2025-04-13 17:00:00,769 INFO     8887 __ocr recognize 29 boxes cost 0.026292628000192053s
2025-04-13 17:00:01,077 INFO     8887 __ocr detecting boxes of a image cost (0.30430582899998626s)
2025-04-13 17:00:01,088 INFO     8887 __ocr sorting 958 chars cost 0.010096992999933718s
2025-04-13 17:00:01,109 INFO     8887 __ocr recognize 29 boxes cost 0.020842963999939457s
2025-04-13 17:00:01,457 INFO     8887 __ocr detecting boxes of a image cost (0.34347475900017344s)
2025-04-13 17:00:01,464 INFO     8887 __ocr sorting 800 chars cost 0.006769193999843992s
2025-04-13 17:00:01,486 INFO     8887 __ocr recognize 28 boxes cost 0.021316642000101638s
2025-04-13 17:00:01,500 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.5538461538461538, progress_msg: 
2025-04-13 17:00:01,812 INFO     8887 __ocr detecting boxes of a image cost (0.30787622000002557s)
2025-04-13 17:00:01,816 INFO     8887 __ocr sorting 307 chars cost 0.0025588350001726212s
2025-04-13 17:00:01,839 INFO     8887 __ocr recognize 10 boxes cost 0.022857862000137175s
2025-04-13 17:00:01,841 INFO     8887 __images__ 13 pages cost 6.204996478000112s
2025-04-13 17:00:01,855 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: None, progress_msg: 17:00:01 Page(1~14): OCR finished (12.85s)
2025-04-13 17:00:05,870 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:05] "GET /v1/user/tenant_info HTTP/1.1" 200 -
2025-04-13 17:00:06,018 INFO     8886 HEAD http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac [status:200 duration:0.085s]
2025-04-13 17:00:06,021 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:06] "GET /v1/user/info HTTP/1.1" 200 -
2025-04-13 17:00:06,043 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:06] "GET /v1/document/list?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac&keywords=&page_size=10&page=1 HTTP/1.1" 200 -
2025-04-13 17:00:06,049 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:06] "GET /v1/kb/detail?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac HTTP/1.1" 200 -
2025-04-13 17:00:06,303 INFO     8886 POST http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac/_search [status:200 duration:0.020s]
2025-04-13 17:00:06,306 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:06] "GET /v1/kb/fb16287e106d11f0a4a9c73ddb33c1ac/knowledge_graph HTTP/1.1" 200 -
2025-04-13 17:00:17,718 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:17] "GET /v1/user/info HTTP/1.1" 200 -
2025-04-13 17:00:17,762 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:17] "GET /v1/user/tenant_info HTTP/1.1" 200 -
2025-04-13 17:00:17,811 INFO     8886 HEAD http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac [status:200 duration:0.007s]
2025-04-13 17:00:17,815 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:17] "GET /v1/document/list?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac&keywords=&page_size=10&page=1 HTTP/1.1" 200 -
2025-04-13 17:00:17,834 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:17] "GET /v1/kb/detail?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac HTTP/1.1" 200 -
2025-04-13 17:00:18,118 INFO     8886 POST http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac/_search [status:200 duration:0.010s]
2025-04-13 17:00:18,173 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:18] "GET /v1/kb/fb16287e106d11f0a4a9c73ddb33c1ac/knowledge_graph HTTP/1.1" 200 -
2025-04-13 17:00:19,062 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:19] "GET /v1/user/info HTTP/1.1" 200 -
2025-04-13 17:00:19,126 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:19] "GET /v1/user/tenant_info HTTP/1.1" 200 -
2025-04-13 17:00:19,146 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:19] "GET /v1/document/list?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac&keywords=&page_size=10&page=1 HTTP/1.1" 200 -
2025-04-13 17:00:19,152 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:19] "GET /v1/kb/detail?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac HTTP/1.1" 200 -
2025-04-13 17:00:19,156 INFO     8886 HEAD http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac [status:200 duration:0.005s]
2025-04-13 17:00:19,321 INFO     8886 POST http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac/_search [status:200 duration:0.013s]
2025-04-13 17:00:19,324 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:19] "GET /v1/kb/fb16287e106d11f0a4a9c73ddb33c1ac/knowledge_graph HTTP/1.1" 200 -
2025-04-13 17:00:22,541 INFO     8887 task_executor_0 reported heartbeat: {"name": "task_executor_0", "now": "2025-04-13T17:00:22.539+08:00", "boot_at": "2025-04-13T16:56:50.500+08:00", "pending": 1, "lag": 0, "done": 0, "failed": 0, "current": {"8fd5591a184511f0b69ea33f73a459d7": {"id": "8fd5591a184511f0b69ea33f73a459d7", "doc_id": "b5b1431215be11f085500738a2ff0eb3", "from_page": 0, "to_page": 13, "retry_count": 0, "kb_id": "fb16287e106d11f0a4a9c73ddb33c1ac", "parser_id": "qa", "parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "graphrag": {"use_graphrag": false}, "pages": []}, "name": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "type": "pdf", "location": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "size": 643388, "tenant_id": "e24416a9106d11f0a4a9c73ddb33c1ac", "language": "English", "embd_id": "text-embedding-v2@Tongyi-Qianwen", "pagerank": 0, "kb_parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "raptor": {"use_raptor": false}, "graphrag": {"use_graphrag": false}}, "img2txt_id": "qwen-vl-plus@Tongyi-Qianwen", "asr_id": "", "llm_id": "qwq-32b@Tongyi-Qianwen", "update_time": 1744534749459, "task_type": ""}}}
2025-04-13 17:00:23,644 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:23] "GET /v1/llm/list HTTP/1.1" 200 -
2025-04-13 17:00:24,257 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:24] "GET /v1/user/tenant_info HTTP/1.1" 200 -
2025-04-13 17:00:24,280 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:24] "GET /v1/document/list?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac&keywords=&page_size=10&page=1 HTTP/1.1" 200 -
2025-04-13 17:00:35,539 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.63, progress_msg: 17:00:35 Page(1~14): Layout analysis (33.65s)
2025-04-13 17:00:36,238 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.65, progress_msg: 17:00:36 Page(1~14): Table analysis (0.68s)
2025-04-13 17:00:36,262 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.67, progress_msg: 17:00:36 Page(1~14): Text merged (0.00s)
2025-04-13 17:00:37,379 INFO     8887 Chunking(77.26273144899983) 1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf/1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf done
2025-04-13 17:00:40,607 INFO     8887 MINIO PUT(1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf):2.8972152600001664
2025-04-13 17:00:40,621 INFO     8887 Build document 1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf: 80.50s
2025-04-13 17:00:40,649 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: None, progress_msg: 17:00:40 Page(1~14): Generate 12 chunks
2025-04-13 17:00:42,746 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.7166666666666667, progress_msg: 
2025-04-13 17:00:42,748 INFO     8887 Embedding chunks (2.10s)
2025-04-13 17:00:42,768 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: None, progress_msg: 17:00:42 Page(1~14): Embedding chunks (2.10s)
2025-04-13 17:00:43,195 INFO     8887 PUT http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac/_bulk?refresh=false&timeout=60s [status:200 duration:0.359s]
2025-04-13 17:00:43,457 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 0.8083333333333333, progress_msg: 
2025-04-13 17:00:43,544 INFO     8887 PUT http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac/_bulk?refresh=false&timeout=60s [status:200 duration:0.054s]
2025-04-13 17:00:43,926 INFO     8887 PUT http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac/_bulk?refresh=false&timeout=60s [status:200 duration:0.063s]
2025-04-13 17:00:44,153 INFO     8887 Indexing doc(1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf), page(0-13), chunks(12), elapsed: 1.39
2025-04-13 17:00:44,199 INFO     8887 set_progress(8fd5591a184511f0b69ea33f73a459d7), progress: 1.0, progress_msg: 17:00:44 Page(1~14): Indexing done (1.40s). Task done (94.61s)
2025-04-13 17:00:44,199 INFO     8887 Chunk doc(1-深圳市算力基础设施高质量发展行动计划（2024-2025）-20231205.pdf), page(0-13), chunks(12), token(6256), elapsed:94.61
2025-04-13 17:00:44,201 INFO     8887 handle_task done for task {"id": "8fd5591a184511f0b69ea33f73a459d7", "doc_id": "b5b1431215be11f085500738a2ff0eb3", "from_page": 0, "to_page": 13, "retry_count": 0, "kb_id": "fb16287e106d11f0a4a9c73ddb33c1ac", "parser_id": "qa", "parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "graphrag": {"use_graphrag": false}, "pages": []}, "name": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "type": "pdf", "location": "1-\u6df1\u5733\u5e02\u7b97\u529b\u57fa\u7840\u8bbe\u65bd\u9ad8\u8d28\u91cf\u53d1\u5c55\u884c\u52a8\u8ba1\u5212\uff082024-2025\uff09-20231205.pdf", "size": 643388, "tenant_id": "e24416a9106d11f0a4a9c73ddb33c1ac", "language": "English", "embd_id": "text-embedding-v2@Tongyi-Qianwen", "pagerank": 0, "kb_parser_config": {"layout_recognize": "Plain Text", "chunk_token_num": 512, "delimiter": "\n!?;\u3002\uff1b\uff01\uff1f", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "raptor": {"use_raptor": false}, "graphrag": {"use_graphrag": false}}, "img2txt_id": "qwen-vl-plus@Tongyi-Qianwen", "asr_id": "", "llm_id": "qwq-32b@Tongyi-Qianwen", "update_time": 1744534749459, "task_type": ""}
2025-04-13 17:00:48,909 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:48] "GET /v1/user/info HTTP/1.1" 200 -
2025-04-13 17:00:48,955 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:48] "GET /v1/document/list?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac&keywords=&page_size=10&page=1 HTTP/1.1" 200 -
2025-04-13 17:00:48,959 INFO     8886 HEAD http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac [status:200 duration:0.009s]
2025-04-13 17:00:48,967 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:48] "GET /v1/user/tenant_info HTTP/1.1" 200 -
2025-04-13 17:00:49,070 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:49] "GET /v1/kb/detail?kb_id=fb16287e106d11f0a4a9c73ddb33c1ac HTTP/1.1" 200 -
2025-04-13 17:00:49,112 INFO     8886 POST http://localhost:1200/ragflow_e24416a9106d11f0a4a9c73ddb33c1ac/_search [status:200 duration:0.009s]
2025-04-13 17:00:49,115 INFO     8886 127.0.0.1 - - [13/Apr/2025 17:00:49] "GET /v1/kb/fb16287e106d11f0a4a9c73ddb33c1ac/knowledge_graph HTTP/1.1" 200 -
2025-04-13 17:00:52,615 INFO     8887 task_executor_0 reported heartbeat: {"name": "task_executor_0", "now": "2025-04-13T17:00:52.614+08:00", "boot_at": "2025-04-13T16:56:50.500+08:00", "pending": 0, "lag": 0, "done": 1, "failed": 0, "current": {}}

```

