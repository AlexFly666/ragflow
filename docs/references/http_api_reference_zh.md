---
sidebar_position: 2
slug: /http_api_reference_zh
---

# HTTP API

RAGFlow 的完整 RESTful API 参考文档。在继续之前，请确保您已经[准备好了用于身份验证的 RAGFlow API 密钥](../guides/models/llm_api_key_setup.md)。

---

## 错误代码

---

| 代码 | 消息                 | 描述                |
|-----|---------------------|-------------------|
| 400 | Bad Request         | 无效的请求参数        |
| 401 | Unauthorized        | 未经授权的访问        |
| 403 | Forbidden           | 访问被拒绝           |
| 404 | Not Found          | 资源未找到           |
| 500 | Internal Server Error| 服务器内部错误       |
| 1001| Invalid Chunk ID   | 无效的数据块ID       |
| 1002| Chunk Update Failed | 数据块更新失败       |

---

## OpenAI 兼容 API

---

### 创建聊天完成

**POST** `/api/v1/chats_openai/{chat_id}/chat/completions`

为给定的聊天对话创建模型响应。

此 API 遵循与 OpenAI API 相同的请求和响应格式。它允许您以与 [OpenAI 的 API](https://platform.openai.com/docs/api-reference/chat/create) 类似的方式与模型进行交互。

#### 请求

- 方法: POST
- URL: `/api/v1/chats_openai/{chat_id}/chat/completions`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"model"`: `string`
  - `"messages"`: `object list`
  - `"stream"`: `boolean`

##### 请求示例

```bash
curl --request POST \
     --url http://{address}/api/v1/chats_openai/{chat_id}/chat/completions \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
        "model": "model",
        "messages": [{"role": "user", "content": "Say this is a test!"}],
        "stream": true
      }'
```

##### 请求参数

- `model` (*请求体参数*) `string`, *必需*  
  用于生成响应的模型。服务器将自动解析此参数，因此您现在可以将其设置为任何值。

- `messages` (*请求体参数*) `list[object]`, *必需*  
  用于生成响应的历史聊天消息列表。必须至少包含一条带有 `user` 角色的消息。

- `stream` (*请求体参数*) `boolean`  
  是否以流式方式接收响应。如果您更喜欢一次性接收整个响应而不是流式传输，请将此项明确设置为 `false`。 

#### 响应

流式响应:

```json
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "delta": {
                "content": "This is a test. If you have any specific questions or need information, feel",
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion.chunk",
    "system_fingerprint": "",
    "usage": null
}
// 省略重复信息
{"choices":[{"delta":{"content":" free to ask, and I will do my best to provide an answer based on","role":"assistant"}}]}
{"choices":[{"delta":{"content":" the knowledge I have. If your question is unrelated to the provided knowledge base,","role":"assistant"}}]}
{"choices":[{"delta":{"content":" I will let you know.","role":"assistant"}}]}
// 最后一个数据块
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "delta": {
                "content": null,
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion.chunk",
    "system_fingerprint": "",
    "usage": {
        "prompt_tokens": 18,
        "completion_tokens": 225,
        "total_tokens": 243
    }
}
```

非流式响应:

```json
{
    "choices":[
        {
            "finish_reason":"stop",
            "index":0,
            "logprobs":null,
            "message":{
                "content":"This is a test. If you have any specific questions or need information, feel free to ask, and I will do my best to provide an answer based on the knowledge I have. If your question is unrelated to the provided knowledge base, I will let you know.",
                "role":"assistant"
            }
        }
    ],
    "created":1740543499,
    "id":"chatcmpl-3a9c3572f29311efa69751e139332ced",
    "model":"model",
    "object":"chat.completion",
    "usage":{
        "completion_tokens":246,
        "completion_tokens_details":{
            "accepted_prediction_tokens":246,
            "reasoning_tokens":18,
            "rejected_prediction_tokens":0
        },
        "prompt_tokens":18,
        "total_tokens":264
    }
}
```

失败响应:

```json
{
  "code": 102,
  "message": "The last content of this conversation is not from user."
}
```

---

## 数据集管理

---

### 创建数据集

**POST** `/api/v1/datasets`

创建一个数据集。

#### 请求

- 方法: POST
- URL: `/api/v1/datasets`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"name"`: `string`
  - `"avatar"`: `string`
  - `"description"`: `string`
  - `"embedding_model"`: `string`
  - `"permission"`: `string`
  - `"chunk_method"`: `string`
  - `"parser_config"`: `object`

##### 请求示例

```bash
curl --request POST \
     --url http://{address}/api/v1/datasets \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
      "name": "test_1"
      }'
```

##### 请求参数

- `"name"`: (*请求体参数*), `string`, *必需*  
  要创建的数据集的唯一名称。必须符合以下要求：  
  - 允许的字符包括：
    - 英文字母 (a-z, A-Z)
    - 数字 (0-9)
    - "_" (下划线)
  - 必须以英文字母或下划线开头
  - 最大长度为 65,535 字符
  - 不区分大小写

