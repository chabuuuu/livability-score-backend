package com.kltn.livability_score.property_service.services;

import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import com.kltn.livability_score.property_service.model.specifications.SearchDataDto;
import org.springframework.data.domain.Page;

public interface FavoriteService {
  void likeProperty(Long propertyId);

  void unlikeProperty(Long propertyId);

  Page<PropertyDetailResponse> searchMyFavoritedProperties(SearchDataDto searchDataDto);

  Boolean checkIsFavorited(Long propertyId);
}