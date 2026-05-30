FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
# COPY target/demo-0.0.1-SNAPSHOT.jar app.jar
COPY target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