- `"avatar"`: (*请求体参数*), `string`  
  头像的 Base64 编码。

- `"description"`: (*请求体参数*), `string`  
  要创建的数据集的简要描述。

- `"embedding_model"`: (*请求体参数*), `string`  
  要使用的嵌入模型的名称。例如：`"BAAI/bge-zh-v1.5"`

- `"permission"`: (*请求体参数*), `string`  
  指定谁可以访问要创建的数据集。可用选项：  
  - `"me"`: (默认) 只有您可以管理数据集
  - `"team"`: 所有团队成员都可以管理数据集

- `"chunk_method"`: (*请求体参数*), `enum<string>`  
  要创建的数据集的分块方法。可用选项：  
  - `"naive"`: 通用 (默认)
  - `"manual"`: 手动
  - `"qa"`: 问答
  - `"table"`: 表格
  - `"paper"`: 论文
  - `"book"`: 书籍
  - `"laws"`: 法律
  - `"presentation"`: 演示
  - `"picture"`: 图片
  - `"one"`: 单一
  - `"knowledge_graph"`: 知识图谱  
    在选择此项之前，请确保您已在**设置**页面正确配置了 LLM。另请注意，知识图谱会消耗大量 Token！
  - `"email"`: 邮件 

- `"parser_config"`: (*请求体参数*), `object`  
  数据集解析器的配置设置。此 JSON 对象中的属性根据所选的 `"chunk_method"` 而变化：  
  - 如果 `"chunk_method"` 为 `"naive"`，`"parser_config"` 对象包含以下属性：
    - `"chunk_token_count"`: 默认为 `128`
    - `"layout_recognize"`: 默认为 `true`
    - `"html4excel"`: 指示是否将 Excel 文档转换为 HTML 格式。默认为 `false`
    - `"delimiter"`: 默认为 `"\n!?。；！？"`
    - `"task_page_size"`: 默认为 `12`。仅适用于 PDF
    - `"raptor"`: Raptor 特定设置。默认为：`{"use_raptor": false}`
  - 如果 `"chunk_method"` 为 `"qa"`、`"manuel"`、`"paper"`、`"book"`、`"laws"` 或 `"presentation"`，`"parser_config"` 对象包含以下属性：  
    - `"raptor"`: Raptor 特定设置。默认为：`{"use_raptor": false}`
  - 如果 `"chunk_method"` 为 `"table"`、`"picture"`、`"one"` 或 `"email"`，`"parser_config"` 为空 JSON 对象
  - 如果 `"chunk_method"` 为 `"knowledge_graph"`，`"parser_config"` 对象包含以下属性：  
    - `"chunk_token_count"`: 默认为 `128`
    - `"delimiter"`: 默认为 `"\n!?。；！？"`
    - `"entity_types"`: 默认为 `["organization","person","location","event","time"]`

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": {
        "avatar": null,
        "chunk_count": 0,
        "chunk_method": "naive",
        "create_date": "Thu, 24 Oct 2024 09:14:07 GMT",
        "create_time": 1729761247434,
        "created_by": "69736c5e723611efb51b0242ac120007",
        "description": null,
        "document_count": 0,
        "embedding_model": "BAAI/bge-large-zh-v1.5",
        "id": "527fa74891e811ef9c650242ac120006",
        "language": "English",
        "name": "test_1",
        "parser_config": {
            "chunk_token_num": 128,
            "delimiter": "\\n!?;。；！？",
            "html4excel": false,
            "layout_recognize": true,
            "raptor": {
                "user_raptor": false
            }
        },
        "permission": "me",
        "similarity_threshold": 0.2,
        "status": "1",
        "tenant_id": "69736c5e723611efb51b0242ac120007",
        "token_num": 0,
        "update_date": "Thu, 24 Oct 2024 09:14:07 GMT",
        "update_time": 1729761247434,
        "vector_similarity_weight": 0.3
    }
}
```

失败响应:

```json
{
    "code": 102,
    "message": "Duplicated knowledgebase name in creating dataset."
}
```

---

### 删除数据集

**DELETE** `/api/v1/datasets`

通过 ID 删除数据集。

#### 请求

- 方法: DELETE
- URL: `/api/v1/datasets`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"ids"`: `list[string]`

##### 请求示例

```bash
curl --request DELETE \
     --url http://{address}/api/v1/datasets \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '{
     "ids": ["test_1", "test_2"]
     }'
```

##### 请求参数

- `"ids"`: (*请求体参数*), `list[string]`  
  要删除的数据集的 ID。如果未指定，将删除所有数据集。

#### 响应

成功响应:

```json
{
    "code": 0 
}
```

失败响应:

```json
{
    "code": 102,
    "message": "You don't own the dataset."
}
```

---

### 更新数据集

**PUT** `/api/v1/datasets/{dataset_id}`

更新指定数据集的配置。

#### 请求

- 方法: PUT
- URL: `/api/v1/datasets/{dataset_id}`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"name"`: `string`
  - `"embedding_model"`: `string`
  - `"chunk_method"`: `enum<string>`

##### 请求示例

```bash
curl --request PUT \
     --url http://{address}/api/v1/datasets/{dataset_id} \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "name": "updated_dataset"
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  要更新的数据集的 ID。
- `"name"`: (*请求体参数*), `string`  
  数据集的修改后的名称。
- `"embedding_model"`: (*请求体参数*), `string`  
  更新后的嵌入模型名称。  
  - 在更新 `"embedding_model"` 之前，请确保 `"chunk_count"` 为 `0`。
- `"chunk_method"`: (*请求体参数*), `enum<string>`  
  数据集的分块方法。可用选项：  
  - `"naive"`: 通用
  - `"manual`: 手动
  - `"qa"`: 问答
  - `"table"`: 表格
  - `"paper"`: 论文
  - `"book"`: 书籍
  - `"laws"`: 法律
  - `"presentation"`: 演示
  - `"picture"`: 图片
  - `"one"`: 单一
  - `"email"`: 邮件
  - `"knowledge_graph"`: 知识图谱  
    在选择此项之前，请确保您已在**设置**页面正确配置了 LLM。另请注意，知识图谱会消耗大量 Token！

#### 响应

成功响应:

```json
{
    "code": 0 
}
```

失败响应:

```json
{
    "code": 102,
    "message": "Can't change tenant_id."
}
```

---

### 列出数据集

**GET** `/api/v1/datasets?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={dataset_name}&id={dataset_id}`

列出数据集。

#### 请求

- 方法: GET
- URL: `/api/v1/datasets?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={dataset_name}&id={dataset_id}`
- 请求头:
  - `'Authorization: Bearer <YOUR_API_KEY>'`

##### 请求示例

```bash
curl --request GET \
     --url http://{address}/api/v1/datasets?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&name={dataset_name}&id={dataset_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

##### 请求参数

- `page`: (*过滤参数*)  
  指定显示数据集的页码。默认为 `1`。
- `page_size`: (*过滤参数*)  
  每页显示的数据集数量。默认为 `30`。
- `orderby`: (*过滤参数*)  
  数据集排序的字段。可用选项：
  - `create_time` (默认)
  - `update_time`
- `desc`: (*过滤参数*)  
  指示检索的数据集是否应按降序排序。默认为 `true`。
- `name`: (*过滤参数*)  
  要检索的数据集的名称。
- `id`: (*过滤参数*)  
  要检索的数据集的 ID。 

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": [
        {
            "avatar": "",
            "chunk_count": 59,
            "create_date": "Sat, 14 Sep 2024 01:12:37 GMT",
            "create_time": 1726276357324,
            "created_by": "69736c5e723611efb51b0242ac120007",
            "description": null,
            "document_count": 1,
            "embedding_model": "BAAI/bge-large-zh-v1.5",
            "id": "6e211ee0723611efa10a0242ac120007",
            "language": "English",
            "name": "mysql",
            "chunk_method": "knowledge_graph",
            "parser_config": {
                "chunk_token_num": 8192,
                "delimiter": "\\n!?;。；！？",
                "entity_types": [
                    "organization",
                    "person",
                    "location",
                    "event",
                    "time"
                ]
            },
            "permission": "me",
            "similarity_threshold": 0.2,
            "status": "1",
            "tenant_id": "69736c5e723611efb51b0242ac120007",
            "token_num": 12744,
            "update_date": "Thu, 10 Oct 2024 04:07:23 GMT",
            "update_time": 1728533243536,
            "vector_similarity_weight": 0.3
        }
    ]
}
```

失败响应:

```json
{
    "code": 102,
    "message": "The dataset doesn't exist"
}
```

---

## 数据集内文件管理

---

### 上传文档

**POST** `/api/v1/datasets/{dataset_id}/documents`

向指定数据集上传文档。

#### 请求

- 方法: POST
- URL: `/api/v1/datasets/{dataset_id}/documents`
- 请求头:
  - `'Content-Type: multipart/form-data'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 表单:
  - `'file=@{FILE_PATH}'`

##### 请求示例

```bash
curl --request POST \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents \
     --header 'Content-Type: multipart/form-data' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --form 'file=@./test1.txt' \
     --form 'file=@./test2.pdf'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  要上传文档的数据集的 ID。
- `'file'`: (*请求体参数*)  
  要上传的文档。

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": [
        {
            "chunk_method": "naive",
            "created_by": "69736c5e723611efb51b0242ac120007",
            "dataset_id": "527fa74891e811ef9c650242ac120006",
            "id": "b330ec2e91ec11efbc510242ac120004",
            "location": "1.txt",
            "name": "1.txt",
            "parser_config": {
                "chunk_token_num": 128,
                "delimiter": "\\n!?;。；！？",
                "html4excel": false,
                "layout_recognize": true,
                "raptor": {
                    "user_raptor": false
                }
            },
            "run": "UNSTART",
            "size": 17966,
            "thumbnail": "",
            "type": "doc"
        }
    ]
}
```

失败响应:

```json
{
    "code": 101,
    "message": "No file part!"
}
```

---

### 更新文档

**PUT** `/api/v1/datasets/{dataset_id}/documents/{document_id}`

更新指定文档的配置。

#### 请求

- 方法: PUT
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"name"`: `string`
  - `"meta_fields"`: `object`
  - `"chunk_method"`: `string`
  - `"parser_config"`: `object`

