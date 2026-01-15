package com.kltn.livability_score.user_service.services.impl;

import com.kltn.livability_score.user_service.entity.PreferencePresetEntity;
import com.kltn.livability_score.user_service.entity.PresetAdaptationLogEntity;
import com.kltn.livability_score.user_service.entity.UserEntity;
import com.kltn.livability_score.user_service.entity.UserProfileEntity;
import com.kltn.livability_score.user_service.entity.caching.ForgotPasswordCacheEntity;
import com.kltn.livability_score.user_service.entity.caching.RegisterUserCacheEntity;
import com.kltn.livability_score.user_service.entity.caching.VerifyPhoneCacheEntity;
import com.kltn.livability_score.user_service.enums.RoleTypeEnum;
import com.kltn.livability_score.user_service.enums.SellerApprovalStatus;
import com.kltn.livability_score.user_service.exception.GeneralErrorCode;
import com.kltn.livability_score.user_service.exception.handler.BaseError;
import com.kltn.livability_score.user_service.exception.user.UserForgotPasswordException;
import com.kltn.livability_score.user_service.exception.user.UserLoginException;
import com.kltn.livability_score.user_service.exception.user.UserProfileException;
import com.kltn.livability_score.user_service.exception.user.UserRegisterException;
import com.kltn.livability_score.user_service.exception.user.UserRoleException;
import com.kltn.livability_score.user_service.exception.user.UserVerifyEmailException;
import com.kltn.livability_score.user_service.exception.user.UserVerifyPhoneException;
import com.kltn.livability_score.user_service.mapper.UserMapper;
import com.kltn.livability_score.user_service.mapper.UserProfileMapper;
import com.kltn.livability_score.user_service.model.jwt.vo.JwtTokenVo;
import com.kltn.livability_score.user_service.model.sms.request.SmsSendRequest;
import com.kltn.livability_score.user_service.model.specifications.SearchDataDto;
import com.kltn.livability_score.user_service.model.user.request.AdminApproveSellerRequest;
import com.kltn.livability_score.user_service.model.user.request.UserChangePasswordRequest;
import com.kltn.livability_score.user_service.model.user.request.UserLoginRequest;
import com.kltn.livability_score.user_service.model.user.request.UserProfileUpdateRequest;
import com.kltn.livability_score.user_service.model.user.request.UserRegisterRequest;
import com.kltn.livability_score.user_service.model.user.request.UserResetPasswordRequest;
import com.kltn.livability_score.user_service.model.user.request.UserSendOtpVerifyPhoneRequest;
import com.kltn.livability_score.user_service.model.user.request.UserVerifyEmailRequest;
import com.kltn.livability_score.user_service.model.user.request.UserVerifyPhoneRequest;
import com.kltn.livability_score.user_service.model.user.response.UserGetMeResponse;
import com.kltn.livability_score.user_service.model.user.response.UserLoginResponse;
import com.kltn.livability_score.user_service.model.user.response.UserProfileResponse;
import com.kltn.livability_score.user_service.repository.PreferencePresetRepository;
import com.kltn.livability_score.user_service.repository.PresetAdaptationLogRepository;
import com.kltn.livability_score.user_service.repository.UserProfileRepository;
import com.kltn.livability_score.user_service.repository.UserRepository;
import com.kltn.livability_score.user_service.repository.caching.ForgotPasswordCacheRepository;
import com.kltn.livability_score.user_service.repository.caching.RegisterUserCacheRepository;
import com.kltn.livability_score.user_service.repository.caching.VerifyPhoneCacheRepository;
import com.kltn.livability_score.user_service.services.EmailService;
import com.kltn.livability_score.user_service.services.SmsService;
import com.kltn.livability_score.user_service.services.UserService;
import com.kltn.livability_score.user_service.utils.OtpUtil;
import com.kltn.livability_score.user_service.utils.PasswordUtil;
import com.kltn.livability_score.user_service.utils.SearchUtil;
import com.kltn.livability_score.user_service.utils.SecurityUtil;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


