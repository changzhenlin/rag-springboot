# Python RAG 服务技术文档

## 与 Spring Boot 对比详解 Python 项目运行逻辑

---

## 📋 目录

1. [项目架构对比](#项目架构对比)
2. [应用启动流程](#应用启动流程)
3. [依赖注入机制](#依赖注入机制)
4. [配置管理](#配置管理)
5. [Web 层架构](#web 层架构)
6. [服务层架构](#服务层架构)
7. [数据模型](#数据模型)
8. [运行时流程](#运行时流程)
9. [核心差异总结](#核心差异总结)

---

## 项目架构对比

### Spring Boot 架构

```
┌─────────────────────────────────────┐
│   @SpringBootApplication            │
│   (RagSpringbootApplication)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Spring ApplicationContext         │
│   - @ComponentScan                  │
│   - @Configuration                  │
│   - @Bean                           │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Controller│ │Service │ │Repository│ │Config │
└────────┘ └────────┘ └────────┘ └────────┘
```

### Python FastAPI 架构

```
┌─────────────────────────────────────┐
│   app/main.py                       │
│   create_app()                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   FastAPI 应用实例                   │
│   - routers (APIRouter)             │
│   - dependencies (Depends)          │
│   - middleware                      │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  API   │ │Service │ │ Vector │ │ Config │
│ Router │ │  Class │ │ Store  │ │ Class  │
└────────┘ └────────┘ └────────┘ └────────┘
```

---

## 应用启动流程

### Spring Boot 启动流程

```java
// 1. @SpringBootApplication 注解
@SpringBootApplication
public class RagSpringbootApplication {
    public static void main(String[] args) {
        // 2. SpringApplication.run() 启动
        SpringApplication.run(RagSpringbootApplication.class, args);
    }
}

// 3. Spring 容器自动扫描和创建 Bean
// - @Component, @Service, @Repository, @Controller
// - @Configuration + @Bean
// - 依赖自动注入 (@Autowired)
```

**启动步骤：**
1. 执行 `main()` 方法
2. `SpringApplication.run()` 启动引导
3. 创建 `ApplicationContext`（应用上下文）
4. 组件扫描（`@ComponentScan`）
5. 创建并注册所有 Bean 定义
6. 依赖注入（`@Autowired`）
7. 调用 `@PostConstruct` 初始化方法
8. 启动内嵌 Tomcat/Jetty
9. 应用就绪，监听端口

### Python FastAPI 启动流程

```python
# app/main.py

# 1. 定义应用工厂函数
def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(title=app_settings.app_name)
    
    # 2. 添加中间件
    app.add_middleware(CORSMiddleware, ...)
    
    # 3. 注册路由
    app.include_router(rag_router)
    app.include_router(test_router)
    
    return app

# 4. 创建全局应用实例
app = create_app()

# 5. 启动命令（命令行执行）
# uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**启动步骤：**
1. Python 解释器加载 `app/main.py`
2. 执行模块级代码（导入语句、函数定义）
3. 调用 `create_app()` 创建 FastAPI 实例
4. 注册中间件和路由
5. Uvicorn/Gunicorn 加载应用
6. 启动 ASGI 服务器
7. 应用就绪，监听端口

### 关键差异

| 特性 | Spring Boot | Python FastAPI |
|------|-------------|----------------|
| **启动方式** | `main()` 方法 + `SpringApplication.run()` | 模块加载 + 工厂函数 |
| **容器** | Spring ApplicationContext | FastAPI 应用实例 |
| **Bean 管理** | 自动扫描 + 注解 | 手动注册 + 依赖注入函数 |
| **启动时间** | 较慢（秒级） | 极快（毫秒级） |
| **运行模式** | 独立 JAR，内嵌服务器 | 需要 ASGI 服务器（Uvicorn） |

---

## 依赖注入机制

### Spring Boot：@Autowired

```java
// 1. 定义 Service
@Service
public class RagService {
    private final VectorStore vectorStore;
    private final DashScopeClient dashscopeClient;
    
    // 2. 构造器注入
    @Autowired
    public RagService(VectorStore vectorStore, DashScopeClient dashscopeClient) {
        this.vectorStore = vectorStore;
        this.dashscope_client = dashscopeClient;
    }
}

// 3. Controller 中使用
@RestController
@RequestMapping("/api/rag")
public class RagController {
    private final RagService ragService;
    
    @Autowired
    public RagController(RagService ragService) {
        this.ragService = ragService;
    }
    
    @PostMapping("/ask")
    public ApiResponse<AskResult> ask(@RequestBody QuestionRequest request) {
        String answer = ragService.ask(request.getQuestion(), request.getTopK());
        return ApiResponse.success(new AskResult(request.getQuestion(), answer));
    }
}
```

**Spring DI 特点：**
- 基于注解（`@Autowired`, `@Inject`）
- 容器自动管理 Bean 生命周期
- 支持多种注入方式（构造器、setter、字段）
- 默认单例模式（Singleton）

### Python FastAPI：Depends

```python
# app/dependencies.py

# 1. 定义依赖注入函数（类似 Bean 工厂方法）
@lru_cache(maxsize=1)  # 单例模式
def get_dashscope_client() -> DashScopeClient:
    return DashScopeClient(get_settings())

@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    return build_vector_store(get_settings(), get_dashscope_client())

@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService(get_vector_store(), get_dashscope_client())

# app/api/rag.py

# 2. 在路由中使用依赖注入
@router.post("/ask", response_model=ApiResponse[AskResult])
async def ask_question(
    request: QuestionRequest,
    # 使用 Depends 注入服务（类似 @Autowired）
    rag_service: Annotated[RagService, Depends(get_rag_service)],
) -> ApiResponse[AskResult]:
    answer = rag_service.ask(request.question, request.topK)
    return ApiResponse.success(AskResult(question=request.question, answer=answer))
```

**FastAPI DI 特点：**
- 基于函数（`get_xxx()`）
- 使用 `Depends()` 声明依赖
- 使用 `Annotated` 类型注解
- 使用 `@lru_cache` 实现单例
- 每次请求时解析依赖（可缓存）

### 依赖注入对比

| 特性 | Spring Boot | Python FastAPI |
|------|-------------|----------------|
| **注入方式** | `@Autowired` 注解 | `Depends()` 函数 |
| **作用域** | Singleton/Prototype/Request | 由缓存装饰器控制 |
| **循环依赖** | 支持（三级缓存） | 不支持（需避免） |
| **AOP 支持** | 强大（@Aspect） | 有限（中间件） |

---

## 配置管理

### Spring Boot：@ConfigurationProperties

```java
// application.yaml
spring:
  ai:
    dashscope:
      api-key: ${DASHSCOPE_API_KEY}
      chat-model: qwen-max
      embedding-model: text-embedding-v3

milvus:
  host: localhost
  port: 19530
  collection-name: rag_documents

// Java 配置类
@Configuration
@ConfigurationProperties(prefix = "milvus")
@Data
public class MilvusProperties {
    private String host = "localhost";
    private int port = 19530;
    private String collectionName = "rag_documents";
}
```

### Python：dataclass + 环境变量

```python
# app/core/config.py

from dataclasses import dataclass
import os

@dataclass(frozen=True)  # 不可变对象
class Settings:
    # 应用配置
    app_name: str = os.getenv("APP_NAME", "rag-python-service")
    app_port: int = int(os.getenv("SERVER_PORT", "8080"))
    
    # DashScope 配置
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_chat_model: str = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-max")
    
    # Milvus 配置
    milvus_host: str = os.getenv("MILVUS_HOST", "localhost")
    milvus_port: int = int(os.getenv("MILVUS_PORT", "19530"))
    milvus_collection_name: str = os.getenv("MILVUS_COLLECTION_NAME", "rag_documents")

# 单例获取配置
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

### 配置对比

| 特性 | Spring Boot | Python FastAPI |
|------|-------------|----------------|
| **配置源** | YAML/Properties/环境变量 | 环境变量/.env 文件 |
| **类型安全** | 编译时检查 | 运行时检查 |
| **热更新** | 支持（@RefreshScope） | 不支持（需重启） |
| **验证** | Hibernate Validator | Pydantic 验证 |

---

## Web 层架构

### Spring Boot：@RestController

```java
@RestController
@RequestMapping("/api/rag")
public class RagController {
    
    private final RagService ragService;
    
    @PostMapping("/upload")
    public ResponseEntity<ApiResponse<UploadResult>> uploadDocument(
            @RequestParam("file") MultipartFile file) {
        // 处理文件上传
    }
    
    @PostMapping("/ask")
    public ResponseEntity<ApiResponse<AskResult>> askQuestion(
            @RequestBody QuestionRequest request) {
        String answer = ragService.ask(request.getQuestion(), request.getTopK());
        return ResponseEntity.ok(ApiResponse.success(answer));
    }
    
    @GetMapping("/search")
    public ResponseEntity<ApiResponse<List<DocumentChunk>>> search(
            @RequestParam String query,
            @RequestParam(defaultValue = "4") int topK) {
        // 处理搜索请求
    }
}
```

### Python FastAPI：APIRouter

```python
# app/api/rag.py

from fastapi import APIRouter, Depends, File, UploadFile

router = APIRouter(prefix="/api/rag", tags=["rag"])

@router.post("/upload", response_model=ApiResponse[UploadResult])
async def upload_document(
    file: Annotated[UploadFile, File(...)],  # 文件上传
    parser_service: Annotated[DocumentParserService, Depends(get_document_parser_service)],
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> ApiResponse[UploadResult]:
    content = await file.read()  # 异步读取
    documents = parser_service.parse_upload(file.filename, content, file.content_type)
    vector_store.add_documents(documents)
    return ApiResponse.success(...)

@router.post("/ask", response_model=ApiResponse[AskResult])
async def ask_question(
    request: QuestionRequest,  # 自动解析 JSON
    rag_service: Annotated[RagService, Depends(get_rag_service)],
) -> ApiResponse[AskResult]:
    answer = rag_service.ask(request.question, request.topK)
    return ApiResponse.success(AskResult(question=request.question, answer=answer))

@router.get("/search", response_model=ApiResponse[list[DocumentChunk]])
async def search_similar(
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    query: str,  # URL 参数 ?query=xxx
    topK: int = 4,  # 带默认值
) -> ApiResponse[list[DocumentChunk]]:
    documents = vector_store.similarity_search(query, topK)
    return ApiResponse.success(documents)
```

### Web 层对比

| 特性 | Spring Boot | Python FastAPI |
|------|-------------|----------------|
| **路由定义** | `@RequestMapping` 等注解 | `APIRouter` 装饰器 |
| **参数绑定** | `@RequestParam`, `@RequestBody` | 类型注解自动推断 |
| **异步支持** | WebFlux（响应式） | async/await（原生异步） |
| **文件上传** | `MultipartFile` | `UploadFile` |
| **文档生成** | SpringDoc/Swagger | 自动生成 OpenAPI |
| **验证** | `@Valid` + 注解 | Pydantic 模型验证 |

---

## 服务层架构

### Spring Boot：@Service

```java
@Service
public class RagService {
    private final VectorStore vectorStore;
    private final DashScopeClient dashscopeClient;
    
    public String ask(String question, int topK) {
        // 第一步：检索
        List<DocumentChunk> documents = vectorStore.similaritySearch(question, topK);
        
        if (documents.isEmpty()) {
            return "知识库中暂无相关文档";
        }
        
        // 第二步：生成
        return generateAnswer(question, documents);
    }
    
    private String generateAnswer(String question, List<DocumentChunk> documents) {
        // 构建提示词
        String context = buildContext(documents);
        String prompt = buildPrompt(context, question);
        
        // 调用 AI 模型
        return dashscopeClient.chat(prompt);
    }
}
```

### Python：Service Class

```python
# app/services/rag_service.py

class RagService:
    def __init__(self, vector_store: VectorStore, dashscope_client: DashScopeClient) -> None:
        self.vector_store = vector_store
        self.dashscope_client = dashscope_client
    
    def ask(self, question: str, top_k: int = 4) -> str:
        # 第一步：检索（Retrieval）
        documents = self.vector_store.similarity_search(question, top_k)
        
        if not documents:
            return "知识库中暂无相关文档，无法基于上下文回答该问题。"
        
        # 第二步：生成（Generation）
        return self._generate_answer(question, documents)
    
    def _generate_answer(self, question: str, documents: list[DocumentChunk]) -> str:
        # 构建上下文
        context = "\n\n".join([
            f"[片段 {i+1}] 来源：{doc.metadata.get('source')}\n{doc.content}"
            for i, doc in enumerate(documents)
        ])
        
        # 系统提示词
        system_prompt = "你是一个专业的企业知识库问答助手..."
        prompt = f"上下文信息如下：\n{context}\n\n用户问题：{question}"
        
        try:
            # 调用 DashScope API
            return self.dashscope_client.chat(prompt=prompt, system_prompt=system_prompt)
        except DashScopeClientError as exc:
            # 降级方案
            logger.warning("Falling back to extractive answer: %s", exc)
            return self._fallback_answer(question, documents)
    
    @staticmethod
    def _fallback_answer(question: str, documents: list[DocumentChunk]) -> str:
        # 返回检索摘要
        summary = "\n\n".join([
            f"- 来源 {doc.metadata.get('source')}: {doc.content[:280]}"
            for doc in documents
        ])
        return f"DashScope 当前不可用...\n\n问题：{question}\n\n相关内容：\n{summary}"
```

### 服务层对比

| 特性 | Spring Boot | Python FastAPI |
|------|-------------|----------------|
| **类定义** | `@Service` 注解 | 普通 Python 类 |
| **初始化** | 构造器 + DI | `__init__()` 方法 |
| **方法可见性** | `private`/`protected`/`public` | `_method()` 约定私有 |
| **静态方法** | `static` 关键字 | `@staticmethod` 装饰器 |
| **异常处理** | Checked/Unchecked Exception | 全为 Unchecked |

---

## 数据模型

### Spring Boot：DTO/Entity

```java
// DTO：数据传输对象
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ApiResponse<T> {
    private int code;
    private String message;
    private T data;
    
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(200, "操作成功", data);
    }
}

// Request DTO
@Data
public class QuestionRequest {
    @NotBlank(message = "问题不能为空")
    @Size(min = 1, message = "问题长度至少为 1")
    private String question;
    
    @Min(value = 1, message = "topK 最小为 1")
    @Max(value = 20, message = "topK 最大为 20")
    private Integer topK = 4;
}

// Response DTO
@Data
public class DocumentChunk {
    private String id;
    private String content;
    private Map<String, Object> metadata;
    private Double score;
}
```

### Python：Pydantic Model

```python
# app/models/schemas.py

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any

T = TypeVar("T")  # 泛型类型变量

# 通用响应封装
class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None
    
    @classmethod
    def success(cls, data: Any, message: str = "操作成功") -> "ApiResponse[Any]":
        return cls(code=200, message=message, data=data)
    
    @classmethod
    def error(cls, message: str, code: int = 500) -> "ApiResponse[Any]":
        return cls(code=code, message=message, data=None)

# 请求模型
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)  # ... 表示必填
    topK: int = Field(default=4, ge=1, le=20)  # ge=大于等于，le=小于等于

# 文档切片模型
class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None

# 响应模型
class AskResult(BaseModel):
    question: str
    answer: str

class UploadResult(BaseModel):
    fileName: str
    chunksCount: int
    fileSize: int
```

### 数据模型对比

| 特性 | Spring Boot | Python FastAPI |
|------|-------------|----------------|
| **定义方式** | Java Class + Lombok | Pydantic BaseModel |
| **验证注解** | `@NotNull`, `@Size` 等 | `Field(..., min_length=1)` |
| **泛型支持** | `<T>` | `TypeVar("T")` |
| **序列化** | Jackson | Pydantic 内置 |
| **工厂方法** | 静态方法 | 类方法（`@classmethod`） |
| **可选字段** | `Optional<T>` | `Optional[T]` |

---

## 运行时流程

### Spring Boot 请求处理流程

```
1. HTTP 请求到达
   ↓
2. Tomcat/Jetty 接收请求
   ↓
3. DispatcherServlet（前端控制器）
   ↓
4. HandlerMapping 查找匹配的 Controller
   ↓
5. HandlerAdapter 执行 Controller 方法
   ↓
6. 参数解析（@RequestParam, @RequestBody）
   ↓
7. 依赖注入（@Autowired）
   ↓
8. 业务逻辑执行（Service 层）
   ↓
9. 返回值处理（HttpMessageConverter）
   ↓
10. 响应返回给客户端
```

### Python FastAPI 请求处理流程

```
1. HTTP 请求到达
   ↓
2. Uvicorn（ASGI 服务器）接收请求
   ↓
3. FastAPI 应用路由匹配
   ↓
4. 依赖注入系统解析 Depends()
   ↓
5. 请求验证（Pydantic 模型）
   ↓
6. 执行路由函数（async def）
   ↓
7. 业务逻辑执行（Service 层）
   ↓
8. 响应模型序列化（.model_dump()）
   ↓
9. JSON 响应返回给客户端
```

### 详细对比

#### 1. 请求入口

**Spring Boot:**
```java
// Tomcat 接收请求 → DispatcherServlet → Controller
@PostMapping("/ask")
public ResponseEntity<ApiResponse<AskResult>> askQuestion(...) {
    // 同步或异步处理
}
```

**Python FastAPI:**
```python
# Uvicorn 接收请求 → FastAPI Router → Route Function
@router.post("/ask", response_model=ApiResponse[AskResult])
async def ask_question(...) -> ApiResponse[AskResult]:
    # 异步处理（async/await）
```

#### 2. 参数绑定

**Spring Boot:**
```java
// 注解驱动
@PostMapping("/ask")
public ResponseEntity<?> ask(
    @RequestBody QuestionRequest request,  // JSON → Object
    @RequestParam String query,           // URL 参数
    @PathVariable String id               // 路径参数
) { ... }
```

**Python FastAPI:**
```python
# 类型注解驱动
@router.post("/ask")
async def ask_question(
    request: QuestionRequest,     # 自动从 JSON 解析
    query: str,                   # 自动从 URL 参数解析
    item_id: str                  # 自动从路径参数解析
) -> ApiResponse[AskResult]: ...
```

#### 3. 异常处理

**Spring Boot:**
```java
// 全局异常处理器
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(DocumentParserException.class)
    public ResponseEntity<ApiResponse<?>> handleParserException(...) {
        return ResponseEntity.status(500).body(ApiResponse.error("解析失败"));
    }
}
```

**Python FastAPI:**
```python
# 全局异常处理
@app.exception_handler(DocumentParserError)
async def parser_error_handler(request: Request, exc: DocumentParserError):
    return JSONResponse(
        status_code=500,
        content=ApiResponse.error(f"解析失败：{exc}").model_dump()
    )
```

---

## 核心差异总结

### 1. 编程范式

| Spring Boot | Python FastAPI |
|-------------|----------------|
| 面向对象（OOP） | 面向对象 + 函数式 |
| 注解驱动 | 装饰器驱动 |
| 编译时检查 | 运行时检查 |
| 强类型系统 | 动态类型 + 类型提示 |

### 2. 并发模型

| Spring Boot | Python FastAPI |
|-------------|----------------|
| 多线程（Thread per Request） | 异步 IO（Async/Await） |
| 阻塞式 IO | 非阻塞 IO |
| WebFlux（响应式） | 原生异步支持 |
| 线程池管理 | 事件循环（Event Loop） |

### 3. 生态系统

| Spring Boot | Python FastAPI |
|-------------|----------------|
| Maven/Gradle 构建 | pip/poetry 包管理 |
| Spring 全家桶 | 轻量级框架 |
| 企业级生态 | 数据科学生态 |
| JRE 依赖 | Python 解释器依赖 |

### 4. 性能特征

| Spring Boot | Python FastAPI |
|-------------|----------------|
| JVM 优化（JIT） | CPython 解释器 |
| 启动慢（秒级） | 启动快（毫秒级） |
| 内存占用高 | 内存占用低 |
| 高并发能力强 | 受 GIL 限制 |

### 5. 开发体验

| Spring Boot | Python FastAPI |
|-------------|----------------|
| IDE 友好（IntelliJ） | 编辑器友好（VSCode） |
| 重构工具强大 | 动态类型难重构 |
| 学习曲线陡峭 | 学习曲线平缓 |
| 代码冗长 | 代码简洁 |

---

## 附录：完整示例对比

### Spring Boot 完整示例

```java
// 1. 启动类
@SpringBootApplication
public class RagSpringbootApplication {
    public static void main(String[] args) {
        SpringApplication.run(RagSpringbootApplication.class, args);
    }
}

// 2. 配置类
@Configuration
@ConfigurationProperties(prefix = "dashscope")
@Data
public class DashScopeProperties {
    private String apiKey;
    private String chatModel = "qwen-max";
}

// 3. 服务类
@Service
public class RagService {
    private final VectorStore vectorStore;
    private final DashScopeClient dashscopeClient;
    
    @Autowired
    public RagService(VectorStore vectorStore, DashScopeClient dashscopeClient) {
        this.vectorStore = vectorStore;
        this.dashscopeClient = dashscopeClient;
    }
    
    public String ask(String question, int topK) {
        List<DocumentChunk> docs = vectorStore.similaritySearch(question, topK);
        if (docs.isEmpty()) {
            return "知识库中暂无相关文档";
        }
        return generateAnswer(question, docs);
    }
}

// 4. 控制器
@RestController
@RequestMapping("/api/rag")
public class RagController {
    private final RagService ragService;
    
    @Autowired
    public RagController(RagService ragService) {
        this.ragService = ragService;
    }
    
    @PostMapping("/ask")
    public ResponseEntity<ApiResponse<AskResult>> ask(@RequestBody QuestionRequest request) {
        String answer = ragService.ask(request.getQuestion(), request.getTopK());
        return ResponseEntity.ok(ApiResponse.success(new AskResult(request.getQuestion(), answer)));
    }
}
```

### Python FastAPI 完整示例

```python
# 1. 应用入口（app/main.py）
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="RAG Service")
    app.include_router(rag_router)
    return app

app = create_app()

# 2. 配置类（app/core/config.py）
@dataclass(frozen=True)
class Settings:
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_chat_model: str = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-max")

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

# 3. 服务类（app/services/rag_service.py）
class RagService:
    def __init__(self, vector_store: VectorStore, dashscope_client: DashScopeClient):
        self.vector_store = vector_store
        self.dashscope_client = dashscope_client
    
    def ask(self, question: str, top_k: int = 4) -> str:
        docs = self.vector_store.similarity_search(question, top_k)
        if not docs:
            return "知识库中暂无相关文档"
        return self._generate_answer(question, docs)

# 4. 依赖注入（app/dependencies.py）
@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService(get_vector_store(), get_dashscope_client())

# 5. 路由（app/api/rag.py）
@router.post("/ask", response_model=ApiResponse[AskResult])
async def ask_question(
    request: QuestionRequest,
    rag_service: Annotated[RagService, Depends(get_rag_service)],
) -> ApiResponse[AskResult]:
    answer = rag_service.ask(request.question, request.topK)
    return ApiResponse.success(AskResult(question=request.question, answer=answer))
```

---

## 总结

### Spring Boot 优势
- ✅ 企业级框架，生态完善
- ✅ 强大的依赖注入和 AOP
- ✅ 编译时类型安全
- ✅ 优秀的 IDE 支持
- ✅ 成熟的微服务解决方案

### Python FastAPI 优势
- ✅ 简洁优雅，学习成本低
- ✅ 原生异步支持
- ✅ 自动生成 API 文档
- ✅ 启动速度快
- ✅ 适合快速原型开发

### 适用场景

**选择 Spring Boot：**
- 大型企业级应用
- 复杂的业务逻辑
- 需要强大的事务管理
- 团队熟悉 Java 生态

**选择 Python FastAPI：**
- 快速开发和迭代
- AI/ML 相关服务
- 数据密集型应用
- 需要灵活的架构

---

**文档版本：** v1.0  
**最后更新：** 2026-04-02  
**作者：** AI Assistant
