package com.kltn.livability_score.user_service.services;

import com.kltn.livability_score.user_service.model.sms.request.SmsSendRequest;

public interface SmsService {

  void sendSms(SmsSendRequest smsSendRequest);
  
}
