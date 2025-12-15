package com.kltn.livability_score.user_service.controllers;

import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.user_service.model.user.response.UserProfileResponse;
import com.kltn.livability_score.user_service.services.UserService;
import com.kltn.livability_score.user_service.utils.ResponseEntityGenerator;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal")
@RequiredArgsConstructor
public class InternalController {

  private final UserService userService;

  @GetMapping("/user/{userId}")
  public ResponseEntity<ResponseVO<UserProfileResponse>> getUserProfile(
      @PathVariable Long userId
  ) {

    UserProfileResponse response = userService.getUserProfileById(userId);
    return ResponseEntityGenerator.okFormat(response);
  }

}
