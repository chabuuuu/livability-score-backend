package com.kltn.livability_score.user_service.utils;

import java.security.SecureRandom;

public class OtpUtil {

  private static final SecureRandom random = new SecureRandom();
  private static final int OTP_LENGTH = 6;

  public static String generateOtp() {
    StringBuilder otp = new StringBuilder(OTP_LENGTH);
    for (int i = 0; i < OTP_LENGTH; i++) {
      otp.append(random.nextInt(10)); // Append a random digit (0-9)
    }
    return otp.toString();
  }
}
