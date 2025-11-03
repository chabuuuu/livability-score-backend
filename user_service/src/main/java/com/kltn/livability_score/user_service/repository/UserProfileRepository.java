package com.kltn.livability_score.user_service.repository;


import com.kltn.livability_score.user_service.entity.UserProfileEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface UserProfileRepository extends JpaRepository<UserProfileEntity, Long>,
    JpaSpecificationExecutor<UserProfileEntity> {

  // findById(Long id) sẽ hoạt động, vì 'id' chính là 'user_id'
  // Nhờ @Where trong BaseEntity, nó đã tự động lọc soft-delete
}