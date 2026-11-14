# GNU THU PHAT — tự chọn câu phát và xem câu thu

Flowgraph phát văn bản UTF-8 bằng OFDM từ **N321 RF0 TX/RX**, thu bằng **B210 A RX2**. Câu mặc định là ` HELLO KIÊN TRẦN ĐÃ LÀM ĐƯỢC `, giữ một khoảng trắng ở mỗi đầu. Có nhánh cộng nhiễu Gaussian nhân tạo phía thu; mặc định `noise_amp = 0` nên chưa thêm nhiễu.

## Các file

| File/thư mục | Công dụng |
|---|---|
| `GNU_THU_PHAT.grc` | Flowgraph mở bằng GNU Radio Companion, chỉnh câu phát và xem sơ đồ |
| `gnu_thu_phat.py` | Python do GRC sinh, có cửa sổ phổ TX/RX |
| `DATA/` | Chứa dữ liệu thực thu và log; ban đầu chưa có phép đo của thư mục mới này |
| `check_rx.py` | Hiện câu thu được, so sánh từng byte với câu đã lưu trong GRC |
| `chay_gui.sh` | Sinh lại Python, mở GUI và lưu log, sao lưu dữ liệu khi GUI kết thúc |
| `payload_utils.py` | Mã hóa UTF-8, kiểm tra độ dài và đệm gói |
| `isac_ofdm_modem.py` | Bộ thu OFDM có ngưỡng đồng bộ và kiểm tra độ dài header; giữ thông tin GPL của GNU Radio |
| `isac_manual_ofdm_rx.block.yml` | Mô tả block thu riêng để GRC sử dụng |

## Chuẩn bị

- Giữ nguyên ăng-ten N321 **RF0 TX/RX** và B210 **A RX2**, cùng hướng, khoảng cách như lần thử gần nhất 15–20 cm.
- B210 nối USB 3; SFP N321 `192.168.180.3` nối laptop `192.168.180.2`; quản trị N321 `192.168.3.102` qua router/MINHDZ.
- Đóng các chương trình khác đang sử dụng hai USRP.
- Block riêng đã được đăng ký tại `/home/keindeptrai/.local/state/gnuradio/isac_manual_ofdm_rx.block.yml`. Nếu GRC đang mở sẵn, đóng rồi mở lại để nhận block.
- Giữ nguyên thư mục hiện tại: block và File Sink sử dụng đường dẫn tuyệt đối. Nếu chuyển thư mục, cần cập nhật đường dẫn rồi đăng ký/sinh lại.

## 1. Đổi câu phát bằng GNU Radio Companion

Mở terminal:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE/GNU THU PHAT'
gnuradio-companion GNU_THU_PHAT.grc
```

Nhấp đúp biến **message_text**, nhập chuỗi Python có dấu nháy, ví dụ `"XIN CHÀO KIÊN"`, rồi lưu **Ctrl+S**. Giới hạn **1–64 byte UTF-8**, không phải 64 ký tự; chữ có dấu có thể chiếm nhiều byte. Chương trình báo lỗi nếu câu vượt giới hạn. Giữ `packet_len = 64` và các thông số RF hiện tại.

Muốn đổi câu, dừng phiên đang chạy, sửa và lưu GRC rồi chạy lại. Khởi động lại monitor để nó đọc câu kỳ vọng mới.

## 2. Chạy phát/thu

Cách thuận tiện để có cả log và bản sao dữ liệu từng phiên: sau khi lưu GRC, chạy ở terminal:

```bash
bash chay_gui.sh
```

Hoặc nhấn **Generate → Execute** ngay trong GRC. Chỉ chọn một cách chạy tại một thời điểm.

Cửa sổ mở ra với **TX DATA = 0**. Chuyển sang **1** để phát lặp câu đã chọn; phổ trên hiển thị IQ phía phát, phổ dưới hiển thị IQ thu sau khi cộng nhiễu. Phổ phát là dữ liệu baseband phía máy tính, không phải phép đo công suất RF đã hiệu chuẩn. Phổ thu có tín hiệu cũng chưa đủ để kết luận đã nhận đúng câu.

**GUI không tự dừng sau 8 giây.** Khi kết thúc, chuyển TX DATA về **0**, rồi nhấn Stop/đóng cửa sổ để dừng streaming và giải phóng USRP. TX DATA = 0 chỉ đặt mẫu phát bằng 0, không giải phóng thiết bị.

## 3. Xem chữ thực thu và kiểm tra đúng/sai

Mở terminal thứ hai:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE/GNU THU PHAT'
python3 -u check_rx.py
```

Khi nhận được gói đúng, xuất hiện:

```text
THU ĐÚNG: ' HELLO KIÊN TRẦN ĐÃ LÀM ĐƯỢC '
bytes=... matched=... unexpected=... partial=...
```

