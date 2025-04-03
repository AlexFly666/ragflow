---
sidebar_position: 2
slug: /launch_ragflow_from_source_zh
---

# 从源码启动服务

本指南介绍如何从源码设置 RAGFlow 服务。通过遵循本指南，你将能够使用源码进行调试。

## 目标受众

已添加新功能或修改现有代码，并希望使用源码进行调试的开发者，前提是其机器已设置好目标部署环境。

## 前置条件

- CPU ≥ 4核
- 内存 ≥ 16 GB
- 磁盘 ≥ 50 GB
- Docker ≥ 24.0.0 和 Docker Compose ≥ v2.26.1

:::tip 注意
如果你还没有在本地机器（Windows、Mac 或 Linux）上安装 Docker，请参阅 [安装 Docker Engine](https://docs.docker.com/engine/install/) 指南。
:::

## 从源码启动服务

要从源码启动 RAGFlow 服务，请按以下步骤操作：

### 克隆 RAGFlow 仓库

```bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
```

### 安装 Python 依赖

1. 安装 uv：
   
   ```bash
   pipx install uv
   ```

2. 安装 Python 依赖：
   - 精简版：
   ```bash
   uv sync --python 3.10 # 安装 RAGFlow 依赖的 Python 模块
   ```
   - 完整版：
   ```bash
   uv sync --python 3.10 --all-extras # 安装 RAGFlow 依赖的 Python 模块
   ```
   *将创建一个名为 `.venv` 的虚拟环境，所有 Python 依赖都将安装到这个新环境中。*

### 启动第三方服务

以下命令使用 Docker Compose 启动"基础"服务（MinIO、Elasticsearch、Redis 和 MySQL）：

```bash
docker compose -f docker/docker-compose-base.yml up -d
```

### 更新第三方服务的 `host` 和 `port` 设置

1. 在 `/etc/hosts` 中添加以下行，将 **docker/service_conf.yaml.template** 中指定的所有主机解析到 `127.0.0.1`：

   ```
   127.0.0.1       es01 infinity mysql minio redis
   ```

2. 在 **docker/service_conf.yaml.template** 中，将 mysql 端口更新为 `5455`，es 端口更新为 `1200`，如 **docker/.env** 中指定。

### 启动 RAGFlow 后端服务

1. 在 **docker/entrypoint.sh** 中注释掉 `nginx` 行：

   ```
   # /usr/sbin/nginx
   ```

2. 激活 Python 虚拟环境：

   ```bash
   source .venv/bin/activate
   export PYTHONPATH=$(pwd)
   ```

3. **可选：** 如果你无法访问 HuggingFace，设置 HF_ENDPOINT 环境变量以使用镜像站点：
 
   ```bash
   export HF_ENDPOINT=https://hf-mirror.com
   ```

4. 检查 **conf/service_conf.yaml** 中的配置，确保所有主机和端口设置正确。
   
5. 运行 **entrypoint.sh** 脚本启动后端服务：

   ```shell
   JEMALLOC_PATH=$(pkg-config --variable=libdir jemalloc)/libjemalloc.so;
   LD_PRELOAD=$JEMALLOC_PATH python rag/svr/task_executor.py 1;
   ```
   ```shell
   python api/ragflow_server.py;
   ```

### 启动 RAGFlow 前端服务

1. 导航到 `web` 目录并安装前端依赖：

   ```bash
   cd web
   npm install
   ```

2. 在 **.umirc.ts** 中将 `proxy.target` 更新为 `http://127.0.0.1:9380`：

   ```bash
   vim .umirc.ts
   ```

3. 启动 RAGFlow 前端服务：

   ```bash
   npm run dev 
   ```

   *将显示以下消息，显示你的前端服务的 IP 地址和端口号：*  

   ![](https://github.com/user-attachments/assets/0daf462c-a24d-4496-a66f-92533534e187)

### 访问 RAGFlow 服务

在 Web 浏览器中输入 `http://127.0.0.1:<PORT>/`，确保端口号与上图所示的端口号匹配。

### 开发完成后停止 RAGFlow 服务

1. 停止 RAGFlow 前端服务：
   ```bash
   pkill npm
   ```

2. 停止 RAGFlow 后端服务：
   ```bash
   pkill -f "docker/entrypoint.sh"
   ``` 