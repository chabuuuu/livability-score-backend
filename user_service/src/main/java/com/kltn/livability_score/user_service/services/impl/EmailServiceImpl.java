package com.kltn.livability_score.user_service.services.impl;

import com.kltn.livability_score.user_service.helper.EmailSenderHelper;
import com.kltn.livability_score.user_service.services.EmailService;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import java.io.File;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailServiceImpl implements EmailService {

  private static String BUSINESS_NAME = "TimNha.com";
  private final JavaMailSender emailSender;
  private final String EMAIL_USERNAME = System.getenv("EMAIL_USERNAME");
  private final EmailSenderHelper emailSenderHelper;

  public void sendSimpleMessage(String to, String subject, String text) {
    String businessName = BUSINESS_NAME;
    // SimpleMailMessage message = new SimpleMailMessage();
    MimeMessage message = emailSender.createMimeMessage();
    try {
      MimeMessageHelper helper = new MimeMessageHelper(message, "utf-8");
      helper.setTo(to);
      helper.setSubject(subject);
      helper.setText(text);

      // Set the sender of the email to the business name
      helper.setFrom(new InternetAddress(EMAIL_USERNAME, businessName, "UTF-8"));
      emailSenderHelper.send(message);
    } catch (Exception e) {
      log.error(e.getMessage());
    }

  }

  public void sendHtmlMessage(String to, String subject, String htmlContent) {
    String businessName = BUSINESS_NAME;
    // SimpleMailMessage message = new SimpleMailMessage();
    MimeMessage message = emailSender.createMimeMessage();
    try {
      MimeMessageHelper helper = new MimeMessageHelper(message, "utf-8");
      helper.setTo(to);
      helper.setSubject(subject);
      helper.setText(htmlContent, true);

      // Set the sender of the email to the business name
      helper.setFrom(new InternetAddress(EMAIL_USERNAME, businessName, "UTF-8"));
      emailSenderHelper.send(message);
    } catch (Exception e) {
      log.error(e.getMessage());
    }
  }

  public void sendEmailWithAttachments(String to, String subject, String text, List<File> files,
      Boolean isHtmlContent) {
    MimeMessage message = emailSender.createMimeMessage();
    MimeMessageHelper helper;
    try {
      helper = new MimeMessageHelper(message, true);
      helper.setTo(to);
      helper.setSubject(subject);
      helper.setText(text, isHtmlContent);

      // Set the sender of the email to the business name
      String businessName = BUSINESS_NAME;
      helper.setFrom(new InternetAddress(EMAIL_USERNAME, businessName, "UTF-8"));

      for (File file : files) {
        FileSystemResource fileResource = new FileSystemResource(file);
        helper.addAttachment(file.getName(), fileResource);
      }

      // Send email with attachments (also delete the temporary files after sending)
      emailSenderHelper.sendWithAttachments(message, files);
    } catch (Exception e) {
      log.error(e.getMessage());
    }
  }

  @SneakyThrows
  @Override
  public void sendRegisterAccountOtpEmail(String to, String recipientName, String otp) {
    String businessName = BUSINESS_NAME;

    String emailSubject = "Xác thực danh tính tài khoản để sử dụng dịch vụ của " + businessName;

    String text = "Mã OTP của bạn là: " + otp + ". Mã này có hiệu lực trong 15 phút.";

    sendSimpleMessage(to, emailSubject, text);
  }

  @Override
  public void sendForgotPasswordOtpEmail(String to, String recipientName, String otp) {
    String businessName = BUSINESS_NAME;

    String emailSubject = "Xác thực OTP để khôi phục tài khoản của dịch vụ " + businessName;

    String text = "Mã OTP của bạn là: " + otp + ". Mã này có hiệu lực trong 15 phút.";

    sendSimpleMessage(to, emailSubject, text);
  }
}
