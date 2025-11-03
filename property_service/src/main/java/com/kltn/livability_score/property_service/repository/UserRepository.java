package com.kltn.livability_score.property_service.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.kltn.livability_score.property_service.entity.UserEntity;

public interface UserRepository extends JpaRepository<UserEntity, Integer> {

}
