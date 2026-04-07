pluginManagement {
    repositories {
        maven { url = uri("https://repo.maven.apache.org/maven2") }
        gradlePluginPortal()
        mavenCentral()
    }
}

plugins {
    id("org.springframework.boot") version "3.2.0"
    id("io.spring.dependency-management") version "1.1.4"
    kotlin("jvm") version "1.9.20"
    kotlin("plugin.spring") version "1.9.20"
    kotlin("plugin.jpa") version "1.9.20"
}

group = "com.trading"
version = "1.0.0"
java.sourceCompatibility = JavaVersion.VERSION_17

repositories {
    mavenCentral()
}

dependencies {
    // Spring Boot
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    
    // Kafka
    implementation("org.springframework.kafka:spring-kafka")
    
    // Redis
    implementation("org.springframework.boot:spring-boot-starter-data-redis")
    
    // WebSocket for real-time
    implementation("org.springframework.boot:spring-boot-starter-websocket")
    
    // PostgreSQL
    runtimeOnly("org.postgresql:postgresql")
    
    // Jackson for JSON
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")
    
    // Lombok
    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")
    
    // Swagger/OpenAPI
    implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.2.0")
    
    // HTTP Client
    implementation("org.springframework.boot:spring-boot-starter-webflux")
    
    // Binance Connector Java
    implementation("com.binance.connector:binance-connector-java:3.5.0")
    
    // JSON parsing
    implementation("org.json:json:20231013")
    
    // OkHttp for HTTP requests
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    
    // Monitoring
    implementation("io.micrometer:micrometer-registry-prometheus")
    
    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.kafka:spring-kafka-test")
    
    // Kotlin
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
