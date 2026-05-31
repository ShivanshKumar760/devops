package com.example.urlshortner.config;

import org.springframework.amqp.core.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
public class RabbitConfig{
    @Value("${app.exchange}")
    private String exchangeName;

    @Value("${app.cache-queue}")
    private String cacheQueue;

    @Value("${app.audit-queue}")
    private String auditQueue;

    @Bean
    public FanoutExchange urlExchange(){
        return new FanoutExchange(exchangeName, true , false );
    }

    @Bean
    public Queue cacheQ(){
        return QueueBuilder.durable(cacheQueue).build();
    }

    @Bean
    public Queue auditQ(){
        return QueueBuilder.durable(auditQueue).build();
    }

    @Bean 
    public Binding cacheBinding(Queue cacheQ , FanoutExchange urlExchange){
        return BindingBuilder.bind(cacheQ).to(urlExchange);
    }

    @Bean
    public Binding auditBinding(Queue auditQ, FanoutExchange urlExchange) {
        return BindingBuilder.bind(auditQ).to(urlExchange);
    }
}   
