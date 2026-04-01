package com.example.ragspringboot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

/**
 * 企业级RAG智能问答系统
 * 
 * 核心功能：
 * - 文档解析：支持PDF、Word、Excel、PPT等多种格式
 * - 向量存储：使用Milvus向量数据库
 * - RAG检索：基于向量相似度的智能检索
 * - AI回答：结合检索结果生成准确回答
 */
@SpringBootApplication
@EnableConfigurationProperties
public class RagSpringbootApplication {

    public static void main(String[] args) {
        SpringApplication.run(RagSpringbootApplication.class, args);
    }
}
