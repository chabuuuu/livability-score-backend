package com.kltn.livability_score.property_service.model.property.response;


import com.kltn.livability_score.property_service.enums.ListingType;
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
}