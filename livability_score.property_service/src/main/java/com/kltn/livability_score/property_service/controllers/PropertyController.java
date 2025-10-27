package com.kltn.livability_score.property_service.controllers;

import com.kltn.livability_score.property_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.property_service.exception.property.PropertyException;
import com.kltn.livability_score.property_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.property_service.model.property.request.PropertyRequest;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import com.kltn.livability_score.property_service.services.PropertyService;
import com.kltn.livability_score.property_service.utils.ResponseEntityGenerator;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/properties")
@RequiredArgsConstructor
@Tag(name = "Property API", description = "APIs for property management by users")
@SecurityRequirement(name = "bearerAuth") // Assume JWT auth
public class PropertyController {

  private final PropertyService propertyService;

  @PostMapping
  @Operation(summary = "Create a new property listing")
  @ApiErrorResponse(errorEnum = PropertyException.class, validateSchema = PropertyRequest.class) // Add validation errors
  public ResponseEntity<ResponseVO<PropertyDetailResponse>> createProperty(
      @Valid @RequestBody PropertyRequest request) {

    PropertyDetailResponse response = propertyService.createProperty(request);
    return ResponseEntityGenerator.okFormat(response);
  }

  @PutMapping("/{id}")
  @Operation(summary = "Update an existing property listing")
  @ApiErrorResponse(errorEnum = PropertyException.class)
  public ResponseEntity<ResponseVO<PropertyDetailResponse>> updateProperty(
      @PathVariable("id") Long propertyId,
      @Valid @RequestBody PropertyRequest request) {

    PropertyDetailResponse response = propertyService.updateProperty(propertyId, request);
    return ResponseEntityGenerator.okFormat(response);
  }

  @DeleteMapping("/{id}")
  @Operation(summary = "Delete a property listing (Soft Delete)")
  @ApiErrorResponse(errorEnum = PropertyException.class)
  public ResponseEntity<ResponseVO<String>> deleteProperty(
      @PathVariable("id") Long propertyId) {

    propertyService.deleteProperty(propertyId);
    return ResponseEntityGenerator.okFormat("Delete successfully");
  }

  @GetMapping("/{id}")
  @Operation(summary = "Get property details")
  @ApiErrorResponse(errorEnum = PropertyException.class)
  public ResponseEntity<ResponseVO<PropertyDetailResponse>> getPropertyById(
      @PathVariable("id") Long propertyId) {

    PropertyDetailResponse response = propertyService.getPropertyById(propertyId);
    return ResponseEntityGenerator.okFormat(response);
  }
}