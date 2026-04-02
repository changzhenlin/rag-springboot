package com.example.ragspringboot.config;

import io.milvus.client.MilvusClient;
import io.milvus.client.MilvusServiceClient;
import io.milvus.param.ConnectParam;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.milvus.MilvusVectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Milvus向量数据库配置类
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class MilvusConfig {
    
    private final MilvusProperties milvusProperties;
    
    @Value("${spring.ai.dashscope.api-key}")
    private String dashScopeApiKey;
    
    /**
     * 创建 Milvus 客户端
     */
    @Bean
    public MilvusClient milvusClient() {
        ConnectParam.Builder builder = ConnectParam.newBuilder()
                .withHost(milvusProperties.getHost())
                .withPort(milvusProperties.getPort());
        
        if (milvusProperties.getUsername() != null && !milvusProperties.getUsername().isEmpty()) {
            builder.withAuthorization(milvusProperties.getUsername(), milvusProperties.getPassword());
        }
        
        log.info("连接 Milvus：{}:{}", milvusProperties.getHost(), milvusProperties.getPort());
        return new MilvusServiceClient(builder.build());
    }
    
    /**
     * 创建 Milvus 向量存储
     */
    @Bean
    public VectorStore vectorStore(MilvusClient milvusClient, EmbeddingModel embeddingModel) {
        return MilvusVectorStore.builder((MilvusServiceClient) milvusClient, embeddingModel)
                .collectionName(milvusProperties.getCollectionName())
                .embeddingDimension(milvusProperties.getDimension())
                .initializeSchema(true)
                .build();
    }
    
    /**
     * 文本分割器配置
     */
    @Bean
    public TokenTextSplitter tokenTextSplitter() {
        return new TokenTextSplitter();
    }
}
