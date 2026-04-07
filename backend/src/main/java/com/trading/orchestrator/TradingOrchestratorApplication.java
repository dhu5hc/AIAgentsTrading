package com.trading.orchestrator;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableKafka
@EnableScheduling
public class TradingOrchestratorApplication {

    public static void main(String[] args) {
        SpringApplication.run(TradingOrchestratorApplication.class, args);
        System.out.println("🤖 AI Trading Orchestrator Started!");
    }
}
