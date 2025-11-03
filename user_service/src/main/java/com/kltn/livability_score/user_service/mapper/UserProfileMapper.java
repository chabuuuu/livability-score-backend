package com.kltn.livability_score.user_service.mapper;


import com.kltn.livability_score.user_service.entity.UserProfileEntity;
import com.kltn.livability_score.user_service.model.user.request.UserProfileUpdateRequest;
import com.kltn.livability_score.user_service.model.user.response.UserProfileResponse;
import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;

@Mapper(componentModel = "spring",
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
public interface UserProfileMapper {

  // Chuyển từ Entity -> Response DTO
  @Mapping(source = "id", target = "id")
  @Mapping(source = "updateAt", target = "updateAt")
  UserProfileResponse toResponse(UserProfileEntity entity);

  // Cập nhật Entity từ Request DTO (Bỏ qua các trường null)
  @Mapping(target = "id", ignore = true)
  @Mapping(target = "user", ignore = true)
  @Mapping(target = "createAt", ignore = true)
  @Mapping(target = "updateAt", ignore = true)
  @Mapping(target = "deleteAt", ignore = true)
  void updateEntityFromRequest(UserProfileUpdateRequest request,
      @MappingTarget UserProfileEntity entity);

  default Page<UserProfileResponse> toPageResponse(Page<UserProfileEntity> entities) {
    // Nếu đầu vào là null, trả về null
    if (entities == null) {
      return null;
    }

    List<UserProfileResponse> responses = toResponseList(entities.getContent());

    // 2. Tạo một đối tượng PageImpl mới với nội dung đã chuyển đổi và thông tin phân trang từ Page cũ
    return new PageImpl<>(responses, entities.getPageable(), entities.getTotalElements());
  }

  List<UserProfileResponse> toResponseList(List<UserProfileEntity> entities);


}