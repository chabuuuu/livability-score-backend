package com.kltn.livability_score.user_service.utils;

import com.kltn.livability_score.user_service.model.base_format.request.RequestPageableVO;
import com.kltn.livability_score.user_service.model.base_format.response.ResponsePageableVO;
import com.kltn.livability_score.user_service.model.base_format.response.ResponsePagingVO;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVO;
import com.kltn.livability_score.user_service.model.base_format.response.ResponseVOBuilder;
import com.kltn.livability_score.user_service.model.specifications.SearchDataDto;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

public class ResponseEntityGenerator<T> {

  /*
   * Generate ResponseEntity with status CREATED 201
   * Using for any POST method
   */
  public static <T> ResponseEntity<ResponseVO<T>> createdFormat(Object body) {
    return new ResponseEntity<>((new ResponseVOBuilder().addData(body, HttpStatus.CREATED).build()),
        HttpStatus.CREATED);
  }

  /*
   * Generate ResponseEntity with status OK 200
   * Using for any GET MANY method
   */
  public static <T> ResponseEntity<ResponseVO<T>> findManyFormat(List<Object> body) {
    return new ResponseEntity<>((new ResponseVOBuilder().addData(body).build()), HttpStatus.OK);
  }

  /*
   * Generate ResponseEntity with status OK 200
   * Using for any DELETE method
   */
  public static <T> ResponseEntity<ResponseVO<T>> deleteFormat(Object body) {
    return new ResponseEntity<>((new ResponseVOBuilder().addData(body).build()), HttpStatus.OK);
  }

  /*
   * Generate ResponseEntity with status OK 200
   * Using for any UPDATE method
   */
  public static <T> ResponseEntity<ResponseVO<T>> updateFormat(Object body) {
    return new ResponseEntity<>((new ResponseVOBuilder().addData(body).build()), HttpStatus.OK);
  }

  /*
   * Generate ResponseEntity with status OK 200
   * Using for any GET ONE method
   */
  public static <T> ResponseEntity<ResponseVO<T>> findOneFormat(Object body) {
    return new ResponseEntity<>((new ResponseVOBuilder().addData(body).build()), HttpStatus.OK);
  }

  /*
   * Generate ResponseEntity with status OK 200
   */
  public static <T> ResponseEntity<ResponseVO<T>> okFormat(T body) {
    return new ResponseEntity<>((new ResponseVOBuilder().addData(body).build()), HttpStatus.OK);
  }

  /*
   * Generate ResponseEntity with status OK 200
   * Using for any GET ONE method
   */
  public static <T> ResponseEntity<ResponseVO<T>> find(Object body) {
    return new ResponseEntity<>((new ResponseVOBuilder().addData(body).build()), HttpStatus.OK);
  }

  /*
   * Generate ResponseEntity with paging
   */
  public static <T> ResponseEntity<ResponseVO<T>> pagingFormat(Page<?> body,
      RequestPageableVO request) {
    List<?> product_list = body.getContent();
    ResponsePageableVO responseVo = new ResponsePageableVO((int) body.getTotalElements(),
        product_list, request);
    return new ResponseEntity<>(new ResponseVOBuilder().addData(responseVo).build(), HttpStatus.OK);
  }

  /*
   * Generate ResponseEntity with search
   */
  public static <T> ResponseEntity<ResponsePagingVO<T>> searchFormat(Page<T> body,
      SearchDataDto request) {
    List<T> product_list = body.getContent();

    RequestPageableVO requestPageableVO = new RequestPageableVO();
    requestPageableVO.setPage(request.getPage());
    requestPageableVO.setRpp(request.getRpp());

    ResponsePageableVO<T> responseVO = new ResponsePageableVO<T>(
        body.getTotalElements(), product_list, requestPageableVO);

    ResponsePagingVO<T> responsePagingVo = new ResponsePagingVO<>();

    responsePagingVo.setData(responseVO);
    responsePagingVo.setResult("Succeeded");
    responsePagingVo.setStatus("200");

    return new ResponseEntity<>(responsePagingVo, HttpStatus.OK);
  }
}
