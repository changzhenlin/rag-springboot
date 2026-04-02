package com.example.ragspringboot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.ai.autoconfigure.vectorstore.milvus.MilvusVectorStoreAutoConfiguration;

/**
 * 企业级 RAG 智能问答系统
 * 
 * 核心功能：
 * - 文档解析：支持 PDF、Word、Excel、PPT 等多种格式
 * - 向量存储：使用 Milvus 向量数据库
 * - RAG 检索：基于向量相似度的智能检索
 * - AI 回答：结合检索结果生成准确回答
 */
@SpringBootApplication(exclude = {MilvusVectorStoreAutoConfiguration.class})
@EnableConfigurationProperties
public class RagSpringbootApplication {

    public static void main(String[] args) {
        SpringApplication.run(RagSpringbootApplication.class, args);
    }
}
