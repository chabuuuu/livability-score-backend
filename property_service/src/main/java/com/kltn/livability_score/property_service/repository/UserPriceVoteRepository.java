package com.kltn.livability_score.property_service.repository;


import com.kltn.livability_score.property_service.entity.UserPriceVoteEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface UserPriceVoteRepository extends JpaRepository<UserPriceVoteEntity, Long> {

  // Lấy tất cả các vote của một bất động sản cụ thể
  List<UserPriceVoteEntity> findByPropertyId(Long propertyId);

  // Đếm tổng số vote
  long countByPropertyId(Long propertyId);
}