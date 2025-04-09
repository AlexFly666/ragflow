# RAGflow详细课程 - 第一节：部署与环境配置

## 引言

欢迎来到RAGflow课程。在本节课中，我们将深入学习RAGflow的部署和环境配置，帮助大家快速搭建起一个功能完善的RAG应用开发环境。无论您是想尝试RAGflow，还是计划在生产环境中使用它，本课程都将为您提供全面的指导。

## 1. RAGflow系统介绍

### 1.1 RAGflow的定位与核心优势

RAGflow是一个开源的RAG（检索增强生成）引擎，基于深度文档理解技术。它为任何规模的企业提供了流畅的RAG工作流程，结合了大型语言模型（LLM）以提供真实可靠的问答能力，支持引用来自各种复杂格式数据的引证。

与其他RAG框架相比，RAGflow的核心优势包括：

- **深度文档理解**：能够从复杂格式的非结构化数据中提取知识
- **模板化分块**：智能且可解释的文档分块策略
- **有据可依的引用**：可视化文本分块，允许人工干预
- **多源数据兼容**：支持Word、PPT、Excel、PDF、图像等多种数据源
- **自动化RAG工作流**：为个人和大型企业定制的流程编排

### 1.2 基于深度文档理解的工作原理

RAGflow的核心是[DeepDoc](https://github.com/infiniflow/ragflow/blob/main/deepdoc/README_zh.md)引擎，它能够理解文档的语义、结构和布局，从而更准确地提取知识。DeepDoc包含以下关键技术：

- **OCR技术**：能够从图像或PDF中精确提取文本
- **布局识别**：识别文档中的标题、正文、表格、图片等不同元素
- **表格结构识别（TSR）**：理解复杂表格结构，包括层次标题、跨行单元格等
- **内容重组**：将识别后的内容重新组织成自然语言句子，便于LLM理解

这些技术使RAGflow能够从几乎任何文档格式中提取结构化知识，真正实现"从文档到知识"的转换。

### 1.3 "Quality in, quality out"的核心理念

RAGflow坚持"输入质量决定输出质量"的理念。这意味着：

- 文档解析的质量直接影响最终回答的质量
- 分块的质量决定了检索的精确度
- 索引的质量影响系统的响应速度

在RAGflow中，每一步都经过精心设计，以确保知识从输入到输出的整个流程中保持高质量。系统提供了可视化工具来检查和干预处理过程，确保数据质量。

## 2. 部署环境要求与准备

### 2.1 硬件要求

RAGflow对硬件有一定要求，以确保系统运行流畅：

- **CPU**：至少4核心
- **RAM**：至少16GB
- **磁盘空间**：至少50GB
- **GPU**（可选）：如需加速嵌入和DeepDoc任务，建议配置NVIDIA GPU

在生产环境中，建议根据预期的文档量和并发用户数适当提高配置。特别是当处理大量PDF或图像文档时，更多的内存和CPU核心会显著提升性能。

### 2.2 Docker环境配置

RAGflow基于Docker容器技术，这使得部署变得简单和一致。在开始前，请确保：

1. 安装Docker（>= 24.0.0）和Docker Compose（>= v2.26.1）
   ```bash
   # 检查Docker版本
   docker --version
   # 检查Docker Compose版本
   docker compose version
   ```

2. 确保Docker服务正在运行
   ```bash
   # 在Linux上检查Docker服务状态
   systemctl status docker
   # 如果未运行，启动Docker服务
   systemctl start docker
   ```

3. 确保当前用户在docker组中（避免使用sudo）
   ```bash
   # 将当前用户添加到docker组
   sudo usermod -aG docker $USER
   # 重新登录以使更改生效
   ```

### 2.3 系统参数优化

Elasticsearch是RAGflow的重要组件，需要调整一些系统参数：

1. 设置vm.max_map_count至少为262144：
   ```bash
   # 检查当前值
   sysctl vm.max_map_count
   
   # 临时设置（重启后失效）
   sudo sysctl -w vm.max_map_count=262144
   
   # 永久设置（添加到/etc/sysctl.conf）
   echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

2. 其他可选的系统优化：
   - 增加文件描述符限制
   - 调整TCP连接参数
   - 设置交换空间策略

这些系统优化对于处理大量文档和并发请求尤为重要。

## 3. 部署方式与实践

### 3.1 使用预构建Docker镜像的快速部署

RAGflow提供了预构建的Docker镜像，使部署过程变得简单：

1. 克隆RAGflow仓库：
   ```bash
   git clone https://github.com/infiniflow/ragflow.git
   cd ragflow/docker
   ```

2. 启动服务（CPU版本）：
   ```bash
   docker compose -f docker-compose.yml up -d
   ```

3. 如果要使用GPU加速：
   ```bash
   docker compose -f docker-compose-gpu.yml up -d
   ```

4. 检查服务状态：
   ```bash
   docker logs -f ragflow-server
   ```

成功启动后，可以通过浏览器访问服务器IP地址，默认使用80端口。

### 3.2 不同版本镜像的选择

RAGflow提供了不同版本的镜像，根据需求选择：

| 镜像标签 | 大小(GB) | 包含嵌入模型? | 稳定性 |
|---------|---------|-------------|-------|
| v0.17.2 | ~9 | ✓ | 稳定发布版 |
| v0.17.2-slim | ~2 | ✗ | 稳定发布版 |
| nightly | ~9 | ✓ | 不稳定夜间构建版 |
| nightly-slim | ~2 | ✗ | 不稳定夜间构建版 |

选择建议：
- 如果有足够的磁盘空间且希望使用本地嵌入模型，选择完整版本（v0.17.2）
- 如果磁盘空间有限或计划使用远程嵌入服务，选择精简版本（v0.17.2-slim）
- 生产环境建议使用稳定版本，开发测试可以尝试nightly版本

### 3.3 GPU加速方案配置

对于大量文档处理，GPU加速可以显著提高性能：

1. 确保服务器安装了NVIDIA驱动和CUDA
   ```bash
   # 检查NVIDIA驱动和CUDA安装
   nvidia-smi
   ```

2. 安装NVIDIA Container Toolkit
   ```bash
   # 安装NVIDIA Container Toolkit
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

3. 使用GPU版docker-compose文件启动服务
   ```bash
   docker compose -f docker-compose-gpu.yml up -d
   ```

GPU加速主要用于以下任务：
- 嵌入模型计算
- DeepDoc的OCR和布局识别
- 本地部署的LLM（如果使用）

### 3.4 从源代码部署与开发环境设置

对于开发人员，从源代码部署提供了更多的灵活性：

1. 克隆代码并安装依赖：
   ```bash
   git clone https://github.com/infiniflow/ragflow.git
   cd ragflow/
   
   # 安装uv包管理工具
   pipx install uv
   export UV_INDEX=https://mirrors.aliyun.com/pypi/simple
   # uv命令生效
   pipx ensurepath
   
   # 安装Python依赖
   uv sync --python 3.10 --all-extras  # 完整版
   ```

2. 启动第三方服务：
   ```bash
   docker-compose -f docker/docker-compose-base.yml up -d --force-recreate
   ```

3. 更新hosts文件：

   > 在 `/etc/hosts` 中添加以下代码，将 **conf/service_conf.yaml** 文件中的所有 host 地址都解析为 `127.0.0.1`

   ```bash
   # 添加到/etc/hosts
   127.0.0.1 es01 infinity mysql minio redis
   ```

4. 启动后端服务：
   ```bash
   source .venv/bin/activate
   export PYTHONPATH=$(pwd)
   
   # 如果无法访问HuggingFace，设置镜像
   export HF_ENDPOINT=https://hf-mirror.com
   
   # 启动后端服务
   bash docker/launch_backend_service.sh
   ```

5. 启动前端服务：
   ```bash
   cd web
   apt install npm
   npm install
   # 更新.umirc.ts中的proxy.target为自己的后端地址，如http://127.0.0.1:9380
   npm run dev
   ```

这种方式适合进行开发、调试和自定义功能。

## 4. 系统配置与自定义

### 4.1 依赖组件环境变量配置（.env文件）

RAGflow使用`docker/.env`文件来管理环境变量，主要配置项包括：

```bash
# 文档引擎类型
# 可用选项：
# - `elasticsearch` (默认) 
# - `infinity` (https://github.com/infiniflow/infinity)
DOC_ENGINE=${DOC_ENGINE:-elasticsearch}

# ------------------------------
# docker 环境变量，用于在启动时指定向量数据库类型
# (基于向量数据库类型，将使用相应的 docker compose 配置)
# COMPOSE_PROFILES 是 Docker Compose 提供的一个环境变量，
# 用于在运行 docker-compose up 命令时自动激活指定的配置文件 (profiles)。
# ------------------------------
COMPOSE_PROFILES=${DOC_ENGINE}

# Elasticsearch 版本
STACK_VERSION=8.11.3

# Elasticsearch 服务暴露的主机名
ES_HOST=es01

# 用于将 Elasticsearch 服务暴露给主机的端口，
# 允许从外部访问 Docker 容器内运行的服务
ES_PORT=1200

# Elasticsearch 密码
ELASTIC_PASSWORD=infini_rag_flow

# 用于将 Kibana 服务暴露给主机的端口，
# 允许从外部访问 Docker 容器内运行的服务
KIBANA_PORT=6601
KIBANA_USER=rag_flow
KIBANA_PASSWORD=infini_rag_flow

# Docker 容器运行时可以使用的最大内存量（以字节为单位）
# 根据主机可用内存更新此值
# MEM_LIMIT=8073741824
MEM_LIMIT=2147483648

# Infinity 服务暴露的主机名
INFINITY_HOST=infinity

# 将 Infinity API 暴露给主机的端口
INFINITY_THRIFT_PORT=23817
INFINITY_HTTP_PORT=23820
INFINITY_PSQL_PORT=5432

# MySQL 密码
MYSQL_PASSWORD=infini_rag_flow
# MySQL 服务暴露的主机名
MYSQL_HOST=mysql
# 要使用的 MySQL 服务数据库
MYSQL_DBNAME=rag_flow
# 用于将 MySQL 服务暴露给主机的端口，
# 允许从外部访问 Docker 容器内运行的 MySQL 数据库
MYSQL_PORT=5455

# MinIO 服务暴露的主机名
MINIO_HOST=minio
# 用于将 MinIO 控制台界面暴露给主机的端口，
# 允许从外部访问 Docker 容器内运行的基于 Web 的控制台
MINIO_CONSOLE_PORT=9001
# 用于将 MinIO API 服务暴露给主机的端口，
# 允许从外部访问 Docker 容器内运行的 MinIO 对象存储服务
MINIO_PORT=9000
# MinIO 用户名
# 更新时，必须相应修改 service_conf.yaml 中的 `minio.user` 条目
MINIO_USER=rag_flow
# MinIO 密码
# 更新时，必须相应修改 service_conf.yaml 中的 `minio.password` 条目
MINIO_PASSWORD=infini_rag_flow

# Redis 服务暴露的主机名
REDIS_HOST=redis
# 用于将 Redis 服务暴露给主机的端口，
# 允许从外部访问 Docker 容器内运行的 Redis 服务
REDIS_PORT=6379
# Redis 密码
REDIS_PASSWORD=infini_rag_flow

# 用于将 RAGFlow 的 HTTP API 服务暴露给主机的端口，
# 允许从外部访问 Docker 容器内运行的服务
SVR_HTTP_PORT=9380

# 要下载的 RAGFlow Docker 镜像
# 默认为 v0.17.2-slim 版本，这是不包含嵌入模型的 RAGFlow Docker 镜像
RAGFLOW_IMAGE=infiniflow/ragflow:v0.17.2-slim
#
# 要下载包含嵌入模型的 RAGFlow Docker 镜像，请取消注释以下行：
# RAGFLOW_IMAGE=infiniflow/ragflow:v0.17.2
# 
# v0.17.2 版本的 Docker 镜像包含：
# - 内置嵌入模型：
#   - BAAI/bge-large-zh-v1.5
#   - BAAI/bge-reranker-v2-m3
#   - maidalun1020/bce-embedding-base_v1
#   - maidalun1020/bce-reranker-base_v1
# - 在 RAGFlow UI 中选择后将下载的嵌入模型：
#   - BAAI/bge-base-en-v1.5
#   - BAAI/bge-large-en-v1.5
#   - BAAI/bge-small-en-v1.5
#   - BAAI/bge-small-zh-v1.5
#   - jinaai/jina-embeddings-v2-base-en
#   - jinaai/jina-embeddings-v2-small-en
#   - nomic-ai/nomic-embed-text-v1.5
#   - sentence-transformers/all-MiniLM-L6-v2

# 如果无法下载 RAGFlow Docker 镜像：
#
# - 对于 `nightly-slim` 版本，取消注释以下任一行：
# RAGFLOW_IMAGE=swr.cn-north-4.myhuaweicloud.com/infiniflow/ragflow:nightly-slim
# RAGFLOW_IMAGE=registry.cn-hangzhou.aliyuncs.com/infiniflow/ragflow:nightly-slim
#
# - 对于 `nightly` 版本，取消注释以下任一行：
# RAGFLOW_IMAGE=swr.cn-north-4.myhuaweicloud.com/infiniflow/ragflow:nightly
# RAGFLOW_IMAGE=registry.cn-hangzhou.aliyuncs.com/infiniflow/ragflow:nightly

# 本地时区
TIMEZONE='Asia/Shanghai'

# 如果您访问 huggingface.co 受限，请取消注释以下行：
# HF_ENDPOINT=https://hf-mirror.com

# MacOS 的优化设置
# 如果您的操作系统是 MacOS，请取消注释以下行：
# MACOS=1

# 知识库或文件管理中每次上传的最大文件大小限制（以字节为单位）
# 要更改 1GB 的文件大小限制，请取消注释下面的行并根据需要更新
# MAX_CONTENT_LENGTH=1073741824
# 更新后，确保相应更新 nginx/nginx.conf 中的 `client_max_body_size`
# 注意，`MAX_CONTENT_LENGTH` 和 `client_max_body_size` 都不会设置上传到代理的文件的最大大小
# 详见 https://ragflow.io/docs/dev/begin_component

# RAGFlow 自有包和导入包的日志级别
# 可用级别：
# - `DEBUG`
# - `INFO`（默认）
# - `WARNING`
# - `ERROR`
# 例如，以下行将 `ragflow.es_conn` 的日志级别更改为 `DEBUG`：
# LOG_LEVELS=ragflow.es_conn=DEBUG

# 阿里云 OSS 配置
# STORAGE_IMPL=OSS
# ACCESS_KEY=xxx
# SECRET_KEY=eee
# ENDPOINT=http://oss-cn-hangzhou.aliyuncs.com
# REGION=cn-hangzhou
# BUCKET=ragflow65536

# 用户注册开关
REGISTER_ENABLED=1

```

这些变量会在启动容器时被加载，影响系统的基本行为。

### 4.2 服务配置（`conf/service_conf.yaml`）

`conf/service_conf.yaml`是RAGflow的核心配置文件，定义了后端服务的行为：

```yaml
# RAGFlow 服务配置
ragflow:
  # 服务监听地址
  host: 0.0.0.0
  # HTTP 服务端口
  http_port: 9380

# MySQL 数据库配置
mysql:
  # 数据库名称
  name: 'rag_flow'
  # 数据库用户名
  user: 'root'
  # 数据库密码
  password: 'infini_rag_flow'
  # 数据库主机地址
  host: 'localhost'
  # 数据库端口
  port: 5455
  # 最大连接数
  max_connections: 100
  # 连接超时时间（秒）
  stale_timeout: 30

# MinIO 对象存储配置
minio:
  # MinIO 用户名
  user: 'rag_flow'
  # MinIO 密码
  password: 'infini_rag_flow'
  # MinIO 服务地址
  host: 'localhost:9000'

# Elasticsearch 配置
es:
  # ES 服务地址
  hosts: 'http://localhost:1200'
  # ES 用户名
  username: 'elastic'
  # ES 密码
  password: 'infini_rag_flow'

# Infinity 向量数据库配置
infinity:
  # Infinity 服务地址
  uri: 'localhost:23817'
  # 默认数据库名称
  db_name: 'default_db'

# Redis 缓存配置
redis:
  # Redis 数据库索引
  db: 1
  # Redis 密码
  password: 'infini_rag_flow'
  # Redis 服务地址
  host: 'localhost:6379'
```

修改此文件可以自定义RAGflow的各种行为，如使用不同的LLM、嵌入模型或存储方式。

### 4.3 LLM与嵌入模型配置

RAGflow支持多种LLM和嵌入模型：

1. LLM配置：
   - OpenAI (GPT-3.5/4)
   - Azure OpenAI
   - Anthropic (Claude)
   - SiliconFlow
   - 本地模型 (Ollama)

   示例配置：
   ```yaml
   user_default_llm:
     factory: openai
     model: gpt-4o
     api_key: sk-xxx
     api_base: https://api.openai.com/v1
   ```

2. 嵌入模型配置：
   - BAAI/bge系列模型
   - Jina Embeddings
   - Nomic Embed
   - OpenAI Embeddings
   
   示例配置：
   ```yaml
   embedding_models:
     - name: bge-large-en-v1.5
       local: true
       device: gpu
     - name: openai
       local: false
       api_key: ${OPENAI_API_KEY}
   ```

选择合适的模型是平衡性能和成本的关键。本地模型降低了成本和延迟，而商业API通常提供更好的质量。

### 4.4 第三方服务连接

RAGflow依赖多个第三方服务：

1. **Elasticsearch**：存储向量嵌入和提供全文搜索
   ```yaml
   es_info:
     host: es01
     port: 9200
     user: elastic
     password: ${ES_PASSWORD}
     verify_certs: false
   ```

2. **MinIO**：对象存储，用于存储原始文档和处理结果
   ```yaml
   minio_info:
     endpoint: http://minio:9000
     access_key: ${MINIO_ROOT_USER}
     secret_key: ${MINIO_ROOT_PASSWORD}
     secure: false
   ```

3. **MySQL**：关系数据库，存储元数据和用户信息
   ```yaml
   db_info:
     host: mysql
     port: 3306
     user: ${MYSQL_USER}
     password: ${MYSQL_PASSWORD}
     database: ${MYSQL_DATABASE}
   ```

4. **Redis**：缓存和消息队列
   ```yaml
   redis_info:
     host: redis
     port: 6379
     password: ""
   ```

正确配置这些服务是系统稳定运行的基础。

## 5. 健康检查与故障排除

### 5.1 服务启动验证

部署完成后，验证各组件是否正常工作：

1. 检查容器状态：
   ```bash
   docker ps
   # 所有容器应该处于"Up"状态
   ```

2. 检查日志：
   ```bash
   docker logs -f ragflow-server
   # 寻找任何错误消息
   ```

3. 访问Web界面：
   在浏览器中访问 `http://<服务器IP>`，应该能看到RAGflow的登录界面

4. 检查API健康状态：
   ```bash
   curl http://<服务器IP>/api/v1/health
   # 应返回状态信息
   ```

### 5.2 日志分析与常见问题解决

常见问题及解决方案：

1. **Elasticsearch启动失败**
   - 症状：ES容器反复重启
   - 解决：检查vm.max_map_count设置和内存分配

2. **嵌入模型下载失败**
   - 症状：日志中显示无法下载模型
   - 解决：设置HF_ENDPOINT环境变量或使用VPN

3. **API密钥问题**
   - 症状：LLM调用失败
   - 解决：检查API密钥配置和网络连接

4. **存储空间不足**
   - 症状：系统报错无法写入文件
   - 解决：增加磁盘空间或清理旧数据

5. **性能问题**
   - 症状：系统响应缓慢
   - 解决：检查资源使用情况，考虑增加CPU/内存或开启GPU

查看日志的最佳实践：
```bash
# 查看最近的500行日志
docker logs --tail 500 ragflow-server

# 实时查看日志
docker logs -f ragflow-server

# 过滤错误日志
docker logs ragflow-server 2>&1 | grep -i error
```

### 5.3 系统升级方法

RAGflow定期发布新版本，升级步骤如下：

1. 备份数据（重要！）：
   ```bash
   # 备份MySQL数据
   docker exec ragflow-mysql mysqldump -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} > ragflow_backup.sql
   
   # 备份MinIO数据
   cp -r /path/to/data/minio /path/to/backup/minio
   ```

2. 更新代码库：
   ```bash
   cd ragflow
   git pull
   ```

3. 更新Docker镜像：
   ```bash
   docker pull infiniflow/ragflow:latest
   # 或指定版本
   docker pull infiniflow/ragflow:v0.17.2
   ```

4. 关闭旧服务：
   ```bash
   docker compose -f docker/docker-compose.yml down
   ```

5. 更新配置文件（如需要）

6. 启动新服务：
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```

7. 验证升级：
   - 检查版本信息
   - 测试基本功能
   - 检查数据完整性

## 总结

在本节课中，我们学习了RAGflow的部署和配置，包括系统架构、环境要求、部署方法和系统配置。掌握这些知识后，您应该能够成功部署一个可用的RAGflow环境，为后续的应用开发做好准备。

下一节课中，我们将深入探讨RAGflow的架构设计和核心原理，帮助大家理解RAG技术的内部工作机制。

## 练习

1. 尝试使用Docker部署RAGflow，并成功访问Web界面
2. 修改配置文件，将LLM更换为不同的提供商
3. 使用监控工具分析RAGflow的资源使用情况
4. 尝试从源代码构建和部署RAGflow（进阶） 