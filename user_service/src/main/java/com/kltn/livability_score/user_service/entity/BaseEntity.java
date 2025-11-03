package com.kltn.livability_score.user_service.entity;

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
import org.springframework.data.annotation.CreatedDate;

@Getter
@Setter
@MappedSuperclass
@ToString
@SQLDelete(sql = "UPDATE #{#entityName} SET delete_at = NOW() WHERE id = ?") // Use entityName
@SQLRestriction("deletedAt <> 'DELETED'")
public class BaseEntity {

  @Column(updatable = false, name = "create_at")
  @CreatedDate
  @CreationTimestamp
  private Instant createAt;

  @Column(insertable = false, name = "update_at")
  @UpdateTimestamp
  private Instant updateAt;

  @Column(name = "delete_at")
  private Instant deleteAt;
}