@Service
@AllArgsConstructor
public class UserServiceImpl implements UserService {

  private final UserRepository userRepository;
  private final UserMapper userMapper;
  private final RegisterUserCacheRepository registerUserCacheRepository;
  private final EmailService emailService;
  private final UserProfileMapper userProfileMapper;
  private final UserProfileRepository userProfileRepository;
  private final PreferencePresetRepository presetRepository;
  private final ForgotPasswordCacheRepository forgotPasswordCacheRepository;
  private final VerifyPhoneCacheRepository verifyPhoneCacheRepository;
  private final SmsService smsService;
  private final PresetAdaptationLogRepository presetAdaptationLogRepository;

  @Override
  @Transactional(readOnly = true)
  public UserProfileResponse getUserProfileById(Long userId) {
    // findById() đã tự động xử lý soft-delete (nhờ @Where)
    UserProfileEntity profile = userProfileRepository.findById(userId)
        .orElseThrow(() -> new BaseError(UserProfileException.PROFILE_NOT_FOUND));

    return userProfileMapper.toResponse(profile);
  }

  @Override
  @Transactional // Rất quan trọng vì chúng ta sửa 2 Bảng (users và user_profiles)
  public UserProfileResponse reviewSellerRequest(Long userId, AdminApproveSellerRequest request) {
    SellerApprovalStatus decision = request.getStatus();

    // 1. Validate quyết định của admin
    if (decision == SellerApprovalStatus.PENDING || decision == SellerApprovalStatus.NONE) {
      throw new BaseError(UserRoleException.INVALID_APPROVAL_DECISION);
    }

    // 2. Tìm cả User và UserProfile
    UserEntity user = userRepository.findById(userId)
        .orElseThrow(() -> new BaseError(UserRoleException.USER_NOT_FOUND));

    UserProfileEntity profile = userProfileRepository.findById(userId)
        .orElseThrow(() -> new BaseError(UserProfileException.PROFILE_NOT_FOUND));

    // 3. Kiểm tra trạng thái hiện tại của request
    if (profile.getBecomeSellerApproveStatus() != SellerApprovalStatus.PENDING) {
      throw new BaseError(UserRoleException.REQUEST_NOT_PENDING);
    }

    // 4. Xử lý logic duyệt
    if (decision == SellerApprovalStatus.APPROVED) {
      // Cập nhật trạng thái profile
      profile.setBecomeSellerApproveStatus(SellerApprovalStatus.APPROVED);

      // Thêm role mới cho User
      List<String> roles = user.getRoles();
      if (!roles.contains(RoleTypeEnum.SELLER.toString())) {
        roles.add(RoleTypeEnum.SELLER.toString());
        user.setRoles(roles);
        userRepository.save(user); // Lưu entity User
      }
    } else { // Quyết định là REJECTED
      profile.setBecomeSellerApproveStatus(SellerApprovalStatus.REJECTED);
      // (Bạn cũng có thể set về NONE để cho phép họ yêu cầu lại sau)

      // Gửi mail từ chối với lý do
      String rejectReason = request.getRejectReason();
      emailService.sendSimpleMessage(user.getEmail(), "Yêu cầu trở thành người bán bị từ chối",
          rejectReason);
    }

    // 5. Lưu entity Profile và trả về
    UserProfileEntity savedProfile = userProfileRepository.save(profile); // Lưu entity UserProfile
    return userProfileMapper.toResponse(savedProfile);
  }

