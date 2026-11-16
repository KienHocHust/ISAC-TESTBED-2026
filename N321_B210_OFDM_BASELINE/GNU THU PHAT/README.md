# GNU THU PHAT — nguyên lý hoạt động của các block

Bài thực hiện truyền thông tin dạng văn bản từ USRP N321 sang USRP B210 qua ăng-ten. GNU Radio chuẩn bị dữ liệu, điều chế OFDM ở phía phát, rồi giải điều chế và lấy lại nội dung ở phía thu.

## Đường đi của thông tin

```text
message_text
    ↓
Vector Source
    ↓
Stream to Tagged Stream
    ↓
OFDM Transmitter
    ↓
Multiply Const — tx_scale
    ↓
Multiply Const — tx_enable
    ↓
UHD: USRP Sink → N321 → ăng-ten phát
                              ↓ sóng RF
UHD: USRP Source ← B210 ← ăng-ten thu
    ↓
ISAC Manual UTF-8 OFDM RX
    ↓
File Sink → file dữ liệu thu → check_rx.py
```

Các block QT GUI Frequency Sink nối nhánh từ đường tín hiệu để hiển thị phổ phát và phổ thu.

## Các block phía phát

| Block / biến | Chức năng |
|---|---|
| **message_text** | Chứa câu chữ người dùng muốn truyền. Đây là nội dung đầu vào của bài. |
| **Vector Source** | Lấy câu chữ, mã hóa thành byte UTF-8 và thêm phần đệm để tạo dữ liệu có độ dài gói theo cấu hình. Khi bật Repeat, nguồn lặp lại cùng nội dung. |
| **Stream to Tagged Stream** | Gắn tag độ dài để đánh dấu ranh giới các gói trong dòng byte. Bộ điều chế dựa vào tag này để xử lý từng gói. |
| **OFDM Transmitter** | Bổ sung CRC, header và phần đồng bộ; chuyển dữ liệu thành bit, ánh xạ BPSK và phân bố các ký hiệu lên sóng mang con. IFFT kết hợp các sóng mang thành mẫu IQ theo thời gian, sau đó thêm tiền tố chu kỳ CP. |
| **Multiply Const — tx_scale** | Điều chỉnh biên độ mẫu IQ trước khi đưa đến thiết bị phát. |
| **Multiply Const — tx_enable** | Cho tín hiệu đi qua khi bật truyền dữ liệu; đưa mẫu về không khi tắt. Block này không tạm dừng việc đọc dữ liệu của Vector Source. |
| **UHD: USRP Sink** | Gửi các mẫu IQ từ máy tính đến N321. Phần cứng N321 chuyển tín hiệu sang RF và phát qua ăng-ten. |

Cả câu trong `message_text` được đóng vào một gói khi còn nằm trong giới hạn độ dài cấu hình. Dấu cách giữa các từ hoặc các số không tự chia chúng thành những gói riêng. Một gói được mang bởi nhiều ký hiệu OFDM; trong mỗi ký hiệu, nhiều sóng mang con cùng mang dữ liệu.

## Các block phía thu

| Block | Chức năng |
|---|---|
| **UHD: USRP Source** | Nhận mẫu IQ từ B210. Phần cứng B210 thu sóng RF qua ăng-ten, chuyển xuống băng gốc và số hóa trước khi đưa dữ liệu về máy tính. |
| **ISAC Manual UTF-8 OFDM RX** | Tìm tín hiệu đồng bộ, căn thời điểm và bù lệch tần số; bỏ CP, thực hiện FFT để tách sóng mang con, ước lượng/cân bằng kênh và giải điều chế BPSK. Sau khi ghép lại byte, bộ thu kiểm tra CRC và xuất payload của gói hợp lệ. |
| **File Sink** | Ghi các byte payload đã giải mã vào file dữ liệu thu. Đây là dữ liệu sau bộ giải mã, không phải mẫu IQ thô. |
| **Tag Debug** | Hỗ trợ quan sát tag trong dòng dữ liệu sau giải mã để kiểm tra quá trình xử lý. Block này không trực tiếp hiển thị câu chữ. |

`check_rx.py` là chương trình kiểm tra bên ngoài flowgraph. Nó đọc file do File Sink ghi, giải mã văn bản và đối chiếu từng byte với nội dung kỳ vọng trong `message_text`. Câu kỳ vọng chỉ dùng để so sánh; nội dung thu thực tế vẫn đến từ tín hiệu B210 nhận được.

Gói không giải mã được hoặc không qua kiểm tra CRC sẽ không được xuất thành payload để chương trình đối chiếu. Vì vậy không có chữ mới xuất hiện chưa đủ để kết luận bên phát đã ngừng gửi.

## Các block quan sát và điều khiển

| Block / nhóm biến | Chức năng |
|---|---|
| **QT GUI Frequency Sink phía phát** | Hiển thị phổ của mẫu IQ trên đường phát trong máy tính. Đồ thị giúp quan sát tín hiệu trước khi phần cứng phát RF. |
| **QT GUI Frequency Sink phía thu** | Hiển thị phổ IQ ở đầu vào bộ giải mã. Có phổ tín hiệu chưa đồng nghĩa đã giải mã đúng nội dung. |
| **QT GUI Range** | Tạo thanh điều khiển để thay đổi một biến khi flowgraph đang chạy, chẳng hạn bật/tắt dữ liệu phát. |
| **Các Variable còn lại** | Cung cấp thông số dùng chung cho các block, như tần số, tốc độ lấy mẫu, độ dài gói, cấu hình OFDM và gain. |

## Các block bổ sung khi thử nhiễu

Nhánh thử nhiễu được đặt ở phía thu, trước bộ giải mã OFDM:

```text
UHD: USRP Source ──→ Add ──→ OFDM RX
                     ↑
                Noise Source
```

- **Noise Source:** tạo mẫu nhiễu Gaussian phức trong phần mềm.
- **Add:** cộng nhiễu với mẫu IQ nhận từ B210, rồi chuyển tín hiệu tổng đến bộ giải mã OFDM.
- **QT GUI Range điều chỉnh nhiễu:** thay đổi biên độ của Noise Source khi chạy.

Nhánh này thêm nhiễu sau khi B210 đã thu và số hóa tín hiệu. Nhiễu được dùng để khảo sát khả năng giải mã, không được phát từ N321 qua ăng-ten. Nếu Frequency Sink phía thu nối sau Add, đồ thị sẽ hiển thị tín hiệu đã cộng nhiễu.

## Phân biệt phần mềm và phần cứng

GNU Radio xử lý câu chữ, gói dữ liệu, điều chế/giải điều chế và mẫu IQ. N321 và B210 đảm nhiệm chuyển đổi giữa mẫu IQ và tín hiệu RF. Ăng-ten truyền và nhận sóng trong môi trường thực.

Việc nhận đúng nội dung được xác nhận bằng dữ liệu sau giải mã và đối chiếu câu chữ; các đồ thị phổ phục vụ quan sát tín hiệu trong quá trình đó.
