package com.kltn.livability_score.user_service.services;

import com.kltn.livability_score.user_service.model.user.request.UserLoginRequest;
import com.kltn.livability_score.user_service.model.user.request.UserRegisterRequest;
import com.kltn.livability_score.user_service.model.user.request.UserVerifyEmailRequest;
import com.kltn.livability_score.user_service.model.user.response.UserGetMeResponse;
import com.kltn.livability_score.user_service.model.user.response.UserLoginResponse;

public interface UserService {

  UserGetMeResponse getMe();

  UserLoginResponse login(UserLoginRequest userLoginRequest, String clientIp);

  void register(UserRegisterRequest userRegisterRequest, String clientIp);

  void verifyEmailAndCreateUser(UserVerifyEmailRequest userVerifyEmailRequest,
      String clientIp);
}
