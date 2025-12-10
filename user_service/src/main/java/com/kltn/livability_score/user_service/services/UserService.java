package com.kltn.livability_score.user_service.services;

import com.kltn.livability_score.user_service.model.specifications.SearchDataDto;
import com.kltn.livability_score.user_service.model.user.request.AdminApproveSellerRequest;
import com.kltn.livability_score.user_service.model.user.request.UserLoginRequest;
import com.kltn.livability_score.user_service.model.user.request.UserProfileUpdateRequest;
import com.kltn.livability_score.user_service.model.user.request.UserRegisterRequest;
import com.kltn.livability_score.user_service.model.user.request.UserResetPasswordRequest;
import com.kltn.livability_score.user_service.model.user.request.UserVerifyEmailRequest;
import com.kltn.livability_score.user_service.model.user.response.UserGetMeResponse;
import com.kltn.livability_score.user_service.model.user.response.UserLoginResponse;
import com.kltn.livability_score.user_service.model.user.response.UserProfileResponse;
import org.springframework.data.domain.Page;

public interface UserService {

  UserGetMeResponse getMe();

  UserLoginResponse login(UserLoginRequest userLoginRequest, String clientIp);

  void register(UserRegisterRequest userRegisterRequest, String clientIp);

  void verifyEmailAndCreateUser(UserVerifyEmailRequest userVerifyEmailRequest,
      String clientIp);

  UserProfileResponse updateMyProfile(UserProfileUpdateRequest request);

  UserProfileResponse requestSellerRole();

  Page<UserProfileResponse> searchUser(SearchDataDto searchDataDto);

  UserProfileResponse getUserProfileById(Long userId);

  UserProfileResponse reviewSellerRequest(Long userId, AdminApproveSellerRequest request);

  void sentForgotPasswordOtp(String email);

  void resetPassword(UserResetPasswordRequest userResetPasswordRequest);
}
