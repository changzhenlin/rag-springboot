package com.example.ragspringboot.service;

import lombok.extern.slf4j.Slf4j;
import org.apache.tika.Tika;
import org.apache.tika.exception.TikaException;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.parser.AutoDetectParser;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.sax.BodyContentHandler;
import org.springframework.ai.document.Document;
import org.springframework.ai.reader.tika.TikaDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.xml.sax.SAXException;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 文档解析服务 - 支持多种文档格式
 */
@Slf4j
@Service
public class DocumentParserService {
    
    private final Tika tika = new Tika();
    private final AutoDetectParser parser = new AutoDetectParser();
    private final TokenTextSplitter textSplitter;
    
    public DocumentParserService(TokenTextSplitter tokenTextSplitter) {
        this.textSplitter = tokenTextSplitter;
    }
    
    /**
     * 解析上传的文件
     */
    public List<Document> parseDocument(MultipartFile file) throws IOException {
        String filename = file.getOriginalFilename();
        log.info("开始解析文档: {}", filename);
        
        String content = extractText(file.getInputStream(), filename);
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("source", filename);
        metadata.put("fileSize", file.getSize());
        metadata.put("contentType", file.getContentType());
        
        Document document = new Document(content, metadata);
        
        // 分割文档
        List<Document> chunks = textSplitter.apply(List.of(document));
        log.info("文档已分割为 {} 个块", chunks.size());
        
        return chunks;
    }
    
    /**
     * 解析本地文件
     */
    public List<Document> parseDocument(Path filePath) throws IOException {
        String filename = filePath.getFileName().toString();
        log.info("开始解析文档: {}", filename);
        
        String content = extractText(Files.newInputStream(filePath), filename);
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("source", filename);
        metadata.put("filePath", filePath.toString());
        
        Document document = new Document(content, metadata);
        List<Document> chunks = textSplitter.apply(List.of(document));
        
        log.info("文档已分割为 {} 个块", chunks.size());
        return chunks;
    }
    
    /**
     * 提取文本内容
     */
    private String extractText(InputStream inputStream, String filename) throws IOException {
        try {
            BodyContentHandler handler = new BodyContentHandler(-1);
            Metadata metadata = new Metadata();
            metadata.set(Metadata.RESOURCE_NAME_KEY, filename);
            ParseContext context = new ParseContext();
            
            parser.parse(inputStream, handler, metadata, context);
            
            return handler.toString().trim();
        } catch (TikaException | SAXException e) {
            log.error("文档解析失败: {}", filename, e);
            throw new IOException("文档解析失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 支持的文档类型
     */
    public static String[] SUPPORTED_TYPES = {
            "pdf", "doc", "docx", "xls", "xlsx", 
            "ppt", "pptx", "txt", "html", "xml", 
            "md", "csv", "json"
    };
    
    /**
     * 检查文件类型是否支持
     */
    public static boolean isSupported(String filename) {
        if (filename == null) return false;
        String extension = filename.substring(filename.lastIndexOf('.') + 1).toLowerCase();
        for (String type : SUPPORTED_TYPES) {
            if (type.equals(extension)) return true;
        }
        return false;
    }
}
