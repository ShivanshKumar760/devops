package com.example.urlshortner.worker;

import com.example.urlshortner.model.UrlEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Cache Worker
 * Listens on cache_q and keeps an in-memory map of short_code -> originalUrl.
 * Replaces Redis with a plain ConcurrentHashMap for single-digit-ms lookups.
 */
@Slf4j
@Component
public class CacheWorker {

    // In-memory cache: shortCode -> CacheEntry
    private final Map<String, CacheEntry> cache = new ConcurrentHashMap<>();

    record CacheEntry(String url, AtomicLong hits, long cachedAt) {}

    @RabbitListener(queues = "${app.cache-queue}")
    public void handleEvent(UrlEvent event) {
        if (event == null || event.getType() == null) return;

        switch (event.getType()) {
            case "URL_CREATED" -> {
                cache.put(event.getShortCode(),
                    new CacheEntry(event.getOriginalUrl(), new AtomicLong(0), System.currentTimeMillis()));
                log.info("[Cache] SET  {} -> {}", event.getShortCode(), event.getOriginalUrl());
            }
            case "URL_VISITED" -> {
                CacheEntry entry = cache.get(event.getShortCode());
                if (entry != null) {
                    long hits = entry.hits().incrementAndGet();
                    log.info("[Cache] HIT  {} | total hits: {}", event.getShortCode(), hits);
                }
            }
            default -> log.debug("[Cache] Unknown event type: {}", event.getType());
        }
    }

    /** Exposed for potential REST inspection (optional). */
    public Map<String, CacheEntry> getCache() {
        return Map.copyOf(cache);
    }
}