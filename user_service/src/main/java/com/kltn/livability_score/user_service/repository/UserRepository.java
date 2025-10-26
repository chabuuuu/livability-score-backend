package com.kltn.livability_score.user_service.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.kltn.livability_score.user_service.entity.UserEntity;

public interface UserRepository extends JpaRepository<UserEntity, Integer> {

}
