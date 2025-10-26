package com.kltn.livability_score.user_service.services;

import com.kltn.livability_score.user_service.entity.UserEntity;

public interface UserService {
    void test();

    UserEntity getUserById(Integer id);
}
