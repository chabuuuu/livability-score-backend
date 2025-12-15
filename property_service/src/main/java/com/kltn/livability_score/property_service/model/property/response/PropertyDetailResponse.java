package com.kltn.livability_score.property_service.model.property.response;


import com.kltn.livability_score.property_service.client.model.UserProfileResponse;
import com.kltn.livability_score.property_service.enums.ListingType;
import com.kltn.livability_score.property_service.enums.PropertyApprovalStatus;
import com.kltn.livability_score.property_service.enums.SellerApprovalStatus;
import lombok.Data;
import org.locationtech.jts.geom.Point; // (Cần dependency jts-core)

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@Data
public class PropertyDetailResponse {

  // Base fields
  private Long id;
  private Instant createdAt;
  private Instant updatedAt;

  // Ownership and Status
  private Long userId;
  private SellerProfile sellerProfile;

  @Data
  public static class SellerProfile {
    private String fullName;
    private String phoneNumber;
    private String avatarUrl;
    private String liveAddress;
    private Boolean verifiedPhone;
    private Instant updateAt;
  }

  private PropertyApprovalStatus approvalStatus;

  // Core Info
  private String title;
  private String description;
  private ListingType listingType;
  private BigDecimal price;
  private String priceUnit;
  private BigDecimal area;
  private String propertyType;
  private String legalStatus;

  // Details
  private Integer numBedrooms;
  private Integer numBathrooms;
  private Integer numFloors;
  private BigDecimal facadeWidthM;
  private BigDecimal roadWidthM;

  // Directions & Furniture
  private String houseDirection;
  private String balconyDirection;
  private String furnitureStatus;

  // Project/Building Info
  private String projectName;
  private String buildingBlock;
  private Integer floorNumber;

  // Address
  private String addressStreet;
  private String addressWard;
  private String addressDistrict;
  private String addressCity;

  // Technical fields
  private Point location; // Sẽ được serialize thành GeoJSON (cần jackson-datatype-jts)
  private Map<String, Object> features; // Cho JSONB

  // --- Mapped Relationship Fields ---

  // Mapped từ List<PropertyImageEntity>
  private List<String> imageUrls;

  // Mapped từ Set<TagEntity>
  private List<String> tagNames;

  private Long viewCount;
}