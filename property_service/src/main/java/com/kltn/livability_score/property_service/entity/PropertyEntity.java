package com.kltn.livability_score.property_service.entity;


import com.kltn.livability_score.property_service.enums.ListingType;
import com.kltn.livability_score.property_service.enums.PropertyApprovalStatus;
import jakarta.persistence.*;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.*;
import org.hibernate.type.SqlTypes;
import org.locationtech.jts.geom.Point; // Dependency: org.locationtech.jts:jts-core

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "`properties`")
public class PropertyEntity extends BaseEntity{

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "title", nullable = false, columnDefinition = "text")
  private String title;

  @Column(name = "description", columnDefinition = "text")
  private String description;

  @Enumerated(EnumType.STRING)
  @Column(name = "listing_type", nullable = false, length = 20)
  private ListingType listingType;

  @Column(name = "price", nullable = false, precision = 19, scale = 2)
  private BigDecimal price;

  @Column(name = "price_unit", nullable = false, length = 20)
  private String priceUnit;

  @Column(name = "area", nullable = false, precision = 10, scale = 2)
  private BigDecimal area;

  @Column(name = "property_type", nullable = false, length = 50)
  private String propertyType;

  @Column(name = "legal_status", length = 100)
  private String legalStatus;

  @Column(name = "num_bedrooms")
  private Integer numBedrooms = 0;

  @Column(name = "num_bathrooms")
  private Integer numBathrooms = 0;

  @Column(name = "num_floors")
  private Integer numFloors;

  @Column(name = "facade_width_m", precision = 5, scale = 2)
  private BigDecimal facadeWidthM;

  @Column(name = "road_width_m", precision = 5, scale = 2)
  private BigDecimal roadWidthM;

  @Column(name = "house_direction", length = 50)
  private String houseDirection;

  @Column(name = "balcony_direction", length = 50)
  private String balconyDirection;

  @Column(name = "furniture_status", length = 50)
  private String furnitureStatus;

  @Column(name = "project_name")
  private String projectName;

  @Column(name = "building_block", length = 100)
  private String buildingBlock;

  @Column(name = "floor_number")
  private Integer floorNumber;

  @Column(name = "address_street", columnDefinition = "text")
  private String addressStreet;

  @Column(name = "address_ward", length = 100)
  private String addressWard;

  @Column(name = "address_district", length = 100)
  private String addressDistrict;

  @Column(name = "address_city", length = 100)
  private String addressCity;

  @Column(name = "location", columnDefinition = "geometry(Point, 4326)") // Kiểu PostGIS
  private Point location;

  @JdbcTypeCode(SqlTypes.JSON) // Xử lý JSONB
  @Column(name = "features", columnDefinition = "jsonb")
  private Map<String, Object> features;

  @Column(name = "source_url", unique = true, columnDefinition = "text")
  private String sourceUrl;

  @Column(name = "source_listing_id", length = 100)
  private String sourceListingId;

  @Column(name = "posted_at")
  private OffsetDateTime postedAt;

  @Column(name = "provider", nullable = false, length = 50)
  private String provider = "SYSTEM";

  @Column(name = "user_id", nullable = false)
  private Long userId;

  // --- NEW FIELD: Status for admin approval ---
  @Enumerated(EnumType.STRING)
  @Column(name = "approval_status", nullable = false, length = 50)
  private PropertyApprovalStatus approvalStatus = PropertyApprovalStatus.PENDING;

// --- Relationships ---

  @OneToMany(
      mappedBy = "property",
      cascade = CascadeType.ALL,
      orphanRemoval = true,
      fetch = FetchType.LAZY
  )
  private List<PropertyImageEntity> images = new ArrayList<>();

  @ManyToMany(
      fetch = FetchType.LAZY,
      cascade = { CascadeType.PERSIST, CascadeType.MERGE }
  )
  @JoinTable(
      name = "property_tags",
      joinColumns = @JoinColumn(name = "property_id"),
      inverseJoinColumns = @JoinColumn(name = "tag_id")
  )
  // Use Set for ManyToMany
  private Set<TagEntity> tags = new HashSet<>();

  // --- Helper Methods ---

  public void addImage(PropertyImageEntity image) {
    images.add(image);
    image.setProperty(this);
  }

  public void removeImage(PropertyImageEntity image) {
    images.remove(image);
    image.setProperty(null);
  }

  public void addTag(TagEntity tag) {
    tags.add(tag);
    tag.getProperties().add(this);
  }

  public void removeTag(TagEntity tag) {
    tags.remove(tag);
    tag.getProperties().remove(this);
  }

  // --- Equals & HashCode (Important for Set) ---
  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    PropertyEntity that = (PropertyEntity) o;
    return id != null && Objects.equals(id, that.id);
  }

  @Override
  public int hashCode() {
    return getClass().hashCode();
  }

}