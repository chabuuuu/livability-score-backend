package com.kltn.livability_score.property_service.entity;


import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "`tags`")
public class TagEntity extends BaseEntity {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Integer id;

  @Column(name = "name", nullable = false, unique = true, length = 100)
  private String name;

  @ManyToMany(mappedBy = "tags", fetch = FetchType.LAZY)
  // Use Set for ManyToMany
  private Set<PropertyEntity> properties = new HashSet<>();

  // Constructor for easy creation
  public TagEntity(String name) {
    this.name = name;
  }

  // --- Equals & HashCode (Based on business key 'name') ---
  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    TagEntity tagEntity = (TagEntity) o;
    return Objects.equals(name, tagEntity.name);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name);
  }
}