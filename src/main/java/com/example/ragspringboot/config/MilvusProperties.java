package com.example.ragspringboot.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * Milvus向量数据库配置属性
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "milvus")
public class MilvusProperties {
    
    /**
     * Milvus服务器地址
     */
    private String host = "localhost";
    
    /**
     * Milvus服务器端口
     */
    private int port = 19530;
    
    /**
     * 用户名（可选）
     */
    private String username = "";
    
    /**
     * 密码（可选）
     */
    private String password = "";
    
    /**
     * 集合名称
     */
    private String collectionName = "rag_documents";
    
    /**
     * 向量维度
     */
    private int dimension = 1536;
    
    /**
     * 索引类型
     */
    private String indexType = "IVF_FLAT";
    
    /**
     * 距离度量类型
     */
    private String metricType = "COSINE";
}
