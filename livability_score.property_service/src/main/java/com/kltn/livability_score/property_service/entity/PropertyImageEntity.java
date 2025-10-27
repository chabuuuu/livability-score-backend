package com.kltn.livability_score.property_service.entity;


import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "`property_images`")
public class PropertyImageEntity extends BaseEntity{

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "image_url", nullable = false, columnDefinition = "text")
  private String imageUrl;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "property_id", nullable = false)
  private PropertyEntity property;

  // Constructor for easy creation
  public PropertyImageEntity(String imageUrl,  PropertyEntity property) {
    this.imageUrl = imageUrl;
    this.property = property;
  }

}