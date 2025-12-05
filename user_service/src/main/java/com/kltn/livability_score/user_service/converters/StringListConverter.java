package com.kltn.livability_score.user_service.converters;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Converter
public class StringListConverter implements AttributeConverter<List<String>, String> {

  @Override
  public String convertToDatabaseColumn(List<String> list) {
    // Kiểm tra null hoặc rỗng để tránh lưu chuỗi "null" hoặc lỗi
    if (list == null || list.isEmpty()) {
      return null;
    }
    return String.join(",", list);
  }

  @Override
  public List<String> convertToEntityAttribute(String joined) {
    // 1. Trả về ArrayList rỗng thay vì null để tránh NullPointerException khi gọi .add()
    if (joined == null || joined.isEmpty()) {
      return new ArrayList<>();
    }

    // 2. Bọc kết quả trong new ArrayList(...) để tạo ra một List có thể chỉnh sửa (Mutable)
    // Arrays.asList(...) trả về list cố định -> gây lỗi UnsupportedOperationException
    return new ArrayList<>(Arrays.asList(joined.split(",")));
  }
}