package com.kltn.livability_score.property_service.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "user_favorite_properties")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class UserFavoritePropertyEntity extends BaseEntity {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;


  @Column(name = "user_id", nullable = false)
  private Long userId;

  // --- BỔ SUNG TRƯỜNG NÀY ---
  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "property_id", nullable = false)
  private PropertyEntity property;
}