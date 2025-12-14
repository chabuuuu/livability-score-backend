package com.kltn.livability_score.property_service.model.property.response;


import com.kltn.livability_score.property_service.enums.ListingType;
import java.time.Instant;
import lombok.Data;
import org.locationtech.jts.geom.Point;

import java.math.BigDecimal;

/**
 * A lightweight DTO for displaying property pins on a map.
 */
@Data
public class PropertyMapSummaryResponse {

  private Long id;
  private String title;
  private BigDecimal price;
  private String priceUnit;
  private ListingType listingType;
  private Point location; // Jackson will serialize this to GeoJSON
  private BigDecimal area;
  private String addressStreet;
  private String addressWard;
  private String addressDistrict;
  private String addressCity;
  private Instant createdAt;
  private String thumbnailUrl; // The first image URL for the property
}