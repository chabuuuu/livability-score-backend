package com.kltn.livability_score.property_service.repository;


import com.kltn.livability_score.property_service.entity.TagEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface TagRepository extends JpaRepository<TagEntity, Integer> {

  Optional<TagEntity> findByName(String name);
}