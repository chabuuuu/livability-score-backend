package com.kltn.livability_score.user_service.utils;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Arrays;
import java.util.List;
import org.springframework.security.web.util.matcher.IpAddressMatcher;

public class GetClientIp {
  // Danh sách các dải IP nội bộ và private theo chuẩn RFC 1918 và loopback
  private static final List<String> LOCAL_IP_RANGES = Arrays.asList(
      "127.0.0.1/32",      // Loopback IPv4
      "::1/128",           // Loopback IPv6
      "10.0.0.0/8",        // Private network
      "172.16.0.0/12",     // Private network (Docker's default often falls here)
      "192.168.0.0/16"     // Private network
  );

  public static boolean isLocalOrInternal(String ipAddress) {
    if (ipAddress == null) {
      return false;
    }

    for (String range : LOCAL_IP_RANGES) {
      IpAddressMatcher matcher = new IpAddressMatcher(range);
      if (matcher.matches(ipAddress)) {
        return true;
      }
    }
    return false;
  }

  public static String get(HttpServletRequest request) {
    String ip = request.getHeader("X-Forwarded-For");
    if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
      ip = request.getRemoteAddr();
    }

    return ip;
  }
}
