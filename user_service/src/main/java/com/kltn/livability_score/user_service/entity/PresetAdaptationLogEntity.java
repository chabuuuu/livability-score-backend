package com.kltn.livability_score.user_service.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "preset_adaptation_logs")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PresetAdaptationLogEntity extends BaseEntity {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "user_id")
  private Long userId;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "source_preset_id")
  private PreferencePresetEntity preferencePresetEntity;

  // Lưu lại bộ chỉ số MỚI mà người dùng vừa custom
  private BigDecimal newSafety;
  private BigDecimal newEducation;
  private BigDecimal newShopping;
  private BigDecimal newTransportation;
  private BigDecimal newEnvironment;
  private BigDecimal newEntertainment;
  private BigDecimal newHealthcare;

}