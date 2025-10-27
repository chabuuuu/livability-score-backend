package com.kltn.livability_score.property_service.utils;

public class TraceIdGenerator {

  public static String generateTraceId() {
    String traceId = RandomStringUtil.generateRandomString(23);

    return traceId;
  }
}
