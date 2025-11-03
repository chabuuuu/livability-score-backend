package com.kltn.livability_score.property_service.controllers;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.kltn.livability_score.property_service.annotations.ApiErrorResponse;
import com.kltn.livability_score.property_service.entity.UserEntity;
import com.kltn.livability_score.property_service.exception.UserRegisterException;
import com.kltn.livability_score.property_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.property_service.model.user.request.UserRegisterReq;
import com.kltn.livability_score.property_service.model.user.response.UserRegisterRes;
import com.kltn.livability_score.property_service.services.UserService;
import com.kltn.livability_score.property_service.utils.ResponseEntityGenerator;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Tag(name = "User Management", description = "Quản lý người dùng")
public class UserController {
    private final UserService userService;

    @PostMapping
    @Operation(summary = "Register new user", description = "This API wil register new user account")
    @ApiErrorResponse(errorEnum = UserRegisterException.class, validateSchema = UserRegisterReq.class)
    @SneakyThrows
    public ResponseEntity<ResponseVO<UserRegisterRes>> registerUser(@RequestBody @Valid UserRegisterReq request) {
        UserRegisterRes userRegisterRes = new UserRegisterRes("test");

        userService.test();

        return ResponseEntityGenerator.okFormat(userRegisterRes);
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserEntity> getUserById(@PathVariable Integer id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }
}
