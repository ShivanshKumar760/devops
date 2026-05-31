package com.example.urlshortner.controller;
import java.net.URI;
import org.springframework.http.HttpHeaders;
import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

// Removed duplicate import of org.springframework.http.HttpHeaders
import com.example.urlshortner.service.ShortenService;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;

@RestController
@RequiredArgsConstructor
public class UrlController {
    private final ShortenService shortenService;
    private final JdbcTemplate jdbc;

    @Value("${app.base-url}")
    private String baseUrl;

    @PostMapping("/short")
    public ResponseEntity<Map<String,String>> shorten(
        @RequestBody Map<String,String> body,
        HttpServletRequest req
    ){
        String url = body.get("url");
        if (url == null || url.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "url is required"));
        }
        String shortCode = shortenService.shorten(url , req.getRemoteAddr() , req.getHeader("User-Agent"));
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of("shortUrl", baseUrl + "/" + shortCode));
    }

        /**
     * GET /{code} — redirect to original URL
     */
    @GetMapping("/{code}")
    public ResponseEntity<Void> redirect(
            @PathVariable String code,
            HttpServletRequest req) {
 
        try {
            String originalUrl = shortenService.resolve(code);
            shortenService.publishVisit(code, req.getRemoteAddr(), req.getHeader("User-Agent"));
 
            HttpHeaders headers = new HttpHeaders();
            headers.setLocation(URI.create(originalUrl));
            return new ResponseEntity<>(headers, HttpStatus.FOUND);
        } catch (EmptyResultDataAccessException e) {
            return ResponseEntity.notFound().build();
        }
    }
 
    /**
     * GET /api/analytics/{code}
     */
    @GetMapping("/api/analytics/{code}")
    public ResponseEntity<Map<String, Object>> analytics(@PathVariable String code) {
        List<Map<String, Object>> visits = jdbc.queryForList(
            "SELECT ip_address, user_agent, visited_at FROM analytics " +
            "WHERE short_code = ? ORDER BY visited_at DESC",
            code
        );
        return ResponseEntity.ok(Map.of("short_code", code, "visits", visits));
    }

}
