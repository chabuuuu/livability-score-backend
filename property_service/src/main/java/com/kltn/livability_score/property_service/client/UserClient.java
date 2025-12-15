package com.kltn.livability_score.property_service.client;

import com.kltn.livability_score.property_service.client.model.UserProfileResponse;
import com.kltn.livability_score.property_service.model.base_format.response.ResponseVO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient(name = "user-service", url = "${user-service.url:}")
public interface UserClient {
  @GetMapping("/internal/user/{userId}")
  ResponseVO<UserProfileResponse> getUserProfile(@PathVariable("userId") Long userId);
}