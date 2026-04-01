package com.example.ragspringboot.dto;

import lombok.Data;

/**
 * 问答请求DTO
 */
@Data
public class QuestionRequest {
    
    /**
     * 用户问题
     */
    private String question;
    
    /**
     * 检索的topK数量，默认4
     */
    private Integer topK = 4;
}
