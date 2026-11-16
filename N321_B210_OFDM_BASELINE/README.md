# N321 → B210: phát và thu bằng GNU Radio

Thư mục hiện dùng hằng ngày là **[GNU THU PHAT](GNU%20THU%20PHAT/README.md)**. Các thử nghiệm, chẩn đoán, hướng dẫn cũ và bản sao lưu đã được chuyển vào **[LUU TRU](LUU%20TRU/README.md)**; không xóa dữ liệu.

```text
N321_B210_OFDM_BASELINE/
├── GNU THU PHAT/  ← flowgraph đang dùng; DATA/ nằm bên trong
├── LUU TRU/      ← 10 thư mục ít dùng và bản sao lưu
└── README.md
```

## Mở flowgraph đang dùng

```bash
cd '/home/kiendeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE/GNU THU PHAT'
gnuradio-companion GNU_THU_PHAT.grc
```

Giữ `noise_amp = 0` để thử không cộng nhiễu, chạy flowgraph rồi đặt TX DATA = 1 khi muốn phát.

Terminal khác để xem câu thu:

```bash
cd '/home/kiendeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE/GNU THU PHAT'
python3 -u check_rx.py
```

Hoặc chạy `bash chay_gui.sh` trong cùng thư mục để sinh mã và lưu log từng phiên. Không chạy hai flowgraph cùng lúc. Chi tiết đổi câu, điều chỉnh nhiễu và dừng thiết bị nằm trong README của `GNU THU PHAT/`.

Vị trí và nội dung file của `GNU THU PHAT/` không bị thay đổi trong bước lưu trữ, nên các đường dẫn block riêng và DATA đang dùng được giữ nguyên. Không bật streaming/phát RF trong bước này.
