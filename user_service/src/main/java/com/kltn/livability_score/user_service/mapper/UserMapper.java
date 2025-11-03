package com.kltn.livability_score.user_service.mapper;

import com.kltn.livability_score.user_service.entity.UserProfileEntity;
import com.kltn.livability_score.user_service.model.user.response.UserGetMeResponse;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface UserMapper {

  UserGetMeResponse toUserGetMeResponse(UserProfileEntity userEntity);

}