##### 请求示例

```bash
curl --request PUT \
     --url http://{address}/api/v1/datasets/{dataset_id}/info/{document_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --header 'Content-Type: application/json' \
     --data '
     {
          "name": "manual.txt", 
          "chunk_method": "manual", 
          "parser_config": {"chunk_token_count": 128}
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `document_id`: (*路径参数*)  
  要更新的文档的 ID。
- `"name"`: (*请求体参数*), `string`
- `"meta_fields"`: (*请求体参数*), `dict[str, Any]` 文档的元字段。
- `"chunk_method"`: (*请求体参数*), `string`  
  要应用于文档的解析方法：  
  - `"naive"`: 通用
  - `"manual`: 手动
  - `"qa"`: 问答
  - `"table"`: 表格
  - `"paper"`: 论文
  - `"book"`: 书籍
  - `"laws"`: 法律
  - `"presentation"`: 演示
  - `"picture"`: 图片
  - `"one"`: 单一
  - `"email"`: 邮件
- `"parser_config"`: (*请求体参数*), `object`  
  数据集解析器的配置设置。此 JSON 对象中的属性根据所选的 `"chunk_method"` 而变化：  
  - 如果 `"chunk_method"` 为 `"naive"`，`"parser_config"` 对象包含以下属性：
    - `"chunk_token_count"`: 默认为 `128`
    - `"layout_recognize"`: 默认为 `true`
    - `"html4excel"`: 指示是否将 Excel 文档转换为 HTML 格式。默认为 `false`
    - `"delimiter"`: 默认为 `"\n!?。；！？"`
    - `"task_page_size"`: 默认为 `12`。仅适用于 PDF
    - `"raptor"`: Raptor 特定设置。默认为：`{"use_raptor": false}`
  - 如果 `"chunk_method"` 为 `"qa"`、`"manuel"`、`"paper"`、`"book"`、`"laws"` 或 `"presentation"`，`"parser_config"` 对象包含以下属性：
    - `"raptor"`: Raptor 特定设置。默认为：`{"use_raptor": false}`
  - 如果 `"chunk_method"` 为 `"table"`、`"picture"`、`"one"` 或 `"email"`，`"parser_config"` 为空 JSON 对象
  - 如果 `"chunk_method"` 为 `"knowledge_graph"`，`"parser_config"` 对象包含以下属性：
    - `"chunk_token_count"`: 默认为 `128`
    - `"delimiter"`: 默认为 `"\n!?。；！？"`
    - `"entity_types"`: 默认为 `["organization","person","location","event","time"]` 

#### 响应

成功响应:

```json
{
    "code": 0
}
```

失败响应:

```json
{
    "code": 102,
    "message": "The dataset does not have the document."
}
```

---

### 下载文档

**GET** `/api/v1/datasets/{dataset_id}/documents/{document_id}`

从指定数据集下载文档。

#### 请求

- 方法: GET
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}`
- 请求头:
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 输出:
  - `'{PATH_TO_THE_FILE}'`

##### 请求示例

```bash
curl --request GET \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --output ./ragflow.txt
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `documents_id`: (*路径参数*)  
  要下载的文档的 ID。

#### 响应

成功响应:

```json
This is a test to verify the file download feature.
```

失败响应:

```json
{
    "code": 102,
    "message": "You do not own the dataset 7898da028a0511efbf750242ac1220005."
}
```

---

### 列出文档

**GET** `/api/v1/datasets/{dataset_id}/documents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&keywords={keywords}&id={document_id}&name={document_name}`

列出指定数据集中的文档。

#### 请求

- 方法: GET
- URL: `/api/v1/datasets/{dataset_id}/documents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&keywords={keywords}&id={document_id}&name={document_name}`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`

##### 请求示例

```bash
curl --request GET \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}&keywords={keywords}&id={document_id}&name={document_name} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `keywords`: (*过滤参数*), `string`  
  用于匹配文档标题的关键词。
- `page`: (*过滤参数*), `integer`
  指定显示文档的页码。默认为 `1`。
- `page_size`: (*过滤参数*), `integer`  
  每页显示的最大文档数量。默认为 `30`。
- `orderby`: (*过滤参数*), `string`  
  文档排序的字段。可用选项：
  - `create_time` (默认)
  - `update_time`
- `desc`: (*过滤参数*), `boolean`  
  指示检索的文档是否应按降序排序。默认为 `true`。
