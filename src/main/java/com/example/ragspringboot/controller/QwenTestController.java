package com.example.ragspringboot.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 通义千问模型测试控制器
 * 用于验证 DashScope API 配置是否正确
 */
@Slf4j
@RestController
@RequestMapping("/api/test")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class QwenTestController {
    
    private final ChatClient chatClient;
    
    /**
     * 简单测试 - 使用 ChatClient
     */
    @GetMapping("/simple")
    public Map<String, Object> simpleTest() {
        log.info("开始执行简单测试...");
        
        Map<String, Object> result = new HashMap<>();
        try {
            String response = chatClient.prompt()
                    .user("你好，请用一句话介绍你自己")
                    .call()
                    .content();
            
            result.put("success", true);
            result.put("method", "ChatClient");
            result.put("question", "你好，请用一句话介绍你自己");
            result.put("answer", response);
            result.put("message", "✅ 测试成功！");
            
            log.info("简单测试成功：{}", response);
        } catch (Exception e) {
            log.error("简单测试失败", e);
            result.put("success", false);
            result.put("error", e.getMessage());
            result.put("message", "❌ 测试失败，请检查配置");
        }
        
        return result;
    }
    
    /**
     * 详细测试 - 使用 Prompt 方式
     */
    @GetMapping("/detailed")
    public Map<String, Object> detailedTest() {
        log.info("开始执行详细测试...");
        
        Map<String, Object> result = new HashMap<>();
        try {
            // 创建用户消息
            UserMessage userMessage = new UserMessage(
                "你好，我想测试通义千问模型是否正常工作。" +
                "请告诉我：1）你是谁？2）你现在能正常回答问题吗？3）你的模型名称是什么？"
            );
            
            // 创建 Prompt
            Prompt prompt = new Prompt(List.of(userMessage));
            
            // 调用模型
            String response = chatClient.prompt(prompt)
                    .call()
                    .content();
            
            result.put("success", true);
            result.put("method", "Prompt with ChatClient");
            result.put("question", userMessage.getText());
            result.put("answer", response);
            result.put("modelStatus", "active");
            result.put("message", "✅ 详细测试成功！");
            
            log.info("详细测试成功：{}", response);
        } catch (Exception e) {
            log.error("详细测试失败", e);
            result.put("success", false);
            result.put("error", e.getMessage());
            result.put("message", "❌ 测试失败");
        }
        
        return result;
    }
    
    /**
     * 健康检查 - 检查 ChatClient 是否可用
     */
    @GetMapping("/health")
    public Map<String, Object> healthCheck() {
        Map<String, Object> health = new HashMap<>();
        
        health.put("chatClientAvailable", chatClient != null);
        health.put("status", "configured");
        health.put("message", "✅ DashScope 配置已加载");
        
        return health;
    }
    
    /**
     * 完整测试页面（HTML）
     */
    @GetMapping("/page")
    public String testPage() {
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
                   <h1>🤖 通义千问 Qwen-Max 模型测试</h1>
                   
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
                                   '<strong>方法：</strong>' + data.method + '<br><br>' +
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
               """;
    }
}
