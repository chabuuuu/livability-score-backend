package com.kltn.livability_score.user_service.controllers;

import com.kltn.livability_score.user_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.user_service.exception.user.UserLoginException;
import com.kltn.livability_score.user_service.exception.user.UserRegisterException;
import com.kltn.livability_score.user_service.exception.user.UserVerifyEmailException;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.user_service.model.user.request.UserLoginRequest;
import com.kltn.livability_score.user_service.model.user.request.UserRegisterRequest;
import com.kltn.livability_score.user_service.model.user.request.UserVerifyEmailRequest;
import com.kltn.livability_score.user_service.model.user.response.UserGetMeResponse;
import com.kltn.livability_score.user_service.model.user.response.UserLoginResponse;
import com.kltn.livability_score.user_service.services.UserService;
import com.kltn.livability_score.user_service.utils.GetClientIp;
import com.kltn.livability_score.user_service.utils.ResponseEntityGenerator;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
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

  @PreAuthorize("hasAuthority('USER')")
  @Operation(summary = "Get me")
  @GetMapping("/me")
  public ResponseEntity<ResponseVO<UserGetMeResponse>> getMe() {

    UserGetMeResponse userGetMeResponse = userService.getMe();

    return ResponseEntityGenerator.okFormat(userGetMeResponse);
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
}