Đây là ví dụ định dạng, không phải dữ liệu đo sẵn trong thư mục mới. `matched` đếm gói qua CRC và khớp **đủ 64 byte** với câu kỳ vọng có đệm; `unexpected` đếm gói qua CRC nhưng khác câu; `partial` là số byte chưa đủ gói. Không có gói thì không thể kết luận nhận đúng. Dừng monitor bằng Ctrl+C.

Bạn chọn **câu phát** và **câu kỳ vọng để so sánh**; nội dung thực thu do đường RF quyết định. Những gói mất hoặc bị CRC loại bỏ không xuất hiện trong file đầu ra. Các số đếm này không phải BER/PER.

## DATA chứa gì?

- `DATA/rx_payload.bin`: byte thực thu sau CRC, **bị ghi đè khi khởi chạy GUI mới**.
- `DATA/rx_messages.txt`: bản chữ do monitor tạo từ byte thực thu, hiện lại cả khoảng trắng đầu/cuối trong dấu nháy. Monitor tạo lại file khi nhận diện capture mới.
- `DATA/session_<thời-gian>_<PID>/`: khi chạy `chay_gui.sh`, chứa cấu hình, log sinh mã, log GUI và bản sao payload/bản chữ/kiểm tra **sau khi GUI đóng**. Tên thư mục riêng giúp giữ các phiên trước.

Nếu chạy trực tiếp từ GRC, hãy tự sao lưu hai file DATA trước lần chạy tiếp theo. Không xóa hay đổi tên file trong lúc đang thu. Không có IQ thô được ghi tự động trong flowgraph này; `.bin` là payload đã giải mã.

## Tín hiệu được xử lý như thế nào?

`Câu chữ → byte UTF-8 → đệm 64 byte → CRC + header + đồng bộ → BPSK/OFDM → mẫu IQ → N321 → sóng RF → B210 → mẫu IQ → cộng nhiễu Gaussian tùy chỉnh → đồng bộ/giải OFDM → kiểm tra CRC → byte → chữ UTF-8`.

Câu mặc định dài **39 byte**, thêm 25 byte khoảng trắng để đủ 64 byte. BPSK mang một bit trên một ký hiệu dữ liệu; OFDM đặt các ký hiệu lên nhiều sóng mang con. Phần header, pilot, đồng bộ và CRC là thông tin bổ sung của hệ thống, không phải chữ người dùng nhập.

## Cấu hình và giới hạn hiện tại

| Thông số | Giá trị |
|---|---|
| Tần số phát | 2,45 GHz |
| Tần số đặt bên thu | 2,4500114 GHz, bù lệch đo được +11.400 Hz |
| Tốc độ mẫu | 200 kS/s |
| TX/RX gain | 30 / 60 dB |
| FFT / CP | 64 / 16 mẫu |
| Header / payload | BPSK / BPSK |
| Biên độ TX | 0,8/64 = 0,0125 để chuẩn hóa IFFT |
| Ngưỡng đồng bộ thu | 0,3 |
| Payload | 64 byte UTF-8 có đệm |

TX gain là cấu hình gain của radio, không phải công suất đo tại ăng-ten. Trước đó câu mặc định đã thu đúng 7 gói bằng script RF trong thư mục `TEST GNU THU PHÁT`; đường truyền vẫn mất gói. Thư mục này được đóng gói lại để thao tác trong GRC, **chưa chạy RF/GUI tại đây**. GRC đã được kiểm tra sinh Python; không cam kết mỗi lần chạy đều thu được câu.

Nếu không thu được: kiểm tra TX DATA = 1, giữ đúng các cổng ăng-ten, USB/SFP và mạng quản trị, xem log UHD, rồi kiểm tra monitor đọc đúng câu GRC đã lưu. Không tăng gain vượt 30 dB trong cấu hình đã duyệt.


## Điều chỉnh nhiễu phía thu

Đã nối `B210 UHD Source → Add → OFDM RX`, với `Noise Source (Complex, Gaussian) → đầu vào còn lại của Add`. Đồ thị RX cũng lấy đầu ra Add. Đây là nhiễu phần mềm sau ADC B210; không phát nhiễu qua ăng-ten và không mô phỏng bão hòa ADC.

Thanh `RX Gaussian noise amplitude (0 = off)` chạy từ 0 đến 0.01, bước 0.0001. Bắt đầu ở 0 để thu thử, sau đó tăng từng bước nhỏ. Giá trị này là biên độ IQ tuyến tính, **không phải dB hay SNR**. Tổng `matched` không giảm khi tăng nhiễu; quan sát số gói mới tăng trong các khoảng thời gian bằng nhau. Môi trường RF còn biến động nên số gói ít hơn một lần chưa đủ quy hết nguyên nhân cho nhiễu nhân tạo.

File trước khi nối nhiễu được giữ ở `GNU_THU_PHAT.before_rx_noise.grc`. Sau khi sửa file từ bên ngoài, đóng tab GRC cũ **không lưu đè**, rồi mở lại `GNU_THU_PHAT.grc` để nạp đường nối mới. Đã sinh Python thành công; chưa chạy RF để đo tác động của nhánh nhiễu.
