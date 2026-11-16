# Thí nghiệm OFDM: N321 phát → B210 thu, thêm AWGN

## File và mục tiêu

- `N321_B210_OFDM_AWGN.grc`: flowgraph GNU Radio Companion 3.10 được chuyển từ `ofdm_connectbladeRF.grc` bạn cung cấp. Sử dụng UHD thay cho Osmocom/bladeRF.
- `monitor_rx_payload.py`: xem dữ liệu ASCII nhận được trong `rx_payload.bin` theo thời gian thực, đếm gói hợp lệ sau CRC.
- `rx_payload.bin`: được tự tạo khi chạy GRC. Đây là dữ liệu sau giải điều chế và kiểm tra CRC, **không phải IQ thô**.

Luồng:

```text
message_text → Vector Source (byte) → Stream to Tagged Stream
    → OFDM TX (FFT 64, BPSK header, QPSK payload)
    → TX scale × 0.20 ──┐
                        Add → TX Enable (mặc định 0) → UHD USRP Sink (N321, TX/RX)
Complex AWGN (0→0.10) ┘                             ── sóng RF ──>
UHD USRP Source (B210, RX2) → OFDM RX → file rx_payload.bin
                                    ├→ Byte-time plot
                                    └→ RX tags (tuỳ chọn)
```

Nhiễu được cộng **trước khi N321 chuyển IQ thành RF**, nghĩa là bạn đang phát waveform có cả thông tin và nhiễu. Đây **không** phải nhiễu độc lập được phát từ vị trí thứ ba trong không gian. Nếu mục đích chỉ mô phỏng kênh AWGN mà không phát nhiễu ra ngoài, hãy đưa khối cộng nhiễu sang sau `UHD USRP Source` ở phía thu trong GRC.

## Kết nối phần cứng

- **N321 TX**: SFP0 (module SFP 1 GbE → RJ45) nối LAN laptop, IP N321 `192.168.180.3`, IP laptop `192.168.180.2/24`; ăng-ten vào `RF0 TX/RX`.
- **B210 RX**: USB 3.0 vào laptop, serial `F4A11D`; ăng-ten vào `RF A RX2`.
- Cả hai ăng-ten cần đúng dải tần, trở kháng 50 ohm và đầu SMA tương thích.
- Chỉ thực hiện **phát sóng** trên tần số được phép sử dụng trong điều kiện thí nghiệm có che chắn RF hoặc cấu hình kiểm soát phát xạ. **Không bật `TX ENABLE`** cho đến khi bạn xác nhận điều kiện an toàn và pháp lý. Bắt đầu với gain thấp, đặt ăng-ten cách nhau phù hợp để tránh quá tải đầu thu.
- Không cắm ăng-ten vào các cổng LO. Không nối TX trực tiếp với RX bằng cáp nếu thiếu bộ suy hao và kiểm tra công suất.

## Chuẩn bị và kiểm tra thiết bị

```bash
uhd_find_devices
uhd_usrp_probe --args "type=n3xx,addr=192.168.180.3,mgmt_addr=192.168.180.3"
uhd_usrp_probe --args "type=b200,serial=F4A11D"
```

Nếu UHD chưa nhận một trong hai USRP, sửa lỗi kết nối trước; `uhd_find_devices` thành công **không bảo đảm** streaming IQ đã chạy được. N321 hiện có MPM 4.8; laptop UHD 4.9. Nếu báo lỗi tương thích phiên bản, cần kiểm tra release notes và ảnh FPGA/firmware tương ứng trước khi nâng cấp.

## Chạy GNU Radio Companion

1. Lưu cả `.grc` và `monitor_rx_payload.py` vào **cùng một thư mục** trên máy Ubuntu (ví dụ `~/Downloads/ofdm_experiment/`).
2. Trong thư mục đó, mở GRC:

   ```bash
   cd ~/Downloads/ofdm_experiment
   gnuradio-companion N321_B210_OFDM_AWGN.grc
   ```

