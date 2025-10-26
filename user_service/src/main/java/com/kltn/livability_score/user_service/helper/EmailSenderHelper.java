package com.kltn.livability_score.user_service.helper;

import jakarta.mail.internet.MimeMessage;
import java.io.File;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;


@RequiredArgsConstructor
@Component
public class EmailSenderHelper {

  private final JavaMailSender emailSender;

  @Async
  public void send(MimeMessage message) {
    emailSender.send(message);
  }

  @Async
  public void sendWithAttachments(MimeMessage message, List<File> files) {
    try {
      emailSender.send(message);
    } catch (Exception e) {
      e.printStackTrace();
    } finally {
      for (File file : files) {
        file.delete(); // Xóa từng tệp tạm thời sau khi sử dụng
      }
    }
  }
}
