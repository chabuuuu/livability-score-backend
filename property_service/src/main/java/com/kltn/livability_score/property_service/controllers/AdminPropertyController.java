package com.kltn.livability_score.property_service.controllers;

import com.kltn.livability_score.property_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.property_service.exception.property.PropertyException;
import com.kltn.livability_score.property_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.property_service.model.property.request.ApprovePropertyRequest;
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
@RequestMapping("/api/v1/properties/admin")
@RequiredArgsConstructor
@Tag(name = "Admin Property API", description = "APIs for admin to manage properties")
@SecurityRequirement(name = "bearerAuth") // Assume JWT auth
public class AdminPropertyController {

  private final PropertyService propertyService;

  @PostMapping("/{id}/approval")
  @Operation(summary = "Approve or reject a property listing")
  @ApiErrorResponse(errorEnum = PropertyException.class)
  public ResponseEntity<ResponseVO<PropertyDetailResponse>> approveProperty(
      @PathVariable("id") Long propertyId,
      @Valid @RequestBody ApprovePropertyRequest request) {

    PropertyDetailResponse response = propertyService.approveProperty(propertyId, request);
    return ResponseEntityGenerator.okFormat(response);
  }
}