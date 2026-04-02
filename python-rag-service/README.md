# rag-python-service

这是原 `rag-springboot` 项目的纯 Python 重写版，放在独立目录中，不修改任何 Java 代码。

## 功能对齐

- `POST /api/rag/upload` 上传并解析文档，切块后写入向量库
- `POST /api/rag/ask` 基于检索上下文执行 RAG 问答
- `GET /api/rag/search` 返回相似文档块，不生成回答
- `GET /api/rag/health` 返回服务和知识库状态
- `GET /api/test/simple` / `GET /api/test/detailed` 测试 Qwen 调用
- `GET /api/test/health` 检查 DashScope 配置状态
- `GET /api/test/page` 返回测试 HTML 页面

## 技术栈

- FastAPI
- DashScope Python SDK
- pymilvus
- 本地 JSON 向量存储回退
- pypdf / python-docx / openpyxl / python-pptx / BeautifulSoup

## 目录

```text
python-rag-service/
  app/
    api/
    core/
    models/
    services/
  tests/
  data/
```

## 快速启动

```bash
cd /Users/tyler/Project/rag-springboot/python-rag-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 配置说明

- `DASHSCOPE_API_KEY`: 通义千问调用凭证
- `VECTOR_BACKEND`: `auto` / `milvus` / `local`
- `LOCAL_VECTOR_STORE_PATH`: 本地回退存储路径
- `MILVUS_*`: Milvus 连接和集合配置
- `CHUNK_SIZE`, `CHUNK_OVERLAP`: 文本切块参数

`VECTOR_BACKEND=auto` 时会优先连接 Milvus，失败后自动回退到本地 JSON 向量存储。

## 文件格式支持

直接支持：

- `pdf`
- `docx`
- `xlsx`
- `pptx`
- `txt`
- `html`
- `xml`
- `md`
- `csv`
- `json`

兼容声明但当前会返回明确错误：

- `doc`
- `xls`
- `ppt`

这些旧版二进制 Office 格式建议先转换为 `docx/xlsx/pptx` 后再上传。

## 测试

```bash
pytest
```
