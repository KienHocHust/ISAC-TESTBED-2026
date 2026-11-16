LƯU Ý SẮP XẾP THƯ MỤC: mã nguồn/flowgraph baseline đã chuyển vào BASELINE GOC; log chẩn đoán cũ ở CHAN DOAN. Các lệnh/đường dẫn trong tài liệu lịch sử bên dưới có thể là vị trí cũ. Xem README.md ngoài cùng để chạy theo cấu trúc mới.

# Thử OFDM qua RF, ngày 14/11/2026

Đã thu đúng payload qua RF, nhưng chưa ổn định: hai lần cùng cấu hình, mỗi lần bật dữ liệu 8 giây, thu lần lượt 253 và 6 gói qua CRC; tất cả gói thu được đều khớp payload 64 byte. Lần hai chưa đạt điều kiện kiểm tra tối thiểu 10 gói. Không suy ra BER/PER từ những số này.

Cấu hình thử: N321 RF0 TX/RX → B210 A RX2 qua hai ăng-ten cách 15–20 cm; 2,45 GHz; TX gain 30 dB; RX gain 60 dB; 200 kS/s; BPSK; RX offset +11.400 Hz; ngưỡng đồng bộ 0,3; biên độ TX 0,8/64. Chưa thêm nhiễu nhân tạo. Đây là cấu hình script thử riêng; GUI/GRC vẫn giữ các giá trị baseline trước đó, gồm TX gain 10 dB.

Đóng chương trình khác đang dùng USRP, giữ SFP, USB B210 và mạng quản trị. Chạy:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE'
bash run_ofdm_rf_baseline.sh
```

Script tự bật dữ liệu 8 giây rồi dừng hai luồng. Mỗi lần tạo thư mục `rf_validation/manual_<thời-gian>_<PID>/` chứa `run.log`, báo cáo JSON và payload `.bin`; đường dẫn được in ở đầu. Muốn lưu thêm IQ TX/RX:

```bash
bash run_ofdm_rf_baseline.sh --capture-iq
```

Đọc JSON ở cuối log: `matched` là số gói đúng; `unexpected` và `partial_bytes` cần bằng 0; `passed: true` đòi ít nhất 10 gói đúng và không có dữ liệu khác. Mã thoát 1 khi chưa đạt điều kiện này, kể cả khi đã thu được vài gói đúng. Log còn có lỗi header và cảnh báo `Failed to create stream fd`; chưa xác định hết ảnh hưởng, nên chưa gọi đường truyền ổn định.

Log đã đo: `rf_validation/close_antennas_20261114_log.txt` (253 gói), `rf_validation/close_antennas_repeat_20261114_log.txt` (6 gói). IQ lần đầu ở `rf_validation/close_antennas_20261114/`. Cả hai lần streaming đã dừng.
