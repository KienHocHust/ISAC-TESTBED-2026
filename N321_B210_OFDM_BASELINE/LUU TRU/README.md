# Lưu trữ các phần ít dùng

Đã chuyển nguyên 10 thư mục vào đây, không xóa dữ liệu và không sửa nội dung của các thử nghiệm/bản sao lưu:

| Thư mục | Nội dung |
|---|---|
| `BASELINE GOC/` | Flowgraph và Python baseline/tone, kiểm tra loopback/RF/offline cũ |
| `CHAN DOAN/` | Script, log benchmark, readback và IQ CAL cũ |
| `DATA TEST/` | Phép thử gửi từng số 1 → 10 |
| `TEST GNU THU PHÁT/` | Phép thử câu tiếng Việt HELLO |
| `TAI LIEU/` | Hướng dẫn, kết luận và danh sách di chuyển file ở lần sắp xếp trước |
| `rf_validation/` | Kết quả RF, log và IQ cũ |
| `device_backup/` | Bản sao lưu thiết bị trước thay đổi |
| `image_comparison/` | Image tham chiếu và kết quả đối chiếu |
| `image_trial_review/` | Kế hoạch thử/khôi phục, image và log benchmark |
| `uhd48_check/` | UHD 4.8 được giải nén riêng phục vụ kiểm tra |

`DANH_SACH_LUU_TRU.json` ghi vị trí cũ → mới. `README_TRUOC_KHI_LUU_TRU.md` giữ bản đồ thư mục của lần sắp xếp trước.

## Khi cần dùng lại

Các file bên trong được bảo toàn để lưu lại bằng chứng và cấu hình. Những tài liệu, JSON hoặc block GRC cũ có thể còn đường dẫn tuyệt đối ở vị trí trước khi chuyển. Không chạy nguyên các lệnh nạp/khôi phục image trong tài liệu lịch sử mà chưa đối chiếu vị trí và trạng thái thiết bị hiện tại.

Để khôi phục bố cục trước lưu trữ, chuyển thư mục cần dùng trở lại cùng cấp với `GNU THU PHAT/`, không ghi đè nếu đã có thư mục cùng tên. Một số nhóm phụ thuộc nhau: `DATA TEST/chay_lai.sh` dùng `BASELINE GOC/`; validator baseline dùng `rf_validation/`; bộ công cụ nạp image cũ tham chiếu `uhd48_check/` và `image_trial_review/`. Có thể đưa các nhóm liên quan trở lại cùng nhau hoặc cập nhật đường dẫn trước khi chạy.

**GNU THU PHAT đang dùng không phụ thuộc các thư mục lưu trữ này**, và vẫn nằm ở vị trí cũ ngoài `LUU TRU/`.