  @Override
  public void sentForgotPasswordOtp(String email) {
    // Check xem otp trong cache đã hết hạn chưa
    ForgotPasswordCacheEntity existsOtp = forgotPasswordCacheRepository.findById(email)
        .orElse(null);
    if (existsOtp != null) {
      throw new BaseError(UserForgotPasswordException.USER_FORGOT_PASSWORD_CoolDown);
    }

    // Get the user from DB
    UserEntity user = userRepository.findByEmailAndDeleteAtIsNull(email)
        .orElseThrow(
            () -> new BaseError(UserForgotPasswordException.USER_FORGOT_PASSWORD_UserNotFound));

    // Generate session id with UUID
    String otp = OtpUtil.generateOtp();

    ForgotPasswordCacheEntity forgotPasswordCacheEntity = new ForgotPasswordCacheEntity();
    forgotPasswordCacheEntity.setOtp(otp);
    forgotPasswordCacheEntity.setEmail(email);

    // Lưu vào cache để chờ được verify
    forgotPasswordCacheRepository.save(forgotPasswordCacheEntity);

    // Gửi email đến user
    String recipientName = user.getUserProfile().getFullName();

    emailService.sendForgotPasswordOtpEmail(email, recipientName, otp);
  }

  @Override
  public void resetPassword(UserResetPasswordRequest userResetPasswordRequest) {

    // Lấy OTP từ cache
    ForgotPasswordCacheEntity forgotPasswordCacheEntity = forgotPasswordCacheRepository.findById(
            userResetPasswordRequest.getEmail())
        .orElse(null);
    if (forgotPasswordCacheEntity == null) {
      throw new BaseError(UserForgotPasswordException.USER_FORGOT_PASSWORD_InvalidOtp);
    }

    // So sánh otp nhập vào với otp trong cache
    if (!userResetPasswordRequest.getOtp().equals(forgotPasswordCacheEntity.getOtp())) {
      throw new BaseError(UserForgotPasswordException.USER_FORGOT_PASSWORD_InvalidOtp);
    }

    // Lấy user từ DB
    UserEntity user = userRepository.findByEmailAndDeleteAtIsNull(
            userResetPasswordRequest.getEmail())
        .orElseThrow(
            () -> new BaseError(UserForgotPasswordException.USER_FORGOT_PASSWORD_UserNotFound));

    // Hash mật khẩu mới
    String hashedPassword = PasswordUtil.hashPassword(userResetPasswordRequest.getNewPassword());
    user.setPasswordHash(hashedPassword);

    // Cập nhật mật khẩu mới cho user
    userRepository.save(user);
  }

  @Override
  public void sendOtpVerifyPhone(UserSendOtpVerifyPhoneRequest userSendOtpVerifyPhoneRequest) {

    String phoneNumber = userSendOtpVerifyPhoneRequest.getPhoneNumber();

    // Check xem otp trong cache đã hết hạn chưa
    VerifyPhoneCacheEntity existsOtp = verifyPhoneCacheRepository.findById(phoneNumber)
        .orElse(null);
    if (existsOtp != null) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_CoolDown);
    }

    // Get current logged in user
    JwtTokenVo session = SecurityUtil.getSession();
    Long currentUserId = session.getUserId();

    // Validate that the phone number belongs to the current user

    // Convert phone number to standard format (+84xxx -> 0xxx)
    String formattedPhoneNumber = "0" + phoneNumber.substring(3);

    UserProfileEntity profile = findProfileByIdOrThrow(currentUserId);
    if (!formattedPhoneNumber.equals(profile.getPhoneNumber())) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_NotOwnPhone);
    }

    // Validate that the user has not already verified this phone
    if (Boolean.TRUE.equals(profile.getVerifiedPhone())) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_Verified);
    }

    // Generate OTP
    String otp = OtpUtil.generateOtp();

    // Sent OTP
    SmsSendRequest smsSendRequest = new SmsSendRequest();
    smsSendRequest.setPhoneNumbers(List.of(phoneNumber));
    smsSendRequest.setMessage("Your OTP to verify phone number is: " + otp);

    try {
      smsService.sendSms(smsSendRequest);
    } catch (Exception e) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_SendSmsFailed);
    }

    VerifyPhoneCacheEntity verifyPhoneCacheEntity = new VerifyPhoneCacheEntity();
    verifyPhoneCacheEntity.setPhoneNumber(phoneNumber);
    verifyPhoneCacheEntity.setOtp(otp);

    // Lưu vào cache để chờ được verify
    verifyPhoneCacheRepository.save(verifyPhoneCacheEntity);
  }

  @Override
  public void verifyPhoneOtp(UserVerifyPhoneRequest userVerifyPhoneRequest) {
    String phoneNumber = userVerifyPhoneRequest.getPhoneNumber();
    String otp = userVerifyPhoneRequest.getOtp();

    // Convert phone number to standard format (+84xxx -> 0xxx)
    String formattedPhoneNumber = "0" + phoneNumber.substring(3);

    // Lấy OTP từ cache
    VerifyPhoneCacheEntity verifyPhoneCacheEntity = verifyPhoneCacheRepository.findById(
            phoneNumber)
        .orElse(null);
    if (verifyPhoneCacheEntity == null) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_InvalidOtp);
    }

    // So sánh otp nhập vào với otp trong cache
    if (!otp.equals(verifyPhoneCacheEntity.getOtp())) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_InvalidOtp);
    }

    // Get current logged in user
    JwtTokenVo session = SecurityUtil.getSession();
    Long currentUserId = session.getUserId();

    // Validate that the phone number belongs to the current user
    UserProfileEntity profile = findProfileByIdOrThrow(currentUserId);
    if (!formattedPhoneNumber.equals(profile.getPhoneNumber())) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_NotOwnPhone);
    }

    // Validate that the user has not already verified this phone
    if (Boolean.TRUE.equals(profile.getVerifiedPhone())) {
      throw new BaseError(UserVerifyPhoneException.USER_VERIFY_PHONE_Verified);
    }

    // Cập nhật trạng thái verifiedPhone
    profile.setVerifiedPhone(true);
    userProfileRepository.save(profile);
  }

  @Override
  @Transactional
  public void changePassword(UserChangePasswordRequest request) {
    Long currentUserId = SecurityUtil.getSession().getUserId();

    // 1. Lấy thông tin User (chứa mật khẩu)
    UserEntity user = userRepository.findById(currentUserId)
        .orElseThrow(() -> new BaseError(UserRoleException.USER_NOT_FOUND));

    // 2. Kiểm tra mật khẩu cũ
    // Giả sử bạn dùng PasswordUtil.checkPassword(raw, hashed)
    if (!PasswordUtil.checkPassword(request.getOldPassword(), user.getPasswordHash())) {
      throw new BaseError(UserRoleException.PASSWORD_INCORRECT);
    }

    // 3. (Optional) Kiểm tra mật khẩu mới có trùng mật khẩu cũ không
    if (request.getOldPassword().equals(request.getNewPassword())) {
      throw new BaseError(UserRoleException.PASSWORD_SAME_AS_OLD);
    }

    // 4. Mã hóa mật khẩu mới và lưu
    // Giả sử bạn dùng PasswordUtil.hashPassword(raw) hoặc BCrypt.hashpw...
    String newHashedPassword = PasswordUtil.hashPassword(request.getNewPassword());

    user.setPasswordHash(newHashedPassword);
    userRepository.save(user);
  }

  @Override
  @Transactional
  public UserProfileResponse updateMyProfile(UserProfileUpdateRequest request) {
    JwtTokenVo session = SecurityUtil.getSession();
    Long currentUserId = session.getUserId();

    // Find the existing profile
    UserProfileEntity profile = findProfileByIdOrThrow(currentUserId);

    // Identify the preset user is using
    PreferencePresetEntity currentPreset = presetRepository
        .findByPreferenceEducationAndPreferenceSafetyAndPreferenceTransportationAndPreferenceShoppingAndPreferenceEntertainmentAndPreferenceEnvironmentAndPreferenceHealthcare(
            profile.getPreferenceEducation(),
            profile.getPreferenceSafety(),
            profile.getPreferenceTransportation(),
            profile.getPreferenceShopping(),
            profile.getPreferenceEntertainment(),
            profile.getPreferenceEnvironment(),
            profile.getPreferenceHealthcare()
        ).orElse(null);

    // Map non-null fields from request DTO to entity
    userProfileMapper.updateEntityFromRequest(request, profile);

    if (request.getPreferenceSafety() != null) {
      profile.setPreferenceSafety(request.getPreferenceSafety());
    }
    if (request.getPreferenceEducation() != null) {
      profile.setPreferenceEducation(request.getPreferenceEducation());
    }
    if (request.getPreferenceShopping() != null) {
      profile.setPreferenceShopping(request.getPreferenceShopping());
    }
    if (request.getPreferenceTransportation() != null) {
      profile.setPreferenceTransportation(request.getPreferenceTransportation());
    }
    if (request.getPreferenceEnvironment() != null) {
      profile.setPreferenceEnvironment(request.getPreferenceEnvironment());
    }
    if (request.getPreferenceEntertainment() != null) {
      profile.setPreferenceEntertainment(request.getPreferenceEntertainment());
    }
    if (request.getPreferenceHealthcare() != null) {
      profile.setPreferenceHealthcare(request.getPreferenceHealthcare());
    }

    boolean isPreferenceChanged = isPreferenceFieldsChanged(request);

    UserProfileEntity updatedProfile = userProfileRepository.save(profile);

    if (currentPreset != null && isPreferenceChanged) {
      PreferencePresetEntity newPreset = presetRepository
          .findByPreferenceEducationAndPreferenceSafetyAndPreferenceTransportationAndPreferenceShoppingAndPreferenceEntertainmentAndPreferenceEnvironmentAndPreferenceHealthcare(
              request.getPreferenceEducation(),
              request.getPreferenceSafety(),
              request.getPreferenceTransportation(),
              request.getPreferenceShopping(),
              request.getPreferenceEntertainment(),
              request.getPreferenceEnvironment(),
              request.getPreferenceHealthcare()
          ).orElse(null);

      if (newPreset == null) {
        saveAdaptationLog(currentUserId, profile, currentPreset);
      }
    }

    return userProfileMapper.toResponse(updatedProfile);
  }

  // Helper: Ghi log
  private void saveAdaptationLog(Long userId, UserProfileEntity newProfile,
      PreferencePresetEntity preferencePresetEntity) {
    PresetAdaptationLogEntity log = PresetAdaptationLogEntity.builder()
        .userId(userId)
        .preferencePresetEntity(preferencePresetEntity)
        .newSafety(newProfile.getPreferenceSafety())
        .newEducation(newProfile.getPreferenceEducation())
        .newShopping(newProfile.getPreferenceShopping())
        .newTransportation(newProfile.getPreferenceTransportation())
        .newEnvironment(newProfile.getPreferenceEnvironment())
        .newEntertainment(newProfile.getPreferenceEntertainment())
        .newHealthcare(newProfile.getPreferenceHealthcare())
        .build();

    presetAdaptationLogRepository.save(log);
  }

  // Helper: Check if request contains any preference fields
  private boolean isPreferenceFieldsChanged(UserProfileUpdateRequest request) {
    return request.getPreferenceSafety() != null ||
        request.getPreferenceEducation() != null ||
        request.getPreferenceShopping() != null ||
        request.getPreferenceTransportation() != null ||
        request.getPreferenceEnvironment() != null ||
        request.getPreferenceEntertainment() != null ||
        request.getPreferenceHealthcare() != null;
  }

  @Override
  @Transactional
  public UserProfileResponse requestSellerRole() {
    JwtTokenVo session = SecurityUtil.getSession();
    Long currentUserId = session.getUserId();

    // 1. Tìm UserEntity (để kiểm tra vai trò)
    UserEntity user = userRepository.findById(currentUserId)
        .orElseThrow(() -> new BaseError(UserRoleException.USER_NOT_FOUND));

    // 2. Tìm UserProfileEntity (để kiểm tra trạng thái)
    UserProfileEntity profile = findProfileByIdOrThrow(currentUserId); // (Dùng helper method cũ)

    // 3. Kiểm tra logic nghiệp vụ
    if (user.getRoles() != null && user.getRoles().contains(RoleTypeEnum.SELLER.toString())) {
      throw new BaseError(UserRoleException.ALREADY_A_SELLER);
    }

    if (profile.getBecomeSellerApproveStatus() == SellerApprovalStatus.PENDING) {
      throw new BaseError(UserRoleException.REQUEST_ALREADY_PENDING);
    }

    // Check that the user have verified phone number
    if (Boolean.FALSE.equals(profile.getVerifiedPhone())) {
      throw new BaseError(UserRoleException.PHONE_NOT_VERIFIED);
    }

    // 4. Cập nhật trạng thái
    profile.setBecomeSellerApproveStatus(SellerApprovalStatus.PENDING);
    UserProfileEntity savedProfile = userProfileRepository.save(profile);

    // 5. Trả về profile đã cập nhật
    return userProfileMapper.toResponse(savedProfile);
  }

  @Override
  public Page<UserProfileResponse> searchUser(SearchDataDto searchDataDto) {
    Specification<UserProfileEntity> spec = SearchUtil.getSpecification(searchDataDto,
        UserProfileEntity.class);

    // Add deletedAt filter in the specification

    spec = spec.and((root, query, criteriaBuilder)
        -> criteriaBuilder.isNull(root.get("deleteAt"))
    );

    Pageable pageable = SearchUtil.getPageable(searchDataDto);

    Page<UserProfileEntity> userProfileEntityPage = userProfileRepository.findAll(spec, pageable);

    return userProfileMapper.toPageResponse(userProfileEntityPage);
  }
  // --- Private Helper Method ---

  @SneakyThrows
  private UserProfileEntity findProfileByIdOrThrow(Long userId) {
    // We find by ID, because in this design, profile_id IS user_id
    return userProfileRepository.findById(userId)
        .orElseThrow(() -> new BaseError(UserProfileException.PROFILE_NOT_FOUND));
  }

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
    UserGetMeResponse userGetMeResponse = userMapper.toUserGetMeResponse(user.getUserProfile());
    userGetMeResponse.setEmail(user.getEmail());
    userGetMeResponse.setRoles(user.getRoles());

    // Find preference preset ID if exists by user profile perference score
    presetRepository
        .findByPreferenceEducationAndPreferenceSafetyAndPreferenceTransportationAndPreferenceShoppingAndPreferenceEntertainmentAndPreferenceEnvironmentAndPreferenceHealthcare(
            user.getUserProfile().getPreferenceEducation(),
            user.getUserProfile().getPreferenceSafety(),
            user.getUserProfile().getPreferenceTransportation(),
            user.getUserProfile().getPreferenceShopping(),
            user.getUserProfile().getPreferenceEntertainment(),
            user.getUserProfile().getPreferenceEnvironment(),
            user.getUserProfile().getPreferenceHealthcare()
        ).ifPresent(preset -> userGetMeResponse.setPreferencePresetId(preset.getId()));

    return userGetMeResponse;
  }

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

    List<String> roles = user.getRoles();

    JwtTokenVo jwtTokenVo = new JwtTokenVo(
        user.getId(),
        roles, null, clientIp);

    String accessToken = SecurityUtil.createToken(jwtTokenVo);

    UserLoginResponse userLoginResponse = new UserLoginResponse();
    userLoginResponse.setToken(accessToken);

    return userLoginResponse;
  }

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

    // Set role
    user.setRoles(List.of(RoleTypeEnum.USER.toString()));

    return userRepository.save(user);
  }
}
