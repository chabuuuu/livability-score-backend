package com.kltn.livability_score.user_service.utils;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordUtil {
    final static BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);

    public static String hashPassword(String password) {
        // Hash password
        String hashedPassword = PasswordUtil.encoder.encode(password);

        return hashedPassword;
    }

    public static boolean checkPassword(String password, String hashedPassword) {
        return encoder.matches(password, hashedPassword);
    }
}
