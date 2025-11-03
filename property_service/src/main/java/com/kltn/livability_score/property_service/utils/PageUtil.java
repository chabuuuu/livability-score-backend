package com.kltn.livability_score.property_service.utils;

import org.modelmapper.ModelMapper;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import com.kltn.livability_score.property_service.model.base_format.request.RequestPageableVO;

import java.util.List;
import java.util.stream.Collectors;

public class PageUtil {
    private static final ModelMapper modelMapper = new ModelMapper();

    public static Pageable getPageable(RequestPageableVO request) {
        return Pageable.ofSize(request.getRpp()).withPage(request.getPage() - 1);
    }

    public static <T> Page<T> listToPage(List<T> list, Pageable pageable) {
        int start = (int) pageable.getOffset();
        int end = Math.min((start + pageable.getPageSize()), list.size());
        List<T> sublist = list.subList(start, end);
        return new PageImpl<>(sublist, pageable, list.size());
    }

    // Page to list
    public static <T> List<T> pageToList(Page<T> page) {
        return page.getContent();
    }

    /**
     * * Hàm này sẽ chuyển Page<T> sang Page <L>, ví dụ
     * Page<OrderEntity> sang Page<OrderListResponse>
     * ```
     * Pageable pageable = PageUtil.getPageable(requestPageableVO);
     * Page<OrderEntity> order = orderRepository.searchOrders(searchOrderRequest,
     * pageable);
     * Page<OrderListResponse> orderListResponses = PageUtil.mapPage(order,
     * OrderListResponse.class);
     * 
     * @param source
     * @param targetClass
     * @return
     * @param <T>
     * @param <L>
     */
    public static <T, L> Page<L> mapPage(Page<T> source, Class<L> targetClass) {
        Pageable pageable = source.getPageable();
        List<L> mappedContent = source.getContent().stream()
                .map(entity -> modelMapper.map(entity, targetClass))
                .collect(Collectors.toList());
        return new PageImpl<>(mappedContent, pageable, source.getTotalElements());
    }
}
