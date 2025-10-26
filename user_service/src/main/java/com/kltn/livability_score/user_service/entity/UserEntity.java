package com.kltn.livability_score.user_service.entity;

import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Component;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import jakarta.persistence.*;


@Entity
@Table(name = "users")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class UserEntity extends BaseEntity {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "email", nullable = false, unique = true, length = 255)
  private String email;

  @Column(name = "password_hash", nullable = false, length = 255)
  private String passwordHash;

  // --- Mối quan hệ ---

  /**
   * Quan hệ 1-1 với UserProfile.
   * mappedBy = "user": Chỉ ra rằng 'UserProfile' là entity "con" và nó quản lý
   * mối quan hệ này thông qua trường 'user'.
   * cascade = CascadeType.ALL: Bất kỳ thay đổi nào trên User (persist, remove, ...)
   * cũng sẽ được áp dụng cho UserProfile.
   * orphanRemoval = true: Nếu một UserProfile bị gỡ khỏi User (vd: user.setUserProfile(null)),
   * nó sẽ bị xóa khỏi DB.
   */
  @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY, orphanRemoval = true)
  private UserProfileEntity userProfile;

  /**
   * Quan hệ 1-N với bảng join 'UserFavoriteProperty'.
   * Chúng ta không dùng @ManyToMany trực tiếp vì bảng join có thêm cột (created_at, ...).
   */
  @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
  private List<UserFavoritePropertyEntity> favoriteProperties = new ArrayList<>();

}