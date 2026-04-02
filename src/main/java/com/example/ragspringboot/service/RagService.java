package com.example.ragspringboot.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.QuestionAnswerAdvisor;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

/**
 * RAG问答服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RagService {
    
    private final VectorStore vectorStore;
    private final ChatClient chatClient;
    private final ChatModel chatModel;
    
    /**
     * RAG问答
     */
    public String ask(String question) {
        log.info("收到问题: {}", question);
        
        String systemPrompt = """
                你是一个专业的企业知识库问答助手。请根据提供的上下文信息来回答用户的问题。
                
                回答要求：
                1. 基于提供的上下文信息进行回答
                2. 如果上下文中没有相关信息，请明确告知用户
                3. 回答要准确、简洁、有条理
                4. 如果涉及代码，请使用代码块格式
                """;
        
        String response = chatClient.prompt()
                .system(systemPrompt)
                .user(question)
                .advisors(QuestionAnswerAdvisor.builder(vectorStore).build())
                .call()
                .content();
        
        log.info("回答生成完成");
        return response;
    }
    
    /**
     * 带上下文字数的RAG问答
     */
    public String askWithContext(String question, int topK) {
        log.info("收到问题: {}, 检索topK: {}", question, topK);
        
        String systemPrompt = """
                你是一个专业的企业知识库问答助手。请根据提供的上下文信息来回答用户的问题。
                
                回答要求：
                1. 基于提供的上下文信息进行回答
                2. 如果上下文中没有相关信息，请明确告知用户
                3. 回答要准确、简洁、有条理
                4. 如果涉及代码，请使用代码块格式
                """;
        
        String response = chatClient.prompt()
                .system(systemPrompt)
                .user(question)
                .advisors(QuestionAnswerAdvisor.builder(vectorStore).searchRequest(SearchRequest.builder().topK(topK).build()).build())
                .call()
                .content();
        
        log.info("回答生成完成");
        return response;
    }
}
