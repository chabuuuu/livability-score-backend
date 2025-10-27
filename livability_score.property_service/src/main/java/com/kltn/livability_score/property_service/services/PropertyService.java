package com.kltn.livability_score.property_service.services;


import com.kltn.livability_score.property_service.model.property.request.ApprovePropertyRequest;
import com.kltn.livability_score.property_service.model.property.request.PropertyRequest;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;

public interface PropertyService {

  PropertyDetailResponse createProperty(PropertyRequest request);

  PropertyDetailResponse updateProperty(Long propertyId, PropertyRequest request);

  void deleteProperty(Long propertyId);

  PropertyDetailResponse getPropertyById(Long propertyId);

  // Admin function
  PropertyDetailResponse approveProperty(Long propertyId, ApprovePropertyRequest request);
}