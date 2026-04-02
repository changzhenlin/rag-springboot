# 导入未来版本注解
from __future__ import annotations

# 导入类型注解
from typing import Annotated

# 从 fastapi 导入路由类
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

# 导入依赖注入函数
from app.dependencies import get_dashscope_client
# 导入数据模型
from app.models.schemas import TestResult
# 导入 DashScope 客户端
from app.services.dashscope_client import DashScopeClient

# 创建测试路由（类似 Spring 的 @RestController）
# prefix="/api/test" 表示所有测试接口的前缀
router = APIRouter(prefix="/api/test", tags=["test"])


# 简单测试接口：GET /api/test/simple
@router.get("/simple", response_model=TestResult)
async def simple_test(
    # client: 注入 DashScope 客户端
    client: Annotated[DashScopeClient, Depends(get_dashscope_client)],
) -> TestResult:
    # 定义测试问题
    question = "你好，请用一句话介绍你自己"
    try:
        # 调用 DashScope API 进行聊天测试
        answer = client.chat(question)
        # 返回成功结果
        return TestResult(
            success=True,
            method="DashScope Generation",
            question=question,
            answer=answer,
            message="✅ 测试成功！",
        )
    except Exception as exc:
        # 捕获异常并返回错误信息
        return TestResult(success=False, error=str(exc), message="❌ 测试失败，请检查配置")


# 详细测试接口：GET /api/test/detailed
@router.get("/detailed", response_model=TestResult)
async def detailed_test(
    client: Annotated[DashScopeClient, Depends(get_dashscope_client)],
) -> TestResult:
    # 定义更详细的测试问题，用于验证模型功能
    question = (
        "你好，我想测试通义千问模型是否正常工作。"
        "请告诉我：1）你是谁？2）你现在能正常回答问题吗？3）你的模型名称是什么？"
    )
    try:
        answer = client.chat(question)
        return TestResult(
            success=True,
            method="DashScope Generation",
            question=question,
            answer=answer,
            modelStatus="active",  # 标记模型处于活跃状态
            message="✅ 详细测试成功！",
        )
    except Exception as exc:
        return TestResult(success=False, error=str(exc), message="❌ 测试失败")


# 健康检查接口：GET /api/test/health
@router.get("/health")
async def health_check(
    client: Annotated[DashScopeClient, Depends(get_dashscope_client)],
) -> dict[str, object]:
    # 返回 DashScope 客户端的配置状态
    return {
        "chatClientAvailable": client.is_configured(),  # API Key 是否已配置
        "status": "configured" if client.is_configured() else "not_configured",
        "message": "✅ DashScope 配置已加载" if client.is_configured() else "❌ DashScope 未配置",
    }


# 测试页面：GET /api/test/page（返回 HTML 页面）
@router.get("/page", response_class=HTMLResponse)
async def test_page() -> str:
    # 返回一个完整的 HTML 测试页面（类似 Thymeleaf 模板）
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>通义千问模型测试</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .test-btn { padding: 15px 30px; margin: 10px; font-size: 16px; cursor: pointer; background-color: #4CAF50; color: white; border: none; border-radius: 5px; }
            .test-btn:hover { background-color: #45a049; }
            .result { margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; white-space: pre-wrap; }
            .success { color: green; }
            .error { color: red; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>🤖 通义千问 Qwen 模型测试</h1>
        <div>
            <button class="test-btn" onclick="runTest('simple')">📝 简单测试</button>
            <button class="test-btn" onclick="runTest('detailed')">📊 详细测试</button>
            <button class="test-btn" onclick="checkHealth()">💚 健康检查</button>
        </div>
        <div id="result" class="result" style="display:none;"></div>
        <script>
            // 运行测试的 JavaScript 函数
            async function runTest(type) {
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = '⏳ 正在测试...';
                try {
                    const response = await fetch('/api/test/' + type);
                    const data = await response.json();
                    const className = data.success ? 'success' : 'error';
                    resultDiv.innerHTML = '<div class="' + className + '">' +
                        '<strong>' + data.message + '</strong><br><br>' +
                        '<strong>方法：</strong>' + (data.method || 'N/A') + '<br><br>' +
                        '<strong>问题：</strong>' + (data.question || 'N/A') + '<br><br>' +
                        '<strong>回答：</strong>' + (data.answer || 'N/A') +
                        '</div>';
                } catch (error) {
                    resultDiv.innerHTML = '<div class="error">❌ 请求失败：' + error.message + '</div>';
                }
            }
            // 健康检查的 JavaScript 函数
            async function checkHealth() {
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                try {
                    const response = await fetch('/api/test/health');
                    const data = await response.json();
                    let html = '<div class="success"><strong>✅ 健康检查结果：</strong><br><br>';
                    for (const [key, value] of Object.entries(data)) {
                        html += key + ': ' + JSON.stringify(value) + '<br>';
                    }
                    html += '</div>';
                    resultDiv.innerHTML = html;
                } catch (error) {
                    resultDiv.innerHTML = '<div class="error">❌ 请求失败：' + error.message + '</div>';
                }
            }
        </script>
    </body>
    </html>
    """
