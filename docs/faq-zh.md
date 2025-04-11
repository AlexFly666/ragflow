---
sidebar_position: 10
slug: /faq
---

# 常见问题

关于一般功能、故障排除、使用等方面的问答。

---

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 一般功能

---

### RAGFlow 与其他 RAG 产品相比有什么独特之处？

尽管大语言模型（LLM）显著提升了自然语言处理（NLP）能力，但"垃圾进垃圾出"的现状仍未改变。为此，RAGFlow 相比其他检索增强生成（RAG）产品引入了两个独特功能：

- 细粒度文档解析：文档解析包含图像和表格，并可根据需要灵活干预。
- 可追溯的答案，减少幻觉：您可以信任 RAGFlow 的回答，因为您可以查看支持这些回答的引用和参考文献。

---

### 在哪里可以找到 RAGFlow 的版本号？如何解读？

您可以在 UI 的**系统**页面找到 RAGFlow 版本号：

![Image](https://github.com/user-attachments/assets/20cf7213-2537-4e18-a88c-4dadf6228c6b)

如果您从源代码构建 RAGFlow，版本号也会显示在系统日志中：

```
        ____   ___    ______ ______ __               
       / __ \ /   |  / ____// ____// /____  _      __
      / /_/ // /| | / / __ / /_   / // __ \| | /| / /
     / _, _// ___ |/ /_/ // __/  / // /_/ /| |/ |/ / 
    /_/ |_|/_/  |_|\____//_/    /_/ \____/ |__/|__/                             

2025-02-18 10:10:43,835 INFO     1445658 RAGFlow version: v0.15.0-50-g6daae7f2 full
```

其中：

- `v0.15.0`：官方发布的版本。
- `50`：自官方发布以来的 git 提交次数。
- `g6daae7f2`：`g` 是前缀，`6daae7f2` 是当前提交 ID 的前七个字符。
- `full`/`slim`：RAGFlow 的版本。
  - `full`：完整的 RAGFlow 版本。
  - `slim`：不包含嵌入模型和 Python 包的 RAGFlow 版本。

---

### 为什么 RAGFlow 解析文档比 LangChain 花费更长时间？

我们使用视觉模型在文档预处理任务（如布局分析、表格结构识别和 OCR（光学字符识别））上投入了大量精力。这导致了额外的时间需求。

---

### 为什么 RAGFlow 比其他项目需要更多资源？

RAGFlow 内置了多个用于文档结构解析的模型，这导致了额外的计算资源需求。

---

### RAGFlow 支持哪些架构或设备？

我们官方支持 x86 CPU 和 NVIDIA GPU。虽然我们也在 ARM64 平台上测试 RAGFlow，但我们不为 ARM 维护 RAGFlow Docker 镜像。如果您在 ARM 平台上，请按照[本指南](./develop/build_docker_image.mdx)构建 RAGFlow Docker 镜像。

---

### 哪些嵌入模型可以在本地部署？

RAGFlow 提供两个 Docker 镜像版本，`v0.17.2-slim` 和 `v0.17.2`：  
  
- `infiniflow/ragflow:v0.17.2-slim`（默认）：不包含嵌入模型的 RAGFlow Docker 镜像。  
- `infiniflow/ragflow:v0.17.2`：包含以下嵌入模型的 RAGFlow Docker 镜像：
  - 内置嵌入模型：
    - `BAAI/bge-large-zh-v1.5`
    - `BAAI/bge-reranker-v2-m3`
    - `maidalun1020/bce-embedding-base_v1`
    - `maidalun1020/bce-reranker-base_v1`
  - 在 RAGFlow UI 中选择后才会下载的嵌入模型：
    - `BAAI/bge-base-en-v1.5`
    - `BAAI/bge-large-en-v1.5`
    - `BAAI/bge-small-en-v1.5`
    - `BAAI/bge-small-zh-v1.5`
    - `jinaai/jina-embeddings-v2-base-en`
    - `jinaai/jina-embeddings-v2-small-en`
    - `nomic-ai/nomic-embed-text-v1.5`
    - `sentence-transformers/all-MiniLM-L6-v2`

---

### 是否提供与第三方应用集成的 API？

相关 API 现已可用。请参阅 [RAGFlow HTTP API 参考](./references/http_api_reference.md) 或 [RAGFlow Python API 参考](./references/python_api_reference.md) 了解更多信息。

---

### 是否支持流式输出？

是的，我们支持。

---

### 是否可以通过 URL 分享对话？

不，不支持此功能。

---

### 是否支持多轮对话，将之前的对话作为当前查询的上下文？

是的，我们支持基于现有对话上下文增强用户查询：

1. 在**聊天**页面，将鼠标悬停在所需的助手对话上并选择**编辑**。
2. 在**聊天配置**弹出窗口中，点击**提示引擎**选项卡。
3. 打开**多轮优化**以启用此功能。

---

### AI 搜索和聊天的主要区别是什么？

- **AI 搜索**：这是使用预定义检索策略（加权关键词相似度和加权向量相似度的混合搜索）和系统默认聊天模型的单轮 AI 对话。它不涉及知识图谱、自动关键词或自动问题等高级 RAG 策略。检索到的文本块将列在聊天模型响应的下方。
- **AI 聊天**：这是多轮 AI 对话，您可以定义检索策略（在混合搜索中可以使用加权重排序分数替代加权向量相似度）并选择聊天模型。在 AI 聊天中，您可以为特定案例配置高级 RAG 策略，如知识图谱、自动关键词和自动问题。检索到的文本块不会与答案一起显示。

在调试聊天助手时，您可以使用 AI 搜索作为参考来验证模型设置和检索策略。

## 故障排除

---

### Docker 镜像问题

---

#### 如何从头构建 RAGFlow 镜像？

请参阅[构建 RAGFlow Docker 镜像](./develop/build_docker_image.mdx)。

---

### Huggingface 模型问题

---

#### 无法访问 https://huggingface.co

本地部署的 RAGflow 默认从 [Huggingface 网站](https://huggingface.co) 下载 OCR 和嵌入模块。如果您的机器无法访问此网站，会出现以下错误且 PDF 解析失败：

```
FileNotFoundError: [Errno 2] No such file or directory: '/root/.cache/huggingface/hub/models--InfiniFlow--deepdoc/snapshots/be0c1e50eef6047b412d1800aa89aba4d275f997/ocr.res'
```

要解决此问题，请使用 https://hf-mirror.com：

1. 停止所有容器并删除所有相关资源：

   ```bash
   cd ragflow/docker/
   docker compose down
   ```

2. 在 **ragflow/docker/.env** 中取消注释以下行：

   ```
   # HF_ENDPOINT=https://hf-mirror.com
   ```

3. 启动服务器：

   ```bash
   docker compose up -d 
   ```

---

#### `MaxRetryError: HTTPSConnectionPool(host='hf-mirror.com', port=443)`

此错误表明您没有互联网访问权限或无法连接到 hf-mirror.com。请尝试以下操作：

1. 手动从 [huggingface.co/InfiniFlow/deepdoc](https://huggingface.co/InfiniFlow/deepdoc) 下载资源文件到本地文件夹 **~/deepdoc**。
2. 在 **docker-compose.yml** 中添加卷，例如：

   ```
   - ~/deepdoc:/ragflow/rag/res/deepdoc
   ```

---

### RAGFlow 服务器问题

---

#### `WARNING: can't find /raglof/rag/res/borker.tm`

忽略此警告并继续。所有系统警告都可以忽略。

---

#### `network anomaly There is an abnormality in your network and you cannot connect to the server.`

![anomaly](https://github.com/infiniflow/ragflow/assets/93570324/beb7ad10-92e4-4a58-8886-bfb7cbd09e5d)

除非服务器完全初始化，否则您将无法登录 RAGFlow。运行 `docker logs -f ragflow-server`。

*如果您的系统显示以下内容，则表示服务器已成功初始化：*

```
     ____   ___    ______ ______ __               
    / __ \ /   |  / ____// ____// /____  _      __
   / /_/ // /| | / / __ / /_   / // __ \| | /| / /
  / _, _// ___ |/ /_/ // __/  / // /_/ /| |/ |/ / 
 /_/ |_|/_/  |_|\____//_/    /_/ \____/ |__/|__/  

 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:9380
 * Running on http://x.x.x.x:9380
 INFO:werkzeug:Press CTRL+C to quit
```

---

### RAGFlow 后端服务问题

---

#### `Realtime synonym is disabled, since no redis connection`

忽略此警告并继续。所有系统警告都可以忽略。

![](https://github.com/infiniflow/ragflow/assets/93570324/ef5a6194-084a-4fe3-bdd5-1c025b40865c)

---

#### 为什么我的文档解析进度卡在 1% 以下？

![stall](https://github.com/infiniflow/ragflow/assets/93570324/3589cc25-c733-47d5-bbfc-fedb74a3da50)

点击"解析状态"栏旁边的红色叉号，然后重新启动解析过程，看看问题是否仍然存在。如果问题仍然存在且您的 RAGFlow 是本地部署的，请尝试以下操作：

1. 检查 RAGFlow 服务器的日志，看看它是否正常运行：

   ```bash
   docker logs -f ragflow-server
   ```

2. 检查 **task_executor.py** 进程是否存在。
3. 检查您的 RAGFlow 服务器是否可以访问 hf-mirror.com 或 huggingface.com。

---

#### 为什么我的 PDF 解析在接近完成时卡住，而日志没有显示任何错误？

点击"解析状态"栏旁边的红色叉号，然后重新启动解析过程，看看问题是否仍然存在。如果问题仍然存在且您的 RAGFlow 是本地部署的，解析过程很可能因内存不足而被终止。尝试通过增加 **docker/.env** 中的 `MEM_LIMIT` 值来增加内存分配。

:::note
确保重启 RAGFlow 服务器以使更改生效！

```bash
docker compose stop
```

```bash
docker compose up -d
```

:::

![nearcompletion](https://github.com/infiniflow/ragflow/assets/93570324/563974c3-f8bb-4c8b-b241-adcda8929cbb)

---

#### `Index failure`

索引失败通常表示 Elasticsearch 服务不可用。

---

#### 如何查看 RAGFlow 的日志？

```bash
tail -f ragflow/docker/ragflow-logs/*.log
```

---

#### 如何检查 RAGFlow 中每个组件的状态？

1. 检查 Elasticsearch Docker 容器的状态：

   ```bash
   $ docker ps
   ```

   *以下是示例结果：*

   ```bash
   5bc45806b680   infiniflow/ragflow:latest     "./entrypoint.sh"        11 hours ago   Up 11 hours               0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp, 0.0.0.0:9380->9380/tcp, :::9380->9380/tcp   ragflow-server
   91220e3285dd   docker.elastic.co/elasticsearch/elasticsearch:8.11.3   "/bin/tini -- /usr/l…"   11 hours ago   Up 11 hours (healthy)     9300/tcp, 0.0.0.0:9200->9200/tcp, :::9200->9200/tcp           ragflow-es-01
   d8c86f06c56b   mysql:5.7.18        "docker-entrypoint.s…"   7 days ago     Up 16 seconds (healthy)   0.0.0.0:3306->3306/tcp, :::3306->3306/tcp     ragflow-mysql
   cd29bcb254bc   quay.io/minio/minio:RELEASE.2023-12-20T01-00-02Z       "/usr/bin/docker-ent…"   2 weeks ago    Up 11 hours      0.0.0.0:9001->9001/tcp, :::9001->9001/tcp, 0.0.0.0:9000->9000/tcp, :::9000->9000/tcp     ragflow-minio
   ```

2. 按照[本文档](./guides/run_health_check.md)检查 Elasticsearch 服务的健康状态。

:::danger 重要提示
Docker 容器的状态不一定反映服务的状态。您可能会发现即使相应的 Docker 容器正在运行，您的服务也不健康。可能的原因包括网络故障、端口号错误或 DNS 问题。
:::

---

#### `Exception: Can't connect to ES cluster`

1. 检查 Elasticsearch Docker 容器的状态：

   ```bash
   $ docker ps
   ```

   *健康的 Elasticsearch 组件的状态应如下所示：*  

   ```
   91220e3285dd   docker.elastic.co/elasticsearch/elasticsearch:8.11.3   "/bin/tini -- /usr/l…"   11 hours ago   Up 11 hours (healthy)     9300/tcp, 0.0.0.0:9200->9200/tcp, :::9200->9200/tcp           ragflow-es-01
   ```

2. 按照[本文档](./guides/run_health_check.md)检查 Elasticsearch 服务的健康状态。

:::danger 重要提示
Docker 容器的状态不一定反映服务的状态。您可能会发现即使相应的 Docker 容器正在运行，您的服务也不健康。可能的原因包括网络故障、端口号错误或 DNS 问题。
:::

3. 如果您的容器不断重启，请确保 `vm.max_map_count` >= 262144，如[此 README](https://github.com/infiniflow/ragflow?tab=readme-ov-file#-start-up-the-server) 中所述。如果您希望永久保留更改，则需要在 **/etc/sysctl.conf** 中更新 `vm.max_map_count` 值。请注意，此配置仅适用于 Linux。

---

#### 无法启动 ES 容器并出现 `Elasticsearch did not exit normally`

这是因为您忘记在 **/etc/sysctl.conf** 中更新 `vm.max_map_count` 值，并且系统重启后此值的更改被重置。

---

#### `{"data":null,"code":100,"message":"<NotFound '404: Not Found'>"}`

您的 IP 地址或端口号可能不正确。如果您使用默认配置，请在浏览器中输入 `http://<您的机器IP>`（**不是 9380，也不需要端口号！**）。这应该可以工作。

---

#### `Ollama - Mistral instance running at 127.0.0.1:11434 but cannot add Ollama as model in RagFlow`

正确的 Ollama IP 地址和端口对于添加模型到 Ollama 至关重要：

- 如果您在 demo.ragflow.io 上，请确保托管 Ollama 的服务器具有可公开访问的 IP 地址。请注意，127.0.0.1 不是可公开访问的 IP 地址。
- 如果您本地部署 RAGFlow，请确保 Ollama 和 RAGFlow 在同一局域网中并且可以相互通信。

请参阅[部署本地 LLM](./guides/models/deploy_local_llm.mdx) 了解更多信息。

---

#### 是否提供使用 DeepDoc 解析 PDF 或其他文件的示例？

是的，我们提供。请参阅 **rag/app** 文件夹下的 Python 文件。

---

#### 为什么我无法将 128MB+ 的文件上传到本地部署的 RAGFlow？

确保您更新了 **MAX_CONTENT_LENGTH** 环境变量：

1. 在 **ragflow/docker/.env** 中，取消注释环境变量 `MAX_CONTENT_LENGTH`：

   ```
   MAX_CONTENT_LENGTH=176160768 # 168MB
   ```

2. 更新 **ragflow/docker/nginx/nginx.conf**：

   ```
   client_max_body_size 168M
   ```

3. 重启 RAGFlow 服务器：

   ```
   docker compose up ragflow -d
   ```

---

#### `FileNotFoundError: [Errno 2] No such file or directory`

1. 检查 MinIO Docker 容器的状态：

   ```bash
   $ docker ps
   ```

   *健康的 Elasticsearch 组件的状态应如下所示：*  

   ```bash
   cd29bcb254bc   quay.io/minio/minio:RELEASE.2023-12-20T01-00-02Z       "/usr/bin/docker-ent…"   2 weeks ago    Up 11 hours      0.0.0.0:9001->9001/tcp, :::9001->9001/tcp, 0.0.0.0:9000->9000/tcp, :::9000->9000/tcp     ragflow-minio
   ```

2. 按照[本文档](./guides/run_health_check.md)检查 Elasticsearch 服务的健康状态。

:::danger 重要提示
Docker 容器的状态不一定反映服务的状态。您可能会发现即使相应的 Docker 容器正在运行，您的服务也不健康。可能的原因包括网络故障、端口号错误或 DNS 问题。
:::

---

## 使用

---

### 如何增加 RAGFlow 响应的长度？

1. 右键点击所需的对话以显示**聊天配置**窗口。
2. 切换到**模型设置**选项卡并调整**最大令牌数**滑块以获得所需的长度。
3. 点击**确定**确认您的更改。

---

### 如何使用本地部署的 LLM 运行 RAGFlow？

您可以使用 Ollama 或 Xinference 来部署本地 LLM。请参阅[此处](./guides/models/deploy_local_llm.mdx)了解更多信息。

---

### 如何添加不支持的 LLM？

如果您的模型目前不受支持但具有与 OpenAI 兼容的 API，请在**模型提供商**页面上点击 **OpenAI-API-Compatible** 来配置您的模型：

![openai-api-compatible](https://github.com/user-attachments/assets/b1e964f2-b86e-41af-8528-fd8a96dc5f6f)

---

### 如何将 RAGFlow 与 Ollama 互联？

- 如果 RAGFlow 是本地部署的，请确保您的 RAGFlow 和 Ollama 在同一局域网中。
- 如果您使用我们的在线演示，请确保您的 Ollama 服务器的 IP 地址是公开且可访问的。

请参阅[此处](./guides/models/deploy_local_llm.mdx)了解更多信息。

---

### 如何更改文件大小限制？

对于本地部署的 RAGFlow：每次上传的总文件大小限制为 1GB，批量上传限制为 32 个文件。每个账户的文件总数没有上限。要更新此 1GB 文件大小限制：

- 在 **docker/.env** 中，取消注释 `# MAX_CONTENT_LENGTH=1073741824`，根据需要调整值，注意 `1073741824` 表示 1GB 的字节数。
- 如果您在 **docker/.env** 中更新了 `MAX_CONTENT_LENGTH` 的值，请确保相应地更新 **nginx/nginx.conf** 中的 `client_max_body_size`。

:::tip 注意
不建议手动更改 32 个文件的批量上传限制。但是，如果您使用 RAGFlow 的 HTTP API 或 Python SDK 上传文件，32 个文件的批量上传限制会自动取消。
:::

---

### `Error: Range of input length should be [1, 30000]`

此错误发生是因为有太多文本块匹配您的搜索条件。尝试减少 **TopN** 并增加**相似度阈值**来解决此问题：

1. 点击页面中间顶部的**聊天**。
2. 右键点击所需的对话 > **编辑** > **提示引擎**
3. 减少 **TopN** 和/或提高**相似度阈值**。
4. 点击**确定**确认您的更改。

![topn](https://github.com/infiniflow/ragflow/assets/93570324/7ec72ab3-0dd2-4cff-af44-e2663b67b2fc)

---

### 如何获取用于与第三方应用集成的 API 密钥？

请参阅[获取 RAGFlow API 密钥](./develop/acquire_ragflow_api_key.md)。

---

### 如何升级 RAGFlow？

请参阅[升级 RAGFlow](./guides/upgrade_ragflow.mdx) 了解更多信息。

---
