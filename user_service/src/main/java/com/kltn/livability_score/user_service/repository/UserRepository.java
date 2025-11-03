package com.kltn.livability_score.user_service.repository;

import com.kltn.livability_score.user_service.entity.UserEntity;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<UserEntity, Long> {

  Optional<UserEntity> findByIdAndDeleteAtIsNull(Long shopperId);

  Optional<UserEntity> findByEmailAndDeleteAtIsNull(String email);

  boolean existsByEmailAndDeleteAtIsNull(String email);
}