- `id`: (*过滤参数*), `string`  
  要检索的文档的 ID。

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": {
        "docs": [
            {
                "chunk_count": 0,
                "create_date": "Mon, 14 Oct 2024 09:11:01 GMT",
                "create_time": 1728897061948,
                "created_by": "69736c5e723611efb51b0242ac120007",
                "id": "3bcfbf8a8a0c11ef8aba0242ac120006",
                "knowledgebase_id": "7898da028a0511efbf750242ac120005",
                "location": "Test_2.txt",
                "name": "Test_2.txt",
                "parser_config": {
                    "chunk_token_count": 128,
                    "delimiter": "\n!?。；！？",
                    "layout_recognize": true,
                    "task_page_size": 12
                },
                "chunk_method": "naive",
                "process_begin_at": null,
                "process_duation": 0.0,
                "progress": 0.0,
                "progress_msg": "",
                "run": "0",
                "size": 7,
                "source_type": "local",
                "status": "1",
                "thumbnail": null,
                "token_count": 0,
                "type": "doc",
                "update_date": "Mon, 14 Oct 2024 09:11:01 GMT",
                "update_time": 1728897061948
            }
        ],
        "total": 1
    }
}
```

失败响应:

```json
{
    "code": 102,
    "message": "You don't own the dataset 7898da028a0511efbf750242ac1220005. "
}
```

---

### 删除文档

**DELETE** `/api/v1/datasets/{dataset_id}/documents`

通过 ID 删除文档。

#### 请求

- 方法: DELETE
- URL: `/api/v1/datasets/{dataset_id}/documents`
- 请求头:
  - `'Content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"ids"`: `list[string]`

##### 请求示例

```bash
curl --request DELETE \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "ids": ["id_1","id_2"]
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `"ids"`: (*请求体参数*), `list[string]`  
  要删除的文档的 ID。如果未指定，将删除指定数据集中的所有文档。

#### 响应

成功响应:

```json
{
    "code": 0
}
```

失败响应:

```json
{
    "code": 102,
    "message": "You do not own the dataset 7898da028a0511efbf750242ac1220005."
}
```

---

### 解析文档

**POST** `/api/v1/datasets/{dataset_id}/chunks`

解析指定数据集中的文档。

#### 请求

- 方法: POST
- URL: `/api/v1/datasets/{dataset_id}/chunks`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"document_ids"`: `list[string]`

##### 请求示例

```bash
curl --request POST \
     --url http://{address}/api/v1/datasets/{dataset_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "document_ids": ["97a5f1c2759811efaa500242ac120004","97ad64b6759811ef9fc30242ac120004"]
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  数据集 ID。
- `"document_ids"`: (*请求体参数*), `list[string]`, *必需*  
  要解析的文档的 ID。

#### 响应

成功响应:

```json
{
    "code": 0
}
```

失败响应:

```json
{
    "code": 102,
    "message": "`document_ids` is required"
}
```

---

### 停止解析文档

**DELETE** `/api/v1/datasets/{dataset_id}/chunks`

停止解析指定文档。

#### 请求

- 方法: DELETE
- URL: `/api/v1/datasets/{dataset_id}/chunks`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"document_ids"`: `list[string]`

##### 请求示例

```bash
curl --request DELETE \
     --url http://{address}/api/v1/datasets/{dataset_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "document_ids": ["97a5f1c2759811efaa500242ac120004","97ad64b6759811ef9fc30242ac120004"]
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `"document_ids"`: (*请求体参数*), `list[string]`, *必需*  
  要停止解析的文档的 ID。

#### 响应

成功响应:

```json
{
    "code": 0
}
```

失败响应:

```json
{
    "code": 102,
    "message": "`document_ids` is required"
}
```

---

## 数据块管理

---

### 添加数据块

**POST** `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks`

向指定数据集中的指定文档添加数据块。

#### 请求

- 方法: POST
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"content"`: `string`
  - `"important_keywords"`: `list[string]`

##### 请求示例

```bash
curl --request POST \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "content": "<CHUNK_CONTENT_HERE>"
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `document_ids`: (*路径参数*)  
  关联的文档 ID。
- `"content"`: (*请求体参数*), `string`, *必需*  
  数据块的文本内容。
- `"important_keywords"`: (*请求体参数*), `list[string]`  
  要与数据块标记的关键词或短语。
- `"questions"`: (*请求体参数*), `list[string]`
  如果有给定问题，嵌入的数据块将基于这些问题生成。

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": {
        "chunk": {
            "content": "who are you",
            "create_time": "2024-12-30 16:59:55",
            "create_timestamp": 1735549195.969164,
            "dataset_id": "72f36e1ebdf411efb7250242ac120006",
            "document_id": "61d68474be0111ef98dd0242ac120006",
            "id": "12ccdc56e59837e5",
            "important_keywords": [],
            "questions": []
        }
    }
}
```

失败响应:

```json
{
    "code": 102,
    "message": "`content` is required"
}
```

---

### 列出数据块

**GET** `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks?keywords={keywords}&page={page}&page_size={page_size}&id={id}`

