package com.example.urlshortner.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UrlEvent {

    private String type;           // URL_CREATED | URL_VISITED

    @JsonProperty("short_code")
    private String shortCode;

    @JsonProperty("original_url")
    private String originalUrl;

    private String ip;

    @JsonProperty("user_agent")
    private String userAgent;

    private String timestamp;
}