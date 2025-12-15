package com.kltn.livability_score.property_service.mapper;

import com.kltn.livability_score.property_service.client.model.UserProfileResponse;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import org.mapstruct.Mapper;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring",
    nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
public interface UserMapper {
  PropertyDetailResponse.SellerProfile toSellerProfile(UserProfileResponse userProfileResponse);
}