列出指定文档中的数据块。

#### 请求

- 方法: GET
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks?keywords={keywords}&page={page}&page_size={page_size}&id={chunk_id}`
- 请求头:
  - `'Authorization: Bearer <YOUR_API_KEY>'`

##### 请求示例

```bash
curl --request GET \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks?keywords={keywords}&page={page}&page_size={page_size}&id={chunk_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>' 
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `document_id`: (*路径参数*)  
  关联的文档 ID。
- `keywords`: (*过滤参数*), `string`  
  用于匹配数据块内容的关键词。
- `page`: (*过滤参数*), `integer`  
  指定显示数据块的页码。默认为 `1`。
- `page_size`: (*过滤参数*), `integer`  
  每页显示的最大数据块数量。默认为 `1024`。
- `id`: (*过滤参数*), `string`  
  要检索的数据块的 ID。

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": {
        "chunks": [
            {
                "available_int": 1,
                "content": "This is a test content.",
                "docnm_kwd": "1.txt",
                "document_id": "b330ec2e91ec11efbc510242ac120004",
                "id": "b48c170e90f70af998485c1065490726",
                "image_id": "",
                "important_keywords": "",
                "positions": [
                    ""
                ]
            }
        ],
        "doc": {
            "chunk_count": 1,
            "chunk_method": "naive",
            "create_date": "Thu, 24 Oct 2024 09:45:27 GMT",
            "create_time": 1729763127646,
            "created_by": "69736c5e723611efb51b0242ac120007",
            "dataset_id": "527fa74891e811ef9c650242ac120006",
            "id": "b330ec2e91ec11efbc510242ac120004",
            "location": "1.txt",
            "name": "1.txt",
            "parser_config": {
                "chunk_token_num": 128,
                "delimiter": "\\n!?;。；！？",
                "html4excel": false,
                "layout_recognize": true,
                "raptor": {
                    "user_raptor": false
                }
            },
            "process_begin_at": "Thu, 24 Oct 2024 09:56:44 GMT",
            "process_duation": 0.54213,
            "progress": 0.0,
            "progress_msg": "Task dispatched...",
            "run": "2",
            "size": 17966,
            "source_type": "local",
            "status": "1",
            "thumbnail": "",
            "token_count": 8,
            "type": "doc",
            "update_date": "Thu, 24 Oct 2024 11:03:15 GMT",
            "update_time": 1729767795721
        },
        "total": 1
    }
}
```

失败响应:

```json
{
    "code": 102,
    "message": "You don't own the document 5c5999ec7be811ef9cab0242ac12000e5."
}
```

---

### 删除数据块

**DELETE** `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks`

通过 ID 删除数据块。

#### 请求

- 方法: DELETE
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"chunk_ids"`: `list[string]`

##### 请求示例

```bash
curl --request DELETE \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "chunk_ids": ["test_1", "test_2"]
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `document_ids`: (*路径参数*)  
  关联的文档 ID。
- `"chunk_ids"`: (*请求体参数*), `list[string]`  
  要删除的数据块的 ID。如果未指定，将删除指定文档的所有数据块。

#### 响应

成功响应:

```json
{
    "code": 0
}
```

失败响应:

```json
{
    "code": 102,
    "message": "`chunk_ids` is required"
}
```

---

### 更新数据块

**PUT** `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}`

更新指定数据块的内容或配置。

#### 请求

- 方法: PUT
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"content"`: `string`
  - `"important_keywords"`: `list[string]`
  - `"available"`: `boolean`

##### 请求示例

```bash
curl --request PUT \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id} \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {   
          "content": "ragflow123",  
          "important_keywords": []  
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `document_ids`: (*路径参数*)  
  关联的文档 ID。
- `chunk_id`: (*路径参数*)  
  要更新的数据块的 ID。
- `"content"`: (*请求体参数*), `string`  
  数据块的文本内容。
- `"important_keywords"`: (*请求体参数*), `list[string]`  
  要与数据块标记的关键词或短语列表。
- `"available"`: (*请求体参数*) `boolean`  
  数据块在数据集中的可用状态。可选值：  
  - `true`: 可用（默认）
  - `false`: 不可用

#### 响应

成功响应:

```json
{
    "code": 0
}
```

失败响应:

```json
{
    "code": 102,
    "message": "Can't find this chunk 29a2d9987e16ba331fb4d7d30d99b71d2"
}
```

---

### 获取数据块

**GET** `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}`

获取指定数据块的详细信息。

#### 请求

- 方法: GET
- URL: `/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id}`
- 请求头:
  - `'Authorization: Bearer <YOUR_API_KEY>'`

##### 请求示例

```bash
curl --request GET \
     --url http://{address}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks/{chunk_id} \
     --header 'Authorization: Bearer <YOUR_API_KEY>'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  关联的数据集 ID。
- `document_id`: (*路径参数*)  
  关联的文档 ID。
