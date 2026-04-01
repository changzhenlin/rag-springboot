package com.example.ragspringboot.controller;

import com.example.ragspringboot.dto.ApiResponse;
import com.example.ragspringboot.dto.QuestionRequest;
import com.example.ragspringboot.service.DocumentParserService;
import com.example.ragspringboot.service.RagService;
import com.example.ragspringboot.service.VectorStoreService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * RAG问答控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/rag")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class RagController {
    
    private final DocumentParserService documentParserService;
    private final VectorStoreService vectorStoreService;
    private final RagService ragService;
    
    /**
     * 上传并解析文档
     */
    @PostMapping("/upload")
    public ResponseEntity<ApiResponse<Map<String, Object>>> uploadDocument(
            @RequestParam("file") MultipartFile file) {
        
        try {
            // 检查文件类型
            if (!DocumentParserService.isSupported(file.getOriginalFilename())) {
                return ResponseEntity.badRequest()
                        .body(ApiResponse.error("不支持的文件类型"));
            }
            
            // 解析文档
            List<Document> documents = documentParserService.parseDocument(file);
            
            // 存储到向量库
            vectorStoreService.addDocuments(documents);
            
            Map<String, Object> result = new HashMap<>();
            result.put("fileName", file.getOriginalFilename());
            result.put("chunksCount", documents.size());
            result.put("fileSize", file.getSize());
            
            return ResponseEntity.ok(ApiResponse.success("文档上传成功", result));
            
        } catch (IOException e) {
            log.error("文档上传失败", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("文档解析失败: " + e.getMessage()));
        }
    }
    
    /**
     * RAG问答
     */
    @PostMapping("/ask")
    public ResponseEntity<ApiResponse<Map<String, String>>> askQuestion(
            @RequestBody QuestionRequest request) {
        
        try {
            String answer;
            if (request.getTopK() != null) {
                answer = ragService.askWithContext(request.getQuestion(), request.getTopK());
            } else {
                answer = ragService.ask(request.getQuestion());
            }
            
            Map<String, String> result = new HashMap<>();
            result.put("question", request.getQuestion());
            result.put("answer", answer);
            
            return ResponseEntity.ok(ApiResponse.success(result));
            
        } catch (Exception e) {
            log.error("问答处理失败", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("问答处理失败: " + e.getMessage()));
        }
    }
    
    /**
     * 相似度搜索（不生成回答）
     */
    @GetMapping("/search")
    public ResponseEntity<ApiResponse<List<Document>>> searchSimilar(
            @RequestParam String query,
            @RequestParam(defaultValue = "4") int topK) {
        
        try {
            List<Document> documents = vectorStoreService.similaritySearch(query, topK);
            return ResponseEntity.ok(ApiResponse.success(documents));
        } catch (Exception e) {
            log.error("搜索失败", e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("搜索失败: " + e.getMessage()));
        }
    }
    
    /**
     * 健康检查
     */
    @GetMapping("/health")
    public ResponseEntity<ApiResponse<Map<String, Object>>> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("hasDocuments", vectorStoreService.hasDocuments());
        return ResponseEntity.ok(ApiResponse.success(health));
    }
}
