package com.kltn.livability_score.user_service.model.sms.request;

import java.util.List;
import lombok.Data;

@Data
public class SmsSendRequest {

  private String message;
  private List<String> phoneNumbers;
}