- `chunk_id`: (*路径参数*)  
  要获取的数据块的 ID。

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": {
        "chunk": {
            "content": "who are you",
            "create_time": "2024-12-30 16:59:55",
            "create_timestamp": 1735549195.969164,
            "dataset_id": "72f36e1ebdf411efb7250242ac120006",
            "document_id": "61d68474be0111ef98dd0242ac120006",
            "id": "12ccdc56e59837e5",
            "important_keywords": [],
            "questions": []
        }
    }
}
```

失败响应:

```json
{
    "code": 102,
    "message": "Can't find this chunk 29a2d9987e16ba331fb4d7d30d99b71d2"
}
```

---

### 搜索数据块

**POST** `/api/v1/datasets/{dataset_id}/search`

在指定数据集中搜索相关数据块。

#### 请求

- 方法: POST
- URL: `/api/v1/datasets/{dataset_id}/search`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
- 请求体:
  - `"query"`: `string`
  - `"top_k"`: `integer`
  - `"reranking"`: `boolean`
  - `"document_ids"`: `list[string]`
  - `"filter"`: `object`

##### 请求示例

```bash
curl --request POST \
     --url http://{address}/api/v1/datasets/{dataset_id}/search \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --data '
     {
          "query": "what is ragflow",
          "top_k": 2,
          "reranking": true,
          "document_ids": ["97a5f1c2759811efaa500242ac120004"]
     }'
```

##### 请求参数

- `dataset_id`: (*路径参数*)  
  要搜索的数据集的 ID。
- `"query"`: (*请求体参数*), `string`  
  搜索查询文本。
- `"top_k"`: (*请求体参数*), `integer`  
  要返回的最相关数据块的数量。默认为 `2`。
- `"reranking"`: (*请求体参数*), `boolean`  
  是否对搜索结果进行重新排序。默认为 `true`。
- `"document_ids"`: (*请求体参数*), `list[string]`  
  限制搜索范围的文档 ID 列表。如果未指定，将搜索整个数据集。
- `"filter"`: (*请求体参数*), `object`  
  用于过滤搜索结果的条件。可选字段：
  - `"metadata"`: `object`  
    基于元数据字段过滤。
  - `"source"`: `string`  
    基于来源过滤。
  - `"date_from"`: `string`  
    基于创建日期过滤（开始日期）。
  - `"date_to"`: `string`  
    基于创建日期过滤（结束日期）。

#### 响应

成功响应:

```json
{
    "code": 0,
    "data": {
        "documents": [
            {
                "chunk": {
                    "content": "RAGFlow 是一个基于 RAG（检索增强生成）技术的开源框架，它提供了一套完整的工具和接口，用于构建和部署基于大语言模型的应用。",
                    "create_time": "2024-12-30 16:59:55",
                    "create_timestamp": 1735549195.969164,
                    "dataset_id": "72f36e1ebdf411efb7250242ac120006",
                    "document_id": "61d68474be0111ef98dd0242ac120006",
                    "id": "12ccdc56e59837e5",
                    "important_keywords": ["RAG", "框架", "LLM"],
                    "questions": [],
                    "score": 0.92
                }
            }
        ]
    }
}
```

失败响应:

```json
{
    "code": 102,
    "message": "Invalid dataset ID"
}
```

---

### 聊天

**POST** `/api/v1/chat`

与 RAGFlow 进行对话。

#### 请求

- 方法: POST
- URL: `/api/v1/chat`
- 请求头:
  - `'content-Type: application/json'`
  - `'Authorization: Bearer <YOUR_API_KEY>'`
  - `'Accept: text/event-stream'` (用于流式响应)
- 请求体:
  - `"messages"`: `list[object]`
  - `"dataset_ids"`: `list[string]`
  - `"document_ids"`: `list[string]`
  - `"stream"`: `boolean`
  - `"model"`: `string`
  - `"temperature"`: `float`
  - `"top_p"`: `float`
  - `"max_tokens"`: `integer`
  - `"presence_penalty"`: `float`
  - `"frequency_penalty"`: `float`
  - `"logit_bias"`: `object`
  - `"user"`: `string`
  - `"stop"`: `list[string]`
  - `"functions"`: `list[object]`
  - `"function_call"`: `string`
  - `"tools"`: `list[object]`
  - `"tool_choice"`: `string`
  - `"response_format"`: `object`
  - `"seed"`: `integer`

##### 请求示例

```bash
curl --request POST \
     --url http://{address}/api/v1/chat \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer <YOUR_API_KEY>' \
     --header 'Accept: text/event-stream' \
     --data '
     {
          "messages": [
              {
                  "role": "user",
                  "content": "what is ragflow"
              }
          ],
          "dataset_ids": ["72f36e1ebdf411efb7250242ac120006"],
          "stream": true,
          "model": "gpt-3.5-turbo"
     }'
