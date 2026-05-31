FROM maven:3.9.6-eclipse-temurin-17-alpine AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests


# Stage 2: Run the application
FROM eclipse-temurin:17-jre-alpine AS prod
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

# Expose the application port
EXPOSE 8080

# Set a default fallback value if none is provided at runtime
ENV ENV_VALUE="Default Container Value"

# Run the jar file
ENTRYPOINT ["java", "-jar", "app.jar"]