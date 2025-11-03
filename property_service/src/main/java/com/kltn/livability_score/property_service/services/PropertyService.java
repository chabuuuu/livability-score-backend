package com.kltn.livability_score.property_service.services;


import com.kltn.livability_score.property_service.model.property.request.ApprovePropertyRequest;
import com.kltn.livability_score.property_service.model.property.request.PropertyRequest;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import com.kltn.livability_score.property_service.model.property.response.PropertyMapSummaryResponse;
import com.kltn.livability_score.property_service.model.specifications.SearchDataDto;
import java.util.List;
import org.springframework.data.domain.Page;

public interface PropertyService {

  PropertyDetailResponse createProperty(PropertyRequest request);

  PropertyDetailResponse updateProperty(Long propertyId, PropertyRequest request);

  void deleteProperty(Long propertyId);

  PropertyDetailResponse getPropertyById(Long propertyId);

  // Admin function
  PropertyDetailResponse approveProperty(Long propertyId, ApprovePropertyRequest request);

  Page<PropertyDetailResponse> searchProperty(SearchDataDto searchDataDto);

  List<PropertyMapSummaryResponse> findPropertiesInViewport(
      double minLat, double minLng, double maxLat, double maxLng
  );

}