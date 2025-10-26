package com.kltn.livability_score.user_service.services;

import java.io.File;
import java.util.List;

public interface EmailService {

  void sendSimpleMessage(String to, String subject, String text);

  void sendEmailWithAttachments(String to, String subject, String text, List<File> files,
      Boolean isHtmlContent);

  void sendRegisterAccountOtpEmail(String to, String recipientName, String otp);

  void sendForgotPasswordOtpEmail(String to, String recipientName, String otp);
}
