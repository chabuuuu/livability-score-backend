package com.kltn.livability_score.property_service.entity;

import jakarta.persistence.Column;
import jakarta.persistence.MappedSuperclass;
import java.time.Instant;
import lombok.Getter;
import lombok.Setter;
import lombok.ToString;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.annotations.Where;
import org.springframework.data.annotation.CreatedDate;

@Getter
@Setter
@MappedSuperclass
@ToString
@SQLDelete(sql = "UPDATE #{#entityName} SET deleted_at = NOW() WHERE id = ?") // Use entityName
@SQLRestriction("deletedAt <> 'DELETED'")
public class BaseEntity {

  @Column(updatable = false, name = "created_at")
  @CreatedDate
  @CreationTimestamp
  private Instant createdAt;

  @Column(insertable = false, name = "updated_at")
  @UpdateTimestamp
  private Instant updatedAt;

  @Column(name = "deleted_at")
  private Instant deletedAt;
}