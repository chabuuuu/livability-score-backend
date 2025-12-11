package com.kltn.livability_score.user_service.repository.caching;

import com.kltn.livability_score.user_service.entity.caching.VerifyPhoneCacheEntity;
import org.springframework.data.repository.CrudRepository;

public interface VerifyPhoneCacheRepository extends
    CrudRepository<VerifyPhoneCacheEntity, String> {

}
