package com.example.ragspringboot.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 向量存储服务
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class VectorStoreService {
    
    private final VectorStore vectorStore;
    
    /**
     * 添加文档到向量库
     */
    public void addDocuments(List<Document> documents) {
        log.info("添加 {} 个文档块到向量库", documents.size());
        vectorStore.add(documents);
        log.info("文档添加成功");
    }
    
    /**
     * 删除文档
     */
    public void deleteDocuments(List<String> documentIds) {
        log.info("删除 {} 个文档", documentIds.size());
        vectorStore.delete(documentIds);
        log.info("文档删除成功");
    }
    
    /**
     * 相似度搜索
     */
    public List<Document> similaritySearch(String query, int topK) {
        log.info("执行相似度搜索：{}, topK: {}", query, topK);
        return vectorStore.similaritySearch(
            SearchRequest.builder()
                .query(query)
                .topK(topK)
                .build()
        );
    }
        
    /**
     * 检查向量库是否包含文档
     */
    public boolean hasDocuments() {
        return !vectorStore.similaritySearch(
            SearchRequest.builder()
                .query("")
                .topK(1)
                .build()
        ).isEmpty();
    }
}
