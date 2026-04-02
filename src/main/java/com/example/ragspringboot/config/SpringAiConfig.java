package com.example.ragspringboot.config;

import com.alibaba.cloud.ai.dashscope.api.DashScopeApi;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Spring AI 配置类
 * 使用阿里云百炼 DashScope API（通义千问 Qwen 模型）
 */
@Configuration
public class SpringAiConfig {
    
    @Value("${spring.ai.dashscope.api-key}")
    private String apiKey;
    
    /**
     * 创建 DashScope API 客户端
     * Spring AI Alibaba 会自动配置 DashScopeChatModel 和 DashScopeEmbeddingModel
     */
    @Bean
    public DashScopeApi dashScopeApi() {
        return new DashScopeApi(apiKey);
    }
    
    /**
     * 创建 Chat 客户端
     * 使用 ChatClient.Builder 方式创建，支持任意 ChatModel 实现
     */
    @Bean
    public ChatClient chatClient(ChatClient.Builder builder) {
        return builder.defaultAdvisors(new SimpleLoggerAdvisor())
                .build();
    }
}
