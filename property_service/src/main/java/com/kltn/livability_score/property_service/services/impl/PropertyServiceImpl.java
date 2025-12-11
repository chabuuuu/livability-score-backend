package com.kltn.livability_score.property_service.services.impl;


import com.kltn.livability_score.property_service.entity.PropertyEntity;
import com.kltn.livability_score.property_service.entity.PropertyImageEntity;
import com.kltn.livability_score.property_service.entity.TagEntity;
import com.kltn.livability_score.property_service.enums.PropertyApprovalStatus;
import com.kltn.livability_score.property_service.exception.handler.BaseError;
import com.kltn.livability_score.property_service.exception.property.PropertyException;
import com.kltn.livability_score.property_service.mapper.PropertyMapper;
import com.kltn.livability_score.property_service.model.jwt.vo.JwtTokenVo;
import com.kltn.livability_score.property_service.model.property.request.ApprovePropertyRequest;
import com.kltn.livability_score.property_service.model.property.request.PropertyRequest;
import com.kltn.livability_score.property_service.model.property.response.PropertyDetailResponse;
import com.kltn.livability_score.property_service.model.property.response.PropertyMapSummaryResponse;
import com.kltn.livability_score.property_service.model.specifications.SearchDataDto;
import com.kltn.livability_score.property_service.publisher.PropertyEventPublisher;
import com.kltn.livability_score.property_service.repository.PropertyRepository;
import com.kltn.livability_score.property_service.repository.TagRepository;
import com.kltn.livability_score.property_service.services.PropertyService;
import com.kltn.livability_score.property_service.utils.SearchUtil;
import com.kltn.livability_score.property_service.utils.SecurityUtil;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashSet;
import java.util.Set;

@Service
@RequiredArgsConstructor
public class PropertyServiceImpl implements PropertyService {

  private final PropertyRepository propertyRepository;
  private final TagRepository tagRepository;
  private final PropertyMapper propertyMapper;
  private final StringRedisTemplate redisTemplate;
  private final PropertyEventPublisher propertyEventPublisher;

  @Override
  @SneakyThrows
  @Transactional
  public PropertyDetailResponse createProperty(PropertyRequest request) {
    JwtTokenVo session = SecurityUtil.getSession();
    Long currentUserId = session.getUserId();

    PropertyEntity entity = propertyMapper.toEntity(request);
    entity.setUserId(currentUserId);
    entity.setApprovalStatus(PropertyApprovalStatus.PENDING); // Default status

    // Handle images and tags
    handleImages(entity, request.getImageUrls());
    handleTags(entity, request.getTagNames());

    PropertyEntity savedEntity = propertyRepository.save(entity);

    // Send event for creating livability score (Async)
    propertyEventPublisher.publishPropertyUpdateEvent(savedEntity.getId(), "created");

    return propertyMapper.toDetailResponse(savedEntity);
  }

  @Override
  @SneakyThrows
  @Transactional
  public PropertyDetailResponse updateProperty(Long propertyId, PropertyRequest request) {
    JwtTokenVo session = SecurityUtil.getSession();
    Long currentUserId = session.getUserId();

    // Find property owned by the current user
    PropertyEntity entity = propertyRepository.findById(propertyId)
        .orElseThrow(() -> new BaseError(PropertyException.PROPERTY_NOT_FOUND));

    // If role is not ADMIN, check ownership
    if (!session.getRoles().contains("ADMIN") && !entity.getUserId().equals(currentUserId)) {
      throw new BaseError(PropertyException.FORBIDDEN_ACCESS);
    }

    // Update entity fields from request
    propertyMapper.updateEntityFromRequest(request, entity);

    // Reset status to PENDING after any update
    entity.setApprovalStatus(PropertyApprovalStatus.PENDING);

    // Handle images and tags (clear old, add new)
    handleImages(entity, request.getImageUrls());
    handleTags(entity, request.getTagNames());

    PropertyEntity updatedEntity = propertyRepository.save(entity);

    // Send event for update livability score (Async)
    propertyEventPublisher.publishPropertyUpdateEvent(updatedEntity.getId(), "updated");

    return propertyMapper.toDetailResponse(updatedEntity);
  }

  @Override
  @SneakyThrows
  @Transactional
  public void deleteProperty(Long propertyId) {
    JwtTokenVo session = SecurityUtil.getSession();
    Long currentUserId = session.getUserId();

    // Check if property exists and belongs to user
    PropertyEntity entity = propertyRepository.findByIdAndUserId(propertyId, currentUserId)
        .orElseThrow(() -> new BaseError(PropertyException.FORBIDDEN_ACCESS));

    // Soft delete (thanks to @SQLDelete in BaseEntity)
    propertyRepository.delete(entity);
  }

  @Override
  @SneakyThrows
  public PropertyDetailResponse getPropertyById(Long propertyId) {
    PropertyEntity entity = propertyRepository.findById(propertyId)
        .orElseThrow(() -> new BaseError(PropertyException.PROPERTY_NOT_FOUND));

    // Admin or owner can see PENDING, but public should only see APPROVED?
    // For now, just return it. Add role-based check if needed.

    // Increase the view count
    String key = "property:view_count:" + propertyId;
    redisTemplate.opsForValue().increment(key);

    // Lưu danh sách các ID đã thay đổi vào 1 Set để Scheduler biết cái nào cần update
    redisTemplate.opsForSet().add("property:changed_views", String.valueOf(propertyId));

    return propertyMapper.toDetailResponse(entity);
  }

  @Override
  @SneakyThrows
  @Transactional
  public PropertyDetailResponse approveProperty(Long propertyId, ApprovePropertyRequest request) {
    // Admin role check should be done by Spring Security config

    if (request.getApprovalStatus() == PropertyApprovalStatus.PENDING) {
      throw new BaseError(PropertyException.INVALID_APPROVAL_STATUS);
    }

    PropertyEntity entity = propertyRepository.findById(propertyId)
        .orElseThrow(() -> new BaseError(PropertyException.PROPERTY_NOT_FOUND));

    entity.setApprovalStatus(request.getApprovalStatus());

    PropertyEntity savedEntity = propertyRepository.save(entity);
    return propertyMapper.toDetailResponse(savedEntity);
  }

  @Override
  public Page<PropertyDetailResponse> searchProperty(SearchDataDto searchDataDto) {
    Specification<PropertyEntity> spec = SearchUtil.getSpecification(searchDataDto,
        PropertyEntity.class);

    // Add deletedAt filter in the specification

    spec = spec.and((root, query, criteriaBuilder)
        -> criteriaBuilder.isNull(root.get("deletedAt"))
    );

    Pageable pageable = SearchUtil.getPageable(searchDataDto);

    Page<PropertyEntity> propertyEntityPage = propertyRepository.findAll(spec, pageable);

    return propertyMapper.toPageResponse(propertyEntityPage);
  }

  @Override
  @Transactional(readOnly = true)
  public List<PropertyMapSummaryResponse> findPropertiesInViewport(
      double minLat, double minLng, double maxLat, double maxLng
  ) {
    List<PropertyEntity> entities = propertyRepository.findPropertiesInViewport(
        minLat, minLng, maxLat, maxLng
    );

    return propertyMapper.toMapSummaryResponseList(entities);
  }

  // --- Private Helper Methods ---

  private void handleImages(PropertyEntity entity, List<String> imageUrls) {
    // Clear existing images
    entity.getImages().clear();

    // Add new images
    if (imageUrls != null && !imageUrls.isEmpty()) {
      imageUrls.forEach(url ->
          entity.addImage(new PropertyImageEntity(url, entity))
      );
    }
  }

  private void handleTags(PropertyEntity entity, List<String> tagNames) {
    // Clear existing tags
    entity.getTags().clear();

    if (tagNames != null && !tagNames.isEmpty()) {
      Set<TagEntity> tags = new HashSet<>();
      for (String name : tagNames) {
        // Find tag or create a new one
        TagEntity tag = tagRepository.findByName(name)
            .orElseGet(() -> new TagEntity(name)); // Let cascade save the new tag
        tags.add(tag);
      }

      // Add all tags to the property
      tags.forEach(entity::addTag);
    }
  }
}