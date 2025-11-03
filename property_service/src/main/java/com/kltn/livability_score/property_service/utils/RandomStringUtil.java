package com.kltn.livability_score.property_service.utils;

import java.security.SecureRandom;
import java.util.Base64;

public class RandomStringUtil {

  private static final SecureRandom secureRandom = new SecureRandom();
  private static final Base64.Encoder base64Encoder = Base64.getUrlEncoder().withoutPadding();

  /**
   * Tạo một chuỗi ngẫu nhiên an toàn cho URL.
   *
   * @param numberOfBytes Số lượng byte ngẫu nhiên cần tạo trước khi mã hóa. Số ký tự cuối cùng sẽ
   *                      lớn hơn một chút.
   * @return Một chuỗi ngẫu nhiên an toàn cho URL.
   */
  public static String generateRandomString(int numberOfBytes) {
    byte[] randomBytes = new byte[numberOfBytes];
    secureRandom.nextBytes(randomBytes);
    return base64Encoder.encodeToString(randomBytes);
  }
}
