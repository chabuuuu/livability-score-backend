package com.kltn.livability_score.user_service.entity.caching;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.redis.core.RedisHash;
import org.springframework.stereotype.Component;

@Component
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@RedisHash(value = "VerifyPhoneCache", timeToLive = 900) // 15 minutes
public class VerifyPhoneCacheEntity {

  @Id
  private String phoneNumber;
  private String otp;
}
