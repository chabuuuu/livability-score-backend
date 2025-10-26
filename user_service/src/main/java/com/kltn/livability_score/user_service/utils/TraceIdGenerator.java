package com.kltn.livability_score.user_service.utils;

public class TraceIdGenerator {

  public static String generateTraceId() {
    String traceId = RandomStringUtil.generateRandomString(23);

    return traceId;
  }
}
