package com.example.urlshortner.service;
import com.example.urlshortner.model.UrlEvent;
import lombok.RequiredArgsConstructor;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ShortenService {
    private final JdbcTemplate jdbc;
    private final RabbitTemplate rabbit;

    @Value("${app.exchange}")
    private String exchange;

    @Value("${app.base-url}")
    private String baseUrl;

    /**
     * Generates a 6-char alphanumeric code, persists it to Postgres,
     * then broadcasts a fanout event to RabbitMQ.
     */

    public String shorten(String originalUrl , String ip , String userAgent)
    {
        //Generate short code from uuid (first 6 chars)
        String shortCode = UUID.randomUUID().toString().replace("","").substring(0,6);
        //Write to Postgres
        jdbc.update(
                "INSERT INTO urls (short_code , original_url) VALUES (? , ?)",
                shortCode , originalUrl
        );

        UrlEvent event = UrlEvent.builder()
                .type("URL_CREATED")
                .shortCode(shortCode)
                .originalUrl(originalUrl)
                .ip(ip)
                .userAgent(userAgent)
                .timestamp(Instant.now().toString())
                .build();
        rabbit.convertAndSend(exchange , "" , event);
        return shortCode;
    }

    public String resolve(String shortCode){
        return jdbc.queryForObject(
                "SELECT original_url FROM urls WHERE short_code = ?",
                String.class , shortCode
        );
    }


        public void publishVisit(String shortCode, String ip, String userAgent) {
        UrlEvent event = UrlEvent.builder()
            .type("URL_VISITED")
            .shortCode(shortCode)
            .ip(ip)
            .userAgent(userAgent)
            .timestamp(Instant.now().toString())
            .build();

        rabbit.convertAndSend(exchange, "", event);
    }
}
