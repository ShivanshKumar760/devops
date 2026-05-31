package com.example.urlshortner.worker;

import com.example.urlshortner.model.UrlEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.sql.Timestamp;
import java.time.Instant;

/**
 * Analytics Worker
 * Listens on audit_q and appends visit records to the analytics table.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AnalyticsWorker {

    private final JdbcTemplate jdbc;

    @RabbitListener(queues = "${app.audit-queue}")
    public void handleEvent(UrlEvent event) {
        if (event == null || event.getType() == null) return;

        if ("URL_VISITED".equals(event.getType()) || "URL_CREATED".equals(event.getType())) {
            try {
                Timestamp ts = event.getTimestamp() != null
                    ? Timestamp.from(Instant.parse(event.getTimestamp()))
                    : new Timestamp(System.currentTimeMillis());

                jdbc.update(
                    "INSERT INTO analytics (short_code, ip_address, user_agent, visited_at) VALUES (?, ?, ?, ?)",
                    event.getShortCode(),
                    event.getIp() != null ? event.getIp() : "unknown",
                    event.getUserAgent() != null ? event.getUserAgent() : "",
                    ts
                );

                log.info("[Analytics] Logged: {} from {}", event.getShortCode(), event.getIp());
            } catch (Exception e) {
                log.error("[Analytics] DB insert failed: {}", e.getMessage());
            }
        }
    }
}
