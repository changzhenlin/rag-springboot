from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.dependencies import get_dashscope_client
from app.models.schemas import TestResult
from app.services.dashscope_client import DashScopeClient

router = APIRouter(prefix="/api/test", tags=["test"])


@router.get("/simple", response_model=TestResult)
async def simple_test(
    client: Annotated[DashScopeClient, Depends(get_dashscope_client)],
) -> TestResult:
    question = "你好，请用一句话介绍你自己"
    try:
        answer = client.chat(question)
        return TestResult(
            success=True,
            method="DashScope Generation",
            question=question,
            answer=answer,
            message="✅ 测试成功！",
        )
    except Exception as exc:
        return TestResult(success=False, error=str(exc), message="❌ 测试失败，请检查配置")


@router.get("/detailed", response_model=TestResult)
async def detailed_test(
    client: Annotated[DashScopeClient, Depends(get_dashscope_client)],
) -> TestResult:
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
            modelStatus="active",
            message="✅ 详细测试成功！",
        )
    except Exception as exc:
        return TestResult(success=False, error=str(exc), message="❌ 测试失败")


@router.get("/health")
async def health_check(
    client: Annotated[DashScopeClient, Depends(get_dashscope_client)],
) -> dict[str, object]:
    return {
        "chatClientAvailable": client.is_configured(),
        "status": "configured" if client.is_configured() else "not_configured",
        "message": "✅ DashScope 配置已加载" if client.is_configured() else "❌ DashScope 未配置",
    }


@router.get("/page", response_class=HTMLResponse)
async def test_page() -> str:
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