```

##### 请求参数

- `"messages"`: (*请求体参数*), `list[object]`  
  对话消息列表。每个消息对象包含：
  - `"role"`: `string`  
    消息发送者的角色。可选值：`"system"`、`"user"`、`"assistant"`、`"function"`、`"tool"`。
  - `"content"`: `string`  
    消息内容。
  - `"name"`: `string`  
    当 `"role"` 为 `"function"` 或 `"tool"` 时的名称。
  - `"function_call"`: `object`  
    当消息调用函数时的详细信息。
  - `"tool_calls"`: `list[object]`  
    当消息调用工具时的详细信息。
- `"dataset_ids"`: (*请求体参数*), `list[string]`  
  要搜索的数据集 ID 列表。
- `"document_ids"`: (*请求体参数*), `list[string]`  
  限制搜索范围的文档 ID 列表。
- `"stream"`: (*请求体参数*), `boolean`  
  是否使用流式响应。默认为 `false`。
- `"model"`: (*请求体参数*), `string`  
  要使用的语言模型。默认为 `"gpt-3.5-turbo"`。
- `"temperature"`: (*请求体参数*), `float`  
  采样温度，控制输出的随机性。范围 0-2，默认为 `1`。
- `"top_p"`: (*请求体参数*), `float`  
  核采样阈值。范围 0-1，默认为 `1`。
- `"max_tokens"`: (*请求体参数*), `integer`  
  生成的最大令牌数。默认为 `None`。
- `"presence_penalty"`: (*请求体参数*), `float`  
  存在惩罚系数。范围 -2.0 到 2.0，默认为 `0`。
- `"frequency_penalty"`: (*请求体参数*), `float`  
  频率惩罚系数。范围 -2.0 到 2.0，默认为 `0`。
- `"logit_bias"`: (*请求体参数*), `object`  
  令牌的对数偏差映射。默认为 `None`。
- `"user"`: (*请求体参数*), `string`  
  最终用户的唯一标识符。
- `"stop"`: (*请求体参数*), `list[string]`  
  生成停止序列。默认为 `None`。
- `"functions"`: (*请求体参数*), `list[object]`  
  可用函数列表。每个函数对象包含：
  - `"name"`: `string`  
    函数名称。
  - `"description"`: `string`  
    函数描述。
  - `"parameters"`: `object`  
    函数参数的 JSON Schema。
- `"function_call"`: (*请求体参数*), `string`  
  强制函数调用。可选值：`"none"`、`"auto"`、`{"name": "<name>"}`。
- `"tools"`: (*请求体参数*), `list[object]`  
  可用工具列表。每个工具对象包含：
  - `"type"`: `string`  
    工具类型。
  - `"function"`: `object`  
    工具函数定义。
- `"tool_choice"`: (*请求体参数*), `string`  
  强制工具选择。可选值：`"none"`、`"auto"`、`{"type": "function", "function": {"name": "<name>"}}`。
- `"response_format"`: (*请求体参数*), `object`  
  响应格式设置。可选字段：
  - `"type"`: `string`  
    响应类型。可选值：`"text"`、`"json_object"`。
- `"seed"`: (*请求体参数*), `integer`  
  随机数生成种子。默认为 `None`。

#### 响应

流式响应:

```json
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "delta": {
                "content": "RAGFlow 是一个基于 RAG（检索增强生成）技术的开源框架，它提供了一套完整的工具和接口，用于构建和部署基于大语言模型的应用。",
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion.chunk",
    "system_fingerprint": "",
    "usage": null
}
// 省略重复信息
{"choices":[{"delta":{"content":"RAGFlow 的主要特点包括：","role":"assistant"}}]}
{"choices":[{"delta":{"content":"1. 简单易用的 API 接口","role":"assistant"}}]}
{"choices":[{"delta":{"content":"2. 灵活的文档处理和向量化能力","role":"assistant"}}]}
{"choices":[{"delta":{"content":"3. 支持多种大语言模型和向量数据库","role":"assistant"}}]}
{"choices":[{"delta":{"content":"4. 内置的文档解析和搜索功能","role":"assistant"}}]}
{"choices":[{"delta":{"content":"5. 可扩展的架构设计","role":"assistant"}}]}
{"choices":[{"delta":{},"finish_reason":"stop"}]}
```

非流式响应:

```json
{
    "id": "chatcmpl-3a9c3572f29311efa69751e139332ced",
    "choices": [
        {
            "message": {
                "content": "RAGFlow 是一个基于 RAG（检索增强生成）技术的开源框架，它提供了一套完整的工具和接口，用于构建和部署基于大语言模型的应用。\n\nRAGFlow 的主要特点包括：\n1. 简单易用的 API 接口\n2. 灵活的文档处理和向量化能力\n3. 支持多种大语言模型和向量数据库\n4. 内置的文档解析和搜索功能\n5. 可扩展的架构设计",
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1740543996,
    "model": "model",
    "object": "chat.completion",
    "system_fingerprint": "",
    "usage": {
        "completion_tokens": 123,
        "prompt_tokens": 456,
        "total_tokens": 579
    }
}
```

失败响应:

```json
{
    "code": 102,
    "message": "Invalid dataset ID"
}
```