package com.example.ragspringboot.config;

import io.milvus.client.MilvusClient;
import io.milvus.param.ConnectParam;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.reader.tika.TikaDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.MilvusVectorStore;
import org.springframework.ai.vectorstore.VectorStore;
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
    
    @Value("${spring.ai.openai.api-key}")
    private String openAiApiKey;
    
    /**
     * 创建Milvus客户端
     */
    @Bean
    public MilvusClient milvusClient() {
        ConnectParam.Builder builder = ConnectParam.newBuilder()
                .withHost(milvusProperties.getHost())
                .withPort(milvusProperties.getPort());
        
        if (milvusProperties.getUsername() != null && !milvusProperties.getUsername().isEmpty()) {
            builder.withUsername(milvusProperties.getUsername())
                   .withPassword(milvusProperties.getPassword());
        }
        
        log.info("连接Milvus: {}:{}", milvusProperties.getHost(), milvusProperties.getPort());
        return new MilvusClient(builder.build());
    }
    
    /**
     * 创建Milvus向量存储
     */
    @Bean
    public VectorStore vectorStore(MilvusClient milvusClient) {
        return MilvusVectorStore.builder()
                .milvusClient(milvusClient)
                .collectionName(milvusProperties.getCollectionName())
                .dimension(milvusProperties.getDimension())
                .build();
    }
    
    /**
     * 文本分割器配置
     */
    @Bean
    public TokenTextSplitter tokenTextSplitter() {
        return new TokenTextSplitter(
                500,    // minChunkSizeChars
                300,    // minChunkLengthToEmbed
                200,    // minLeftChunkSizeChars
                512,    // maxNumChunks
                true,   // trackPartialChunks
                0.2f    // chunkOverlapPercentage
        );
    }
}
