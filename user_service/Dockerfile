FROM eclipse-temurin:21-jdk-jammy AS build
ENV HOME=/usr/app
RUN mkdir -p $HOME
WORKDIR $HOME
ADD . $HOME

# Install Maven
RUN apt-get update && apt-get install -y maven

# Build the Spring Boot app using Maven
RUN mvn clean
RUN mvn package -DskipTests=true

FROM eclipse-temurin:21-jdk-jammy

ARG JAR_FILE=/usr/app/target/*.jar

VOLUME /tmp

# Cài đặt curl để health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=build $JAR_FILE app.jar


#ADD $JAR_FILE app.jar
ENTRYPOINT exec java -jar /app.jar
EXPOSE 8080