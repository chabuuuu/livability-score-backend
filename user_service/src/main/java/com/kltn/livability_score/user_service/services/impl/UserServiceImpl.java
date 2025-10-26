package com.kltn.livability_score.user_service.services.impl;

import com.kltn.livability_score.user_service.entity.UserEntity;
import com.kltn.livability_score.user_service.entity.UserProfileEntity;
import com.kltn.livability_score.user_service.entity.caching.RegisterUserCacheEntity;
import com.kltn.livability_score.user_service.enums.RoleTypeEnum;
import com.kltn.livability_score.user_service.exception.GeneralErrorCode;
import com.kltn.livability_score.user_service.exception.handler.BaseError;
import com.kltn.livability_score.user_service.exception.user.UserLoginException;
import com.kltn.livability_score.user_service.exception.user.UserRegisterException;
import com.kltn.livability_score.user_service.exception.user.UserVerifyEmailException;
import com.kltn.livability_score.user_service.mapper.UserMapper;
import com.kltn.livability_score.user_service.model.jwt.vo.JwtTokenVo;
import com.kltn.livability_score.user_service.model.user.request.UserLoginRequest;
import com.kltn.livability_score.user_service.model.user.request.UserRegisterRequest;
import com.kltn.livability_score.user_service.model.user.request.UserVerifyEmailRequest;
import com.kltn.livability_score.user_service.model.user.response.UserGetMeResponse;
import com.kltn.livability_score.user_service.model.user.response.UserLoginResponse;
import com.kltn.livability_score.user_service.repository.UserRepository;
import com.kltn.livability_score.user_service.repository.caching.RegisterUserCacheRepository;
import com.kltn.livability_score.user_service.services.EmailService;
import com.kltn.livability_score.user_service.services.UserService;
import com.kltn.livability_score.user_service.utils.OtpUtil;
import com.kltn.livability_score.user_service.utils.PasswordUtil;
import com.kltn.livability_score.user_service.utils.SecurityUtil;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;


@Service
@AllArgsConstructor
public class UserServiceImpl implements UserService {

  private final UserRepository userRepository;
  private final UserMapper userMapper;
  private final RegisterUserCacheRepository registerUserCacheRepository;
  private final EmailService emailService;


  @SneakyThrows
  @Override
  public UserGetMeResponse getMe() {
    JwtTokenVo jwtTokenVo = SecurityUtil.getSession();
    Long shopperId = jwtTokenVo.getUserId();

    UserEntity user = userRepository.findByIdAndDeleteAtIsNull(shopperId)
        .orElse(null);

    if (user == null) {
      throw new BaseError(GeneralErrorCode.GNR_UNAUTHORIZED);
    }

    // Map to response
    UserGetMeResponse userGetMeResponse = userMapper.toUserGetMeResponse(user);
    userGetMeResponse.setFullName(user.getUserProfile().getFullName());
    userGetMeResponse.setPhoneNumber(user.getUserProfile().getPhoneNumber());
    userGetMeResponse.setPreferenceType(user.getUserProfile().getPreferenceType());
    userGetMeResponse.setAvatarUrl(user.getUserProfile().getAvatarUrl());

    return userGetMeResponse;
  }

  @SneakyThrows
  @Override
  public UserLoginResponse login(UserLoginRequest userLoginRequest, String clientIp) {
    String email = userLoginRequest.getEmail();
    String password = userLoginRequest.getPassword();

    // Check if this user with this username exists
    UserEntity user = userRepository.findByEmailAndDeleteAtIsNull(email)
        .orElse(null);

    if (user == null) {
      throw new BaseError(UserLoginException.USER_LOGIN_Invalid);
    }

    // Check if the password is correct
    if (!PasswordUtil.checkPassword(password, user.getPasswordHash())) {
      throw new BaseError(UserLoginException.USER_LOGIN_Invalid);
    }

    JwtTokenVo jwtTokenVo = new JwtTokenVo(
        user.getId(),
        List.of(RoleTypeEnum.USER.toString()), null, clientIp);

    String accessToken = SecurityUtil.createToken(jwtTokenVo);

    UserLoginResponse userLoginResponse = new UserLoginResponse();
    userLoginResponse.setToken(accessToken);

    return userLoginResponse;
  }

  @SneakyThrows
  @Override
  public void register(UserRegisterRequest userRegisterRequest, String clientIp) {
    // Kiểm tra xem có tồn tại username này hay không
    if (userRepository.existsByEmailAndDeleteAtIsNull((
        userRegisterRequest.getEmail()))) {
      throw new BaseError(UserRegisterException.USER_REGISTES_UserAlreadyExist);
    }

    // Check xem otp trong cache đã hết hạn chưa
    RegisterUserCacheEntity existsOtp = registerUserCacheRepository.findById(
            userRegisterRequest.getEmail())
        .orElse(null);
    if (existsOtp != null) {
      throw new BaseError(UserRegisterException.USER_REGISTER_CoolDown);
    }

    // Hash password
    String hashedPassword = PasswordUtil.hashPassword(userRegisterRequest.getPassword());
    userRegisterRequest.setPassword(hashedPassword);

    RegisterUserCacheEntity registerUserCacheEntity = new RegisterUserCacheEntity();
    registerUserCacheEntity.setUserRegisterRequest(userRegisterRequest);
    registerUserCacheEntity.setEmail(userRegisterRequest.getEmail());
    registerUserCacheEntity.setClientIp(clientIp);

    // Generate session id with UUID
    String otp = OtpUtil.generateOtp();

    registerUserCacheEntity.setOtp(otp);

    // Lưu vào cache để chờ được verify
    registerUserCacheRepository.save(registerUserCacheEntity);

    // Gửi email đến user
    String recipientName = userRegisterRequest.getFullName();

    emailService.sendRegisterAccountOtpEmail(userRegisterRequest.getEmail(), recipientName, otp);
  }

  @SneakyThrows
  @Override
  public void verifyEmailAndCreateUser(UserVerifyEmailRequest userVerifyEmailRequest,
      String clientIp) {
    String email = userVerifyEmailRequest.getEmail();
    String otp = userVerifyEmailRequest.getOtp();

    RegisterUserCacheEntity registerUserCacheEntity = registerUserCacheRepository.findById(
            email)
        .orElse(null);
    if (registerUserCacheEntity == null) {
      throw new BaseError(UserVerifyEmailException.USER_VERIFY_EMAIL_InvalidOtp);
    }

    // So sánh otp nhập vào với otp trong cache
    if (!otp.equals(registerUserCacheEntity.getOtp())) {
      throw new BaseError(UserVerifyEmailException.USER_VERIFY_EMAIL_InvalidOtp);
    }

    UserRegisterRequest userRegisterRequest = registerUserCacheEntity.getUserRegisterRequest();

    UserEntity user = createUser(userRegisterRequest);

    // Delete otp in cache
    registerUserCacheRepository.deleteById(email);
  }

  @SneakyThrows
  private UserEntity createUser(UserRegisterRequest userRegisterRequest
  ) {

    UserEntity user = new UserEntity();
    user.setEmail(userRegisterRequest.getEmail());

    UserProfileEntity userProfileEntity = new UserProfileEntity();

    userProfileEntity.setFullName(userRegisterRequest.getFullName());
    userProfileEntity.setPhoneNumber(userRegisterRequest.getPhoneNumber());
    userProfileEntity.setPreferenceType(userRegisterRequest.getPreferenceType());
    userProfileEntity.setUser(user);

    user.setPasswordHash(userRegisterRequest.getPassword());
    user.setUserProfile(userProfileEntity);

    return userRepository.save(user);
  }
}