3. Bấm **Generate** (F5) rồi **Execute** (F6). Lúc khởi động, **`TX ENABLE=0`**, tức tín hiệu IQ đầu ra bị tắt; không phát thông điệp trước khi bạn chủ động bật.
4. Giá trị mặc định: `samp_rate=1e6`, `center_freq=2.45e9` (chỉ là **ví dụ kỹ thuật, không tự cấp quyền phát**), `tx_gain=0`, `rx_gain=20`, `tx_scale=0.20`, `noise_voltage=0`, `packet_len=64`.
5. Sau khi thử nghiệm RF được chuẩn bị an toàn, đổi **`TX ENABLE` sang 1**. Quan sát phổ RX B210. Bắt đầu `noise_voltage=0`, rồi tăng từng bước nhỏ `0.001`, `0.003`, `0.01` và xem số gói giải mã thành công thay đổi.
6. Chạy bộ xem ở Terminal **khác**, từ cùng thư mục:

   ```bash
   python3 monitor_rx_payload.py --file rx_payload.bin
   ```

7. Khi nhận tốt, màn hình sẽ tăng `RX accepted` / `matched` và nhận chuỗi:

   ```text
   HELLO N321 -> B210, OFDM AWGN TEST
   ```

   Chuỗi được đệm dấu cách thành 64 byte. Muốn đổi thông điệp, sửa biến `message_text` trong GRC và đảm bảo độ dài ASCII <= `packet_len` (64 byte). Chạy lại lệnh monitor với `--text '...'` tương ứng.
8. **Dừng phát**: đưa `TX ENABLE=0`, sau đó Stop flowgraph.

Nếu cửa sổ GUI hoặc biểu đồ làm máy chậm, bỏ kết nối một số `QT GUI` sink trong GRC. Không thêm `Throttle` vào luồng UHD: phần cứng USRP đã điều phối tốc độ streaming.

## Lỗi thường gặp

- **N321 không mở được stream**: xác nhận `sfp0` có `LOWER_UP`, `MTU=1500`, `ping 192.168.180.3`, thiết bị được probe mà **không còn** `No CHDR interfaces found`. Với FPGA `HG`, SFP0 1GbE dùng đường IQ.
- **B210 không khởi tạo**: xác nhận USB 3.0 và firmware `usrp_b200_fw.hex` được UHD tìm thấy (`UHD_IMAGES_DIR` nếu cần).
- **Không nhận được thông điệp**: kiểm tra RX antenna `RX2`, TX `TX/RX`, cùng tần số trung tâm, sample rate, khoảng cách ăng-ten, gain, đồng bộ OFDM; chú ý offset oscillator của hai thiết bị. Thử phát RF trong hệ đo có suy hao và che chắn trước.
- **Thiết bị báo underrun/overflow (`U`, `O`)**: giảm sample rate, đóng ứng dụng khác, kiểm tra Ethernet/USB và kích thước socket buffer.
- **GRC báo lỗi khối UHD**: mở thuộc tính từng UHD block, kiểm tra Device Address là `addr=192.168.180.3,mgmt_addr=192.168.180.3` và `serial=F4A11D`, Channel `0`, Antenna như trên. Tùy bản GRC, có thể cần chỉnh lại thông số trong dialog UHD.

## Diễn giải nhiễu, BER và phép đo

- `noise_voltage`: biên độ nhiễu Gaussian phức tạo trong phần mềm trước TX; **không phải số SNR (dB)**. Công suất tín hiệu, gain máy, suy hao đường truyền và nhiễu nền ảnh hưởng SNR thật ở RX.
- Bộ OFDM chuẩn có CRC32. Những gói CRC sai bị loại bỏ trước file `rx_payload.bin`; do đó monitor báo **số gói đã giải mã thành công**, **không phải BER thật** và cũng không đo được tỷ lệ mất gói chính xác do TX chưa gắn sequence number.
- Muốn đo PER/BER/SNR chặt chẽ cần thêm sequence number/truyền số bit cố định, bộ đồng bộ/matching và estimator công suất. Flowgraph này là bước thử truyền thông điệp + quan sát tác động nhiễu, chưa phải hệ đo BER đã hiệu chuẩn.

## Xác minh file

File `.grc` được xây dựng và kiểm tra **cú pháp YAML, danh sách block, và liên kết khối**. Môi trường dựng file không có GNU Radio / USRP thật nên **chưa thể chạy hoặc kiểm chứng thực nghiệm**; nếu GRC trên Ubuntu 3.10.12 của bạn hiển thị lỗi tạo code, gửi màn hình lỗi để chỉnh theo cài đặt chính xác của máy.
