package com.kltn.livability_score.property_service.utils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.util.Iterator;
import java.util.Set;
import lombok.experimental.UtilityClass;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@UtilityClass
public class JsonMaskingUtil {

  private static final ObjectMapper objectMapper = new ObjectMapper();
  private static final String MASK = "*";
  // Danh sách các key nhạy cảm cần che
  private static final Set<String> SENSITIVE_KEYS = Set.of(
      "password", "token", "authorization", "clientSecret", "apiKey", "ocp-apim-subscription-key",
      "x-api-key", "x-api-secret", "api-token", "username", "agencyCode", "access_token",
      "refresh_token"
  );

  public String mask(String jsonString) {
    if (jsonString == null || jsonString.isEmpty()) {
      return jsonString;
    }
    try {
      JsonNode rootNode = objectMapper.readTree(jsonString);
      maskNode(rootNode);
      return objectMapper.writeValueAsString(rootNode);
    } catch (Exception e) {
      log.warn("Failed to mask JSON, returning original string.", e);
      return jsonString; // Trả về chuỗi gốc nếu không parse được
    }
  }

  private void maskNode(JsonNode node) {
    if (node.isObject()) {
      ObjectNode objectNode = (ObjectNode) node;
      Iterator<String> fieldNames = objectNode.fieldNames();
      while (fieldNames.hasNext()) {
        String fieldName = fieldNames.next();
        if (SENSITIVE_KEYS.contains(fieldName.toLowerCase())) {
          objectNode.set(fieldName, new TextNode(MASK));
        } else {
          maskNode(objectNode.get(fieldName));
        }
      }
    } else if (node.isArray()) {
      for (JsonNode arrayNode : node) {
        maskNode(arrayNode);
      }
    }
  }
}