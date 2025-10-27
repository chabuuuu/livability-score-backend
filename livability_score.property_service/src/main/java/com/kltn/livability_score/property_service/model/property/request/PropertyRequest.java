package com.kltn.livability_score.property_service.model.property.request;


import com.kltn.livability_score.property_service.enums.ListingType;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Data;
import org.locationtech.jts.geom.Point;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import java.time.OffsetDateTime;


@Data
public class PropertyRequest {

  @NotEmpty
  private String title;

  private String description;

  @NotNull
  private ListingType listingType;

  @NotNull
  @Positive
  private BigDecimal price;

  @NotEmpty
  private String priceUnit;

  @NotNull
  @Positive
  private BigDecimal area;

  @NotEmpty
  private String propertyType;

  private String legalStatus;

  private Integer numBedrooms;

  private Integer numBathrooms;

  private Integer numFloors;

  private BigDecimal facadeWidthM;

  private BigDecimal roadWidthM;

  private String houseDirection;

  private String balconyDirection;

  private String furnitureStatus;

  private String projectName;

  private String buildingBlock;

  private Integer floorNumber;

  private String addressStreet;

  private String addressWard;

  private String addressDistrict;

  private String addressCity;

  // Client needs to send this in a format Jackson can deserialize
  // e.g., using jackson-datatype-jts
  private Point location;

  // For JSONB
  private Map<String, Object> features;

  private String sourceListingId;

  // --- Relationship fields ---

  // List of image URLs to associate with the property
  private List<String> imageUrls;

  // List of tag names to associate (e.g., "new", "lake_view")
  private List<String> tagNames;
}