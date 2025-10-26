package com.kltn.livability_score.user_service.repository.caching;

import com.kltn.livability_score.user_service.entity.caching.RegisterUserCacheEntity;
import org.springframework.data.repository.CrudRepository;

public interface RegisterUserCacheRepository extends
    CrudRepository<RegisterUserCacheEntity, String> {

}
