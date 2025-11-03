package com.kltn.livability_score.property_service.services.impl;

import org.springframework.stereotype.Service;

import com.kltn.livability_score.property_service.entity.UserEntity;
import com.kltn.livability_score.property_service.exception.UserRegisterException;
import com.kltn.livability_score.property_service.exception.handler.BaseError;
import com.kltn.livability_score.property_service.repository.UserRepository;
import com.kltn.livability_score.property_service.services.UserService;

import lombok.AllArgsConstructor;
import lombok.SneakyThrows;

@Service
@AllArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;

    @Override
    @SneakyThrows
    public void test() {
        throw new BaseError(UserRegisterException.USER_REGISTES_UserAlreadyExist);
    }

    public UserEntity getUserById(Integer id) {
        return userRepository.findById(id).orElseThrow(() -> new RuntimeException("User not found"));
    }

}
