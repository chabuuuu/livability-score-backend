import pandas as pd
import os
import time

def split_csv_by_listing_type(input_file, batch_size=5000):
    # Định nghĩa tên file đầu ra
    output_sale = 'properties_sale.csv'
    output_rent = 'properties_rent.csv'
    
    # Xóa file cũ nếu tồn tại để tránh ghi đè chèn lên dữ liệu cũ
    if os.path.exists(output_sale):
        os.remove(output_sale)
    if os.path.exists(output_rent):
        os.remove(output_rent)

    print(f"🚀 Bắt đầu tách file: {input_file}")
    start_time = time.time()
    
    # Biến đếm thống kê
    count_sale = 0
    count_rent = 0
    total_processed = 0
    
    # Cờ kiểm tra xem đã ghi header (tiêu đề cột) chưa
    first_chunk_sale = True
    first_chunk_rent = True

    try:
        # Đọc file theo từng chunk (lô) để tiết kiệm RAM
        # dtype={'listing_type': str}: Đảm bảo cột này đọc vào là chuỗi
        chunk_iter = pd.read_csv(input_file, chunksize=batch_size, low_memory=False)

        for chunk in chunk_iter:
            if 'listing_type' not in chunk.columns:
                print("❌ Lỗi: Không tìm thấy cột 'listing_type' trong file CSV.")
                return

            # Chuẩn hóa dữ liệu cột listing_type (xóa khoảng trắng, chuyển về chữ thường)
            # Để tránh lỗi do data bẩn (ví dụ: "For_Sale " khác "for_sale")
            chunk['listing_type'] = chunk['listing_type'].astype(str).str.strip().str.lower()

            # --- LỌC DỮ LIỆU ---
            # 1. Nhóm For Sale
            df_sale = chunk[chunk['listing_type'] == 'for_sale']
            
            # 2. Nhóm For Rent
            df_rent = chunk[chunk['listing_type'] == 'for_rent']

            # --- GHI FILE ---
            
            # Ghi file Sale
            if not df_sale.empty:
                mode = 'w' if first_chunk_sale else 'a' # 'w' cho lần đầu, 'a' (append) cho các lần sau
                df_sale.to_csv(output_sale, mode=mode, header=first_chunk_sale, index=False)
                count_sale += len(df_sale)
                first_chunk_sale = False

            # Ghi file Rent
            if not df_rent.empty:
                mode = 'w' if first_chunk_rent else 'a'
                df_rent.to_csv(output_rent, mode=mode, header=first_chunk_rent, index=False)
                count_rent += len(df_rent)
                first_chunk_rent = False

            total_processed += len(chunk)
            print(f"📦 Đã duyệt: {total_processed} dòng... (Sale: {count_sale} | Rent: {count_rent})")

        duration = time.time() - start_time
        print("\n✅ HOÀN THÀNH!")
        print(f"⏱️ Tổng thời gian: {duration:.2f} giây")
        print(f"🏠 Tổng For Sale: {count_sale} -> Lưu tại: {output_sale}")
        print(f"🔑 Tổng For Rent: {count_rent} -> Lưu tại: {output_rent}")
        print(f"∑ Tổng cộng: {count_sale + count_rent} (Các dòng khác/lỗi: {total_processed - count_sale - count_rent})")

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file đầu vào '{input_file}'")
    except Exception as e:
        print(f"❌ Lỗi không mong muốn: {e}")

if __name__ == "__main__":
    # Tên file CSV đầu vào (file kết quả từ bước tính điểm trước)
    INPUT_FILE = 'properties_scored_hybrid.csv' 
    
    split_csv_by_listing_type(INPUT_FILE)