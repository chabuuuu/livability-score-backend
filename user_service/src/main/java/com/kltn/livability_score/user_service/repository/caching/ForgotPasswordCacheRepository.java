package com.kltn.livability_score.user_service.repository.caching;

import com.kltn.livability_score.user_service.entity.caching.ForgotPasswordCacheEntity;
import org.springframework.data.repository.CrudRepository;

public interface ForgotPasswordCacheRepository extends
    CrudRepository<ForgotPasswordCacheEntity, String> {

}
