package com.kltn.livability_score.property_service.publisher;


import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class PropertyEventPublisher {

  private final StringRedisTemplate redisTemplate;
  private final ObjectMapper objectMapper; // Jackson object mapper có sẵn của Spring

  private static final String property_updates_topic = "property_updates";

  /**
   * Gửi event lên Redis
   * @param propertyId ID của BĐS
   * @param action Hành động: "created" hoặc "updated"
   */
  public void publishPropertyUpdateEvent(Long propertyId, String action) {
    try {
      // 1. Tạo payload đúng format Python mong đợi
      // Python code: property_id = data.get("property_id"), action = data.get("action")
      Map<String, Object> message = new HashMap<>();
      message.put("property_id", propertyId);
      message.put("action", action);

      // 2. Convert sang JSON String
      String jsonMessage = objectMapper.writeValueAsString(message);

      // 3. Publish lên Channel
      redisTemplate.convertAndSend(property_updates_topic, jsonMessage);

      log.info("Published Redis event to channel '{}': {}", property_updates_topic, jsonMessage);

    } catch (Exception e) {
      // Log lỗi nhưng KHÔNG throw exception để tránh làm lỗi luồng chính của API
      log.error("Failed to publish Redis event for propertyId: {}", propertyId, e);
    }
  }
}