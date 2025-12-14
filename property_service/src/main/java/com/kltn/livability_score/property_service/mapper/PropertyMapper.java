package com.kltn.livability_score.property_service.mapper;


import com.kltn.livability_score.property_service.entity.PropertyEntity;
import com.kltn.livability_score.property_service.entity.PropertyImageEntity;
import com.kltn.livability_score.property_service.entity.TagEntity;
import com.kltn.livability_score.property_service.model.property.request.PropertyRequest;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import com.kltn.livability_score.property_service.model.property.response.PropertyMapSummaryResponse;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;

@Mapper(componentModel = "spring",
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
public interface PropertyMapper {

  // Target "images" and "tags" are ignored, handled manually in service
  @Mapping(target = "id", ignore = true)
  @Mapping(target = "userId", ignore = true)
  @Mapping(target = "approvalStatus", ignore = true)
  @Mapping(target = "images", ignore = true)
  @Mapping(target = "tags", ignore = true)
  PropertyEntity toEntity(PropertyRequest request);

  @Mapping(target = "id", ignore = true)
  @Mapping(target = "userId", ignore = true)
  @Mapping(target = "approvalStatus", ignore = true)
  @Mapping(target = "images", ignore = true)
  @Mapping(target = "tags", ignore = true)
  void updateEntityFromRequest(PropertyRequest request, @MappingTarget PropertyEntity entity);

  @Mapping(source = "images", target = "imageUrls")
  @Mapping(source = "tags", target = "tagNames")
  PropertyDetailResponse toDetailResponse(PropertyEntity entity);

  // --- Custom Mappers for Images and Tags ---
  default List<String> mapImagesToUrls(List<PropertyImageEntity> images) {
    if (images == null) {
      return List.of();
    }
    return images.stream()
        .map(PropertyImageEntity::getImageUrl)
        .collect(Collectors.toList());
  }

  default String mapImagesToThumbnail(List<PropertyImageEntity> images) {
    if (images == null || images.isEmpty()) {
      return null;
    }
    return images.getFirst().getImageUrl();
  }

  default List<String> mapTagsToNames(Set<TagEntity> tags) {
    if (tags == null) {
      return List.of();
    }
    return tags.stream()
        .map(TagEntity::getName)
        .collect(Collectors.toList());
  }

  List<PropertyDetailResponse> toResponseList(List<PropertyEntity> entities);


  default Page<PropertyDetailResponse> toPageResponse(Page<PropertyEntity> entities) {
    // Nếu đầu vào là null, trả về null
    if (entities == null) {
      return null;
    }

    List<PropertyDetailResponse> responses = toResponseList(entities.getContent());

    // 2. Tạo một đối tượng PageImpl mới với nội dung đã chuyển đổi và thông tin phân trang từ Page cũ
    return new PageImpl<>(responses, entities.getPageable(), entities.getTotalElements());
  }

  @Mapping(source = "images", target = "thumbnailUrl")
  PropertyMapSummaryResponse toMapSummaryResponse(PropertyEntity entity);

  List<PropertyMapSummaryResponse> toMapSummaryResponseList(List<PropertyEntity> entities);
}