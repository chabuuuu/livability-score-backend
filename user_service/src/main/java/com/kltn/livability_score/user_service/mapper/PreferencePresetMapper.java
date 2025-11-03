package com.kltn.livability_score.user_service.mapper;


import com.kltn.livability_score.user_service.entity.PreferencePresetEntity;
import com.kltn.livability_score.user_service.model.preference_preset.request.PreferencePresetRequest;
import com.kltn.livability_score.user_service.model.preference_preset.response.PreferencePresetResponse;
import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring",
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
public interface PreferencePresetMapper {

  @Mapping(target = "id", ignore = true)
  @Mapping(target = "createAt", ignore = true)
  @Mapping(target = "updateAt", ignore = true)
  @Mapping(target = "deleteAt", ignore = true)
  PreferencePresetEntity toEntity(PreferencePresetRequest request);

  @Mapping(source = "createAt", target = "createAt")
  PreferencePresetResponse toResponse(PreferencePresetEntity entity);

  List<PreferencePresetResponse> toResponseList(List<PreferencePresetEntity> entities);

  @Mapping(target = "id", ignore = true)
  @Mapping(target = "createAt", ignore = true)
  @Mapping(target = "updateAt", ignore = true)
  @Mapping(target = "deleteAt", ignore = true)
  void updateEntityFromRequest(PreferencePresetRequest request,
      @MappingTarget PreferencePresetEntity entity);
}