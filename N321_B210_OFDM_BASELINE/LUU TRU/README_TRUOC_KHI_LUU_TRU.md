# N321 → B210: bản đồ thư mục

Các file đã được gom theo mục đích. Không xóa kết quả đo, dữ liệu IQ, image hoặc bản sao lưu. Thư mục thao tác GNU Radio hiện tại vẫn là **GNU THU PHAT**.

| Thư mục | Nội dung |
|---|---|
| **[GNU THU PHAT](GNU%20THU%20PHAT/README.md)** | Flowgraph đang dùng để tự nhập câu chữ, phát/thu và chỉnh nhiễu Gaussian phía thu; dữ liệu trong `DATA/` của chính thư mục này |
| **[DATA TEST](DATA%20TEST/KET_QUA.txt)** | Phép thử gửi từng số 1 → 10; log, IQ, kết quả và script chạy lại |
| **[TEST GNU THU PHÁT](TEST%20GNU%20THU%20PHÁT/HUONG_DAN.txt)** | Phép thử câu tiếng Việt HELLO KIÊN TRẦN ĐÃ LÀM ĐƯỢC |
| **BASELINE GOC/** | Flowgraph baseline/tone ban đầu, Python sinh từ GRC, bộ kiểm tra RF/loopback/offline và payload baseline |
| **rf_validation/** | Kết quả thử tone/OFDM RF trước đây, log và IQ; giữ nguyên vị trí |
| **CHAN DOAN/** | Script chẩn đoán RF/CAL, log benchmark, readback clock/RFNoC, báo cáo và IQ CAL cũ |
| **TAI LIEU/** | Các hướng dẫn/kết luận lịch sử và danh sách vị trí cũ → mới của từng file |
| **device_backup/** | Bản sao lưu thiết bị trước khi thay đổi; giữ nguyên |
| **image_comparison/** | Image tham chiếu và kết quả đối chiếu; giữ nguyên |
| **image_trial_review/** | Kế hoạch, bản khôi phục, log nạp và benchmark image chuẩn; giữ nguyên |
| **uhd48_check/** | Bộ UHD 4.8 giải nén riêng để đối chiếu, không phải phần cài vào hệ thống |

## Chạy flowgraph bạn đang dùng

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE/GNU THU PHAT'
gnuradio-companion GNU_THU_PHAT.grc
```

Terminal thứ hai để xem câu thực thu:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE/GNU THU PHAT'
python3 -u check_rx.py
```

Xem `GNU THU PHAT/README.md` để biết cách bật/tắt TX và điều chỉnh nhiễu. Các bước sắp xếp thư mục không bật streaming/phát RF.

## Chạy lại các công cụ baseline cũ

Các file này trước đây nằm ngoài cùng, nay nằm chung trong `BASELINE GOC/` để giữ quan hệ import và cấu hình:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE/BASELINE GOC'
```

- `N321_B210_OFDM_BASELINE.grc`, `n321_b210_ofdm_baseline.py`: baseline cũ; cấu hình khác flowgraph đang dùng ở `GNU THU PHAT/`.
- `N321_B210_RF_TONE_CHECK.grc`, `n321_b210_rf_tone_check.py`: công cụ phát tone; chạy sẽ sử dụng radio.
- `run_ofdm_rf_baseline.sh`: phép thử RF hữu hạn 8 giây; chạy sẽ bật phát, lưu kết quả mới về `../rf_validation/`.
- `test_loopback.py`: kiểm tra phần mềm, không dùng USRP.
- `offline_decode_iq.py`: công cụ phân tích IQ cũ, không dùng USRP.

`DATA TEST/chay_lai.sh` đã được cập nhật để gọi validator trong `BASELINE GOC/`; các thư mục thử nghiệm khác giữ nguyên vị trí nên các block GRC riêng vẫn tìm được module.

## Tìm file đã chuyển

Xem **[TAI LIEU/DANH_SACH_DI_CHUYEN.json](TAI%20LIEU/DANH_SACH_DI_CHUYEN.json)**. File ghi tên cũ, vị trí mới và SHA256 trước khi cập nhật đường dẫn. Mỗi file đã được đối chiếu checksum ngay sau di chuyển. Các tài liệu lịch sử được thêm thông báo vị trí mới; lệnh cũ bên trong được giữ để bảo toàn bối cảnh đo.
