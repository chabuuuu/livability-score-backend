package com.kltn.livability_score.user_service.services.impl;

import com.kltn.livability_score.user_service.entity.PreferencePresetEntity;
import com.kltn.livability_score.user_service.exception.handler.BaseError;
import com.kltn.livability_score.user_service.exception.preference_preset.PreferencePresetException;
import com.kltn.livability_score.user_service.mapper.PreferencePresetMapper;
import com.kltn.livability_score.user_service.model.preference_preset.request.PreferencePresetRequest;
import com.kltn.livability_score.user_service.model.preference_preset.response.PreferencePresetResponse;
import com.kltn.livability_score.user_service.model.preference_preset.response.PresetSuggestionResponse;
import com.kltn.livability_score.user_service.repository.PreferencePresetRepository;
import com.kltn.livability_score.user_service.repository.PresetAdaptationLogRepository;
import com.kltn.livability_score.user_service.services.PreferencePresetService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class PreferencePresetServiceImpl implements PreferencePresetService {

  private final PreferencePresetRepository presetRepository;
  private final PreferencePresetMapper presetMapper;
  private final PresetAdaptationLogRepository presetAdaptationLogRepository;

  @Override
  @SneakyThrows
  @Transactional
  public PreferencePresetResponse createPreset(PreferencePresetRequest request) {
    PreferencePresetEntity entity = presetMapper.toEntity(request);
    PreferencePresetEntity savedEntity = presetRepository.save(entity);
    return presetMapper.toResponse(savedEntity);
  }

  @Override
  @SneakyThrows
  @Transactional
  public PreferencePresetResponse updatePreset(Long id, PreferencePresetRequest request) {
    PreferencePresetEntity entity = findByIdOrThrow(id);

    presetMapper.updateEntityFromRequest(request, entity);

    PreferencePresetEntity updatedEntity = presetRepository.save(entity);
    return presetMapper.toResponse(updatedEntity);
  }

  @Override
  @SneakyThrows
  @Transactional
  public void deletePreset(Long id) {
    PreferencePresetEntity entity = findByIdOrThrow(id);

    // Soft delete (thanks to @SQLDelete in BaseEntity)
    presetRepository.delete(entity);
  }

  @Override
  @SneakyThrows
  @Transactional(readOnly = true)
  public PreferencePresetResponse getPresetById(Long id) {
    PreferencePresetEntity entity = findByIdOrThrow(id);
    return presetMapper.toResponse(entity);
  }

  @Override
  @Transactional(readOnly = true)
  public List<PreferencePresetResponse> getAllPresets() {
    List<PreferencePresetEntity> entities = presetRepository.findAll();
    return presetMapper.toResponseList(entities);
  }

  @Override
  @Transactional(readOnly = true)
  public PresetSuggestionResponse getSuggestionForPreset(Long presetId) {
    // 1. Tìm preset để lấy tên
    PreferencePresetEntity preset = findByIdOrThrow(presetId);

    // 2. Query thống kê từ bảng Log
    PresetSuggestionResponse suggestion = presetAdaptationLogRepository.getSuggestionStats(
        preset.getId());

    // 3. Nếu chưa có dữ liệu log nào, trả về object rỗng với tên preset
    if (suggestion == null) {
      suggestion = new PresetSuggestionResponse();
      suggestion.setSourcePresetName(preset.getName());
      suggestion.setTotalAdaptations(0L);
    }

    return suggestion;
  }

  // --- Private Helper ---

  @SneakyThrows
  private PreferencePresetEntity findByIdOrThrow(Long id) {
    // findById() already filters for deleted_at IS NULL
    return presetRepository.findById(id)
        .orElseThrow(() -> new BaseError(PreferencePresetException.PRESET_NOT_FOUND));
  }
}