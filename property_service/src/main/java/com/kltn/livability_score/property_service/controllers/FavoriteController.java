package com.kltn.livability_score.property_service.controllers;

import com.kltn.livability_score.property_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.property_service.exception.favorite.FavoriteException;
import com.kltn.livability_score.property_service.model.base_format.response.ResponsePagingVO;
import com.kltn.livability_score.property_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import com.kltn.livability_score.property_service.model.specifications.SearchDataDto;
import com.kltn.livability_score.property_service.services.FavoriteService;
import com.kltn.livability_score.property_service.utils.ResponseEntityGenerator;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/properties/favorites")
@RequiredArgsConstructor
@Tag(name = "Favorite API", description = "Manage user favorite properties")
@SecurityRequirement(name = "bearerAuth")
public class FavoriteController {

  private final FavoriteService favoriteService;

  @PostMapping("/{propertyId}")
  @Operation(summary = "Like a property")
  @ApiErrorResponse(errorEnum = FavoriteException.class)
  public ResponseEntity<ResponseVO<String>> likeProperty(@PathVariable Long propertyId) {

    favoriteService.likeProperty(propertyId);
    return ResponseEntityGenerator.okFormat("Property liked successfully");
  }

  @DeleteMapping("/{propertyId}")
  @Operation(summary = "Unlike (remove) a property")
  @ApiErrorResponse(errorEnum = FavoriteException.class)
  public ResponseEntity<ResponseVO<String>> unlikeProperty(@PathVariable Long propertyId) {

    favoriteService.unlikeProperty(propertyId);
    return ResponseEntityGenerator.okFormat("Property unliked successfully");
  }

  @PostMapping("/search")
  @Operation(summary = "Search for favorited properties")
  public ResponseEntity<ResponsePagingVO<PropertyDetailResponse>> searchMyFavoritedProperties(
      @RequestBody SearchDataDto searchDataDto) {

    Page<PropertyDetailResponse> result = favoriteService.searchMyFavoritedProperties(searchDataDto);

    return ResponseEntityGenerator.searchFormat(result, searchDataDto);
  }

  @GetMapping("/{propertyId}/check")
  @Operation(summary = "Check if current user liked this property")
  public ResponseEntity<ResponseVO<Boolean>> checkIsFavorited(
      @PathVariable Long propertyId) {

    Boolean isFavorited = favoriteService.checkIsFavorited(propertyId);

    // Trả về true/false bọc trong ResponseVO
    return ResponseEntityGenerator.okFormat(isFavorited);
  }
}