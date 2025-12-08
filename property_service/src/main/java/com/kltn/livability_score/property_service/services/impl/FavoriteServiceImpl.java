package com.kltn.livability_score.property_service.services.impl;

import com.kltn.livability_score.property_service.entity.PropertyEntity;
import com.kltn.livability_score.property_service.entity.UserFavoritePropertyEntity;
import com.kltn.livability_score.property_service.exception.favorite.FavoriteException;
import com.kltn.livability_score.property_service.exception.handler.BaseError;
import com.kltn.livability_score.property_service.exception.property.PropertyException;
import com.kltn.livability_score.property_service.mapper.PropertyMapper;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import com.kltn.livability_score.property_service.model.specifications.SearchDataDto;
import com.kltn.livability_score.property_service.repository.PropertyRepository;
import com.kltn.livability_score.property_service.repository.UserFavoritePropertyRepository;
import com.kltn.livability_score.property_service.services.FavoriteService;
import com.kltn.livability_score.property_service.utils.SearchUtil;
import com.kltn.livability_score.property_service.utils.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class FavoriteServiceImpl implements FavoriteService {

  private final UserFavoritePropertyRepository favoriteRepository;
  private final PropertyRepository propertyRepository;
  private final PropertyMapper propertyMapper;

  @Override
  @Transactional
  public void likeProperty(Long propertyId) {
    Long currentUserId = SecurityUtil.getSession().getUserId();

    // 1. Kiểm tra xem đã like chưa
    if (favoriteRepository.existsByUserIdAndPropertyId(currentUserId, propertyId)) {
      throw new BaseError(FavoriteException.ALREADY_LIKED);
    }

    // 2. Lấy thông tin Property và User (Proxy reference cho nhẹ DB)
    PropertyEntity property = propertyRepository.findById(propertyId)
        .orElseThrow(() -> new BaseError(PropertyException.PROPERTY_NOT_FOUND));

    // 3. Tạo record mới
    UserFavoritePropertyEntity favorite = new UserFavoritePropertyEntity();
    favorite.setUserId(currentUserId);
    favorite.setProperty(property);

    favoriteRepository.save(favorite);
  }

  @Override
  @Transactional
  public void unlikeProperty(Long propertyId) {
    Long currentUserId = SecurityUtil.getSession().getUserId();

    // 1. Tìm record like
    UserFavoritePropertyEntity favorite = favoriteRepository.findByUserIdAndPropertyId(currentUserId, propertyId)
        .orElseThrow(() -> new BaseError(FavoriteException.NOT_LIKED_YET));

    // 2. Xóa (Soft delete do BaseEntity quản lý)
    favoriteRepository.delete(favorite);
  }

  @Override
  public Page<PropertyDetailResponse> searchMyFavoritedProperties(SearchDataDto searchDataDto) {
    Specification<PropertyEntity> spec = SearchUtil.getSpecification(searchDataDto,
        PropertyEntity.class);

    // Add deletedAt filter in the specification

    spec = spec.and((root, query, criteriaBuilder)
        -> criteriaBuilder.isNull(root.get("deletedAt"))
    );

    // Add filter to only include favorited properties by current user
    Long currentUserId = SecurityUtil.getSession().getUserId();

    spec = spec.and((root, query, criteriaBuilder) -> {
      // Subquery to select property IDs from UserFavoritePropertyEntity
      var subquery = query.subquery(Long.class);
      var favoriteRoot = subquery.from(UserFavoritePropertyEntity.class);
      subquery.select(favoriteRoot.get("property").get("id"))
          .where(criteriaBuilder.equal(favoriteRoot.get("userId"), currentUserId));

      // Main query predicate to filter properties in the subquery result
      return root.get("id").in(subquery);
    });

    Pageable pageable = SearchUtil.getPageable(searchDataDto);

    Page<PropertyEntity> propertyEntityPage = propertyRepository.findAll(spec, pageable);

    return propertyMapper.toPageResponse(propertyEntityPage);
  }

  @Override
  @Transactional(readOnly = true)
  public Boolean checkIsFavorited(Long propertyId) {
    Long currentUserId = SecurityUtil.getSession().getUserId();

    // Repository đã có sẵn hàm này từ bước trước
    return favoriteRepository.existsByUserIdAndPropertyId(currentUserId, propertyId);
  }
}