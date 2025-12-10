package com.kltn.livability_score.user_service.controllers;

import com.kltn.livability_score.user_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.user_service.exception.user.UserForgotPasswordException;
import com.kltn.livability_score.user_service.exception.user.UserLoginException;
import com.kltn.livability_score.user_service.exception.user.UserProfileException;
import com.kltn.livability_score.user_service.exception.user.UserRegisterException;
import com.kltn.livability_score.user_service.exception.user.UserRoleException;
import com.kltn.livability_score.user_service.exception.user.UserVerifyEmailException;
import com.kltn.livability_score.user_service.model.base_format.response.ResponsePagingVO;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;
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
import com.kltn.livability_score.user_service.services.UserService;
import com.kltn.livability_score.user_service.utils.GetClientIp;
import com.kltn.livability_score.user_service.utils.ResponseEntityGenerator;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/user")
@RequiredArgsConstructor
@Tag(name = "User Management", description = "Quản lý người dùng")
public class UserController {

  private final UserService userService;

  @PostMapping("/login")
  @Operation(summary = "Login")
  @ApiErrorResponse(errorEnum = UserLoginException.class, validateSchema = UserLoginRequest.class)
  public ResponseEntity<ResponseVO<UserLoginResponse>> login(
      @Valid @RequestBody UserLoginRequest userLoginRequest,
      HttpServletRequest request
  ) {

    String clientIp = GetClientIp.get(request);

    UserLoginResponse userLoginResponse = userService.login(userLoginRequest, clientIp);

    return ResponseEntityGenerator.okFormat(userLoginResponse);
  }

  @Operation(summary = "Get me")
  @GetMapping("/me")
  public ResponseEntity<ResponseVO<UserGetMeResponse>> getMe() {

    UserGetMeResponse userGetMeResponse = userService.getMe();

    return ResponseEntityGenerator.okFormat(userGetMeResponse);
  }

  @PutMapping("/update/me")
  @Operation(summary = "Update my user profile")
  @ApiErrorResponse(errorEnum = UserProfileException.class)
  public ResponseEntity<ResponseVO<UserProfileResponse>> updateMyProfile(
      @Valid @RequestBody UserProfileUpdateRequest request) {

    UserProfileResponse response = userService.updateMyProfile(request);
    return ResponseEntityGenerator.okFormat(response);
  }

  @PostMapping("/register")
  @Operation(summary = "Register user")
  @ApiErrorResponse(errorEnum = UserRegisterException.class, validateSchema = UserRegisterRequest.class)
  public ResponseEntity<ResponseVO<String>> register(
      @Valid @RequestBody UserRegisterRequest userRegisterRequest,
      HttpServletRequest request
  ) {

    String clientIp = GetClientIp.get(request);

    userService.register(userRegisterRequest, clientIp);

    return ResponseEntityGenerator.okFormat(
        "Register user successfully. Please check email to verify account");
  }

  @PostMapping("/register/verify-email")
  @Operation(summary = "Verify email to register user")
  @ApiErrorResponse(errorEnum = UserVerifyEmailException.class, validateSchema = UserVerifyEmailRequest.class)
  public ResponseEntity<ResponseVO<String>> verifyEmailAndCreate(
      @Valid @RequestBody UserVerifyEmailRequest userVerifyEmailRequest,
      HttpServletRequest request
  ) {

    String clientIp = GetClientIp.get(request);

    userService.verifyEmailAndCreateUser(userVerifyEmailRequest, clientIp);

    return ResponseEntityGenerator.okFormat(
        "Verify email and create user successfully. You can login now");
  }

  @PostMapping("/request-seller-role")
  @Operation(summary = "Request to become a seller")
  @ApiErrorResponse(errorEnum = UserRoleException.class)
  public ResponseEntity<ResponseVO<UserProfileResponse>> requestSellerRole() {

    UserProfileResponse response = userService.requestSellerRole();
    return ResponseEntityGenerator.okFormat(response);
  }

  @PreAuthorize("hasAuthority('ADMIN')")
  @PostMapping("/search")
  @Operation(summary = "Search for users (Admin)")
  public ResponseEntity<ResponsePagingVO<UserProfileResponse>> searchUsers(
      @RequestBody SearchDataDto searchDataDto) {

    Page<UserProfileResponse> result = userService.searchUser(searchDataDto);

    return ResponseEntityGenerator.searchFormat(result, searchDataDto);
  }

  @PreAuthorize("hasAuthority('ADMIN')")
  @GetMapping("/{userId}")
  @Operation(summary = "Get user profile details by ID (Admin)")
  @ApiErrorResponse(errorEnum = UserProfileException.class)
  public ResponseEntity<ResponseVO<UserProfileResponse>> getUserProfile(
      @PathVariable Long userId) {

    UserProfileResponse response = userService.getUserProfileById(userId);
    return ResponseEntityGenerator.okFormat(response);
  }

  @PreAuthorize("hasAuthority('ADMIN')")
  @PostMapping("/{userId}/review-seller")
  @Operation(summary = "Approve or reject a seller request (Admin)")
  @ApiErrorResponse(errorEnum = UserRoleException.class)
  public ResponseEntity<ResponseVO<UserProfileResponse>> reviewSellerRequest(
      @PathVariable Long userId,
      @Valid @RequestBody AdminApproveSellerRequest request) {

    UserProfileResponse response = userService.reviewSellerRequest(userId, request);
    return ResponseEntityGenerator.okFormat(response);
  }

  @PostMapping("/forgot-password/{email}")
  @Operation(summary = "User forgot password - send OTP to email")
  @ApiErrorResponse(errorEnum = UserForgotPasswordException.class)
  public ResponseEntity<ResponseVO<String>> sendForgotPasswordOtp(
      @PathVariable String email) {

    userService.sentForgotPasswordOtp(email);

    return ResponseEntityGenerator.okFormat("OTP sent to email successfully");
  }

  @PostMapping("/forgot-password/verify")
  @Operation(summary = "User forgot password - verify OTP and reset password")
  @ApiErrorResponse(errorEnum = UserForgotPasswordException.class, validateSchema = UserResetPasswordRequest.class)
  public ResponseEntity<ResponseVO<String>> verifyAndResetPassword(
      @Valid @RequestBody UserResetPasswordRequest userResetPasswordRequest
  ) {

    userService.resetPassword(userResetPasswordRequest);

    return ResponseEntityGenerator.okFormat("Password reset successfully");
  }
}
