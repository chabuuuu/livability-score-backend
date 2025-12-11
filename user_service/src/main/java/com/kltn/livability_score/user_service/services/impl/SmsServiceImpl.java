package com.kltn.livability_score.user_service.services.impl;

import com.kltn.livability_score.user_service.model.sms.request.SmsSendRequest;
import com.kltn.livability_score.user_service.services.SmsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@RequiredArgsConstructor
@Slf4j
@Service
public class SmsServiceImpl implements SmsService {

  private static String SMS_GATEWAY_USERNAME = System.getenv("SMS_GATEWAY_USERNAME");
  private static String SMS_GATEWAY_PASSWORD = System.getenv("SMS_GATEWAY_PASSWORD");
  private static String SMS_GATEWAY_URL = System.getenv("SMS_GATEWAY_URL");
  private final RestTemplate restTemplate;

  @Override
  public void sendSms(SmsSendRequest smsSendRequest) {
    try {
      // 1. Tạo Header với Basic Auth
      HttpHeaders headers = new HttpHeaders();
      headers.setContentType(MediaType.APPLICATION_JSON);
      headers.setBasicAuth(SMS_GATEWAY_USERNAME, SMS_GATEWAY_PASSWORD);

      HttpEntity<SmsSendRequest> request = new HttpEntity<>(smsSendRequest, headers);

      // 4. Gửi Request
      restTemplate.postForObject(SMS_GATEWAY_URL, request, String.class);

      log.info("SMS sent to {} successfully", smsSendRequest.getPhoneNumbers());

    } catch (Exception e) {
      log.error("Failed to send SMS to {}: {}", smsSendRequest.getPhoneNumbers(), e.getMessage());
      // Tùy logic, có thể throw Exception để Controller bắt
      throw new RuntimeException("SMS_SEND_FAILED");
    }
  }
  
}
