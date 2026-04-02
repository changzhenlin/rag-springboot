# 导入未来版本注解，启用 Python 3.7+ 的新特性
from __future__ import annotations

# 导入日志模块
import logging

# 从 fastapi 框架导入 FastAPI 主类（类似 Spring Boot 的 @SpringBootApplication）
from fastapi import FastAPI
# 导入 CORS 中间件，用于处理跨域请求（类似 Spring 的 @CrossOrigin）
from fastapi.middleware.cors import CORSMiddleware

# 从 app.api 包导入路由处理器
from app.api.rag import router as rag_router
from app.api.test import router as test_router
# 从配置模块导入设置类和获取设置的函数
from app.core.config import Settings, get_settings

# 配置日志系统的基本格式和级别
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


# 应用工厂函数：创建并配置 FastAPI 应用实例
# 类似 Spring Boot 中手动构建 SpringApplication 的方式
# settings 参数可选，默认使用 get_settings() 获取配置
def create_app(settings: Settings | None = None) -> FastAPI:
    # 如果未提供 settings，则使用默认的设置（单例模式缓存）
    app_settings = settings or get_settings()
    # 创建 FastAPI 应用实例，设置应用名称
    app = FastAPI(title=app_settings.app_name)
    
    # 添加 CORS 跨域中间件（类似 Spring Security 的 CORS 配置）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,  # 允许的来源域名
        allow_credentials=True,  # 允许携带凭证（cookies）
        allow_methods=["*"],  # 允许所有 HTTP 方法（GET/POST/PUT/DELETE 等）
        allow_headers=["*"],  # 允许所有 HTTP 头
    )
    
    # 注册 RAG 相关的路由（类似 Spring 的 @RestController）
    app.include_router(rag_router)
    # 注册测试相关的路由
    app.include_router(test_router)
    
    # 返回配置好的应用实例
    return app


# 创建全局应用实例（类似 Spring Boot 自动启动的应用上下文）
app = create_app()
