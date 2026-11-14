# N321 phát → B210 thu: xác nhận thông điệp trước khi thêm nhiễu

Tất cả file mới nằm trong thư mục `N321_B210_OFDM_BASELINE`; các file gốc được giữ nguyên.

## 1. Nội dung đã chỉnh

- `N321_B210_OFDM_BASELINE.grc`: flowgraph mở bằng GNU Radio Companion 3.10.
- `n321_b210_ofdm_baseline.py`: mã đã sinh bằng `grcc` 3.10.12.0; có thể chạy trực tiếp.
- `check_rx.py`: đọc cấu hình thông điệp từ GRC, kiểm tra byte thu được và hiển thị số payload khớp.
- `test_loopback.py`: thử OFDM trong phần mềm, không mở USRP, không phát RF.
- `loopback_payload.bin`: dữ liệu mẫu từ bài kiểm tra phần mềm, **không phải dữ liệu thu qua ăng-ten**.

Đã bỏ hoàn toàn Noise Source, Add và thanh chỉnh nhiễu. Đã bỏ biểu đồ byte theo thời gian có trục tốc độ lấy mẫu IQ dễ gây hiểu nhầm. Giữ hai phổ TX/RX, bộ thu OFDM và file dữ liệu sau CRC. Biểu thức tạo byte đã chỉnh để GRC sinh đúng callback cập nhật thông điệp.

```text
ASCII lặp lại → Tagged Stream (64 byte) → OFDM TX → ×0.20 → ×TX DATA
 → UHD N321 → RF → UHD B210 → OFDM RX → CRC → rx_payload.bin
```

Không thêm nhiễu nhân tạo; đường truyền thực vẫn có nhiễu nền, suy hao và lệch tần số.

| Thông số | Giá trị |
|---|---|
| N321 | `addr=192.168.180.3,mgmt_addr=192.168.180.3,master_clock_rate=200e6` |
| N321 subdevice / antenna | `A:0` / `TX/RX`, tương ứng RF0 |
| B210 | `serial=F4A11D` |
| B210 subdevice / antenna | `A:A` / `RX2`, tương ứng RF A RX2 |
| Channel | 0 cho mỗi thiết bị |
| Tần số trung tâm | 2.45 GHz, giữ từ bản gốc; thay theo tần số thí nghiệm của bạn |
| Sample rate | 500 kS/s ở cả hai thiết bị; N321 master clock 200 MHz |
| FFT / CP | 64 / 16 |
| Sóng mang dữ liệu / pilot | 48 / 4 |
| Điều chế | BPSK header, QPSK payload |
| TX gain / RX gain | 10 dB / 20 dB |
| TX scale / TX DATA khi mở | 0.5/fft_len = 0.0078125 / 0 |
| Payload | 64 byte, thông điệp ASCII đệm dấu cách |

Thông điệp giữ nguyên từ bản gốc để dễ đối chiếu:

```text
HELLO N321 -> B210, OFDM AWGN TEST
```

Chữ `AWGN TEST` chỉ là nội dung văn bản; flowgraph này không có khối tạo nhiễu.

## 2. Kiểm tra thiết bị

Ăng-ten N321 ở **RF0 TX/RX**, B210 ở **A RX2** như kết nối bạn đã mô tả. Đóng các chương trình khác đang chiếm USRP. Chạy:

```bash
uhd_find_devices
uhd_usrp_probe --args "type=n3xx,addr=192.168.180.3,mgmt_addr=192.168.180.3"
uhd_usrp_probe --args "type=b200,serial=F4A11D"
```

Đối chiếu IP và serial với thiết bị thực. Nếu khác, sửa `Device Address` trong khối UHD tương ứng rồi Generate lại. Trong kết quả probe, kiểm tra tên subdevice: N321 `A:0`, B210 `A:A`; nếu UHD của máy liệt kê tên khác thì chọn đúng tên được probe báo.

## 3. Mở và chạy flowgraph

Terminal 1:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE'
gnuradio-companion N321_B210_OFDM_BASELINE.grc
```

1. Kiểm tra `center_freq`, IP và serial; hai UHD block dùng chung `center_freq` và `samp_rate`.
2. Nhấn **F5 Generate**, sau đó **F6 Execute**.
3. Cửa sổ hiện hai phổ, `TX DATA = 0`. Phổ RX lúc này có thể có nhiễu nền.
4. Trong điều kiện phát RF của phòng thí nghiệm và tại tần số được phép, chuyển **TX DATA = 1** để phát thông điệp. Ban đầu giữ gain như bảng trên.

`TX DATA = 0` nhân mẫu IQ với 0; UHD Sink vẫn đang chạy. Đây không phải lệnh tắt hoàn toàn phần cứng RF. Muốn kết thúc phiên streaming, bấm Stop flowgraph.

Có thể chạy mã đã sinh thay cho GRC, không chạy đồng thời hai cách:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE'
/usr/bin/python3 n321_b210_ofdm_baseline.py
```

Luôn chạy từ thư mục này: `rx_payload.bin` được ghi theo thư mục làm việc và **bị ghi đè mỗi lần khởi động flowgraph**.

## 4. Kiểm tra dữ liệu nhận được

Terminal 2, có thể mở trước khi bật TX DATA:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE'
/usr/bin/python3 check_rx.py
```

Khi thu và giải mã đúng, chương trình sẽ in ví dụ:

```text
First matching payload: b'HELLO N321 -> B210, OFDM AWGN TEST ...'
RX bytes=6400 matched=100 unexpected=0 partial=0
```

`...` trong ví dụ minh họa phần đệm; dữ liệu thật được in đầy đủ bằng `repr`, với dấu cách ở cuối để đủ 64 byte.

- `matched`: số payload 64 byte giống hoàn toàn thông điệp dự kiến.
- `unexpected`: số nhóm 64 byte khác thông điệp dự kiến; mục tiêu là 0.
- `RX bytes`: tổng số byte đã đọc từ file.
- `partial`: byte còn chờ để đủ nhóm 64 byte; khi đang đọc trực tiếp có thể tạm khác 0.

Tiêu chí ban đầu: `matched` tăng liên tục, `unexpected=0`. Chỉ nhìn thấy phổ RX chưa chứng minh đã nhận đúng thông tin.

Sau khi thu một lúc: chuyển TX DATA về 0, **Stop flowgraph**, rồi kiểm tra toàn bộ file đã đóng:

```bash
/usr/bin/python3 check_rx.py --once
```

`PASS` và mã thoát 0 nghĩa là file chứa ít nhất một payload khớp, không có nhóm sai và không dư byte. File rỗng, thiếu file, dữ liệu khác hoặc nhóm cuối chưa đủ sẽ báo thất bại và mã thoát 1. Dùng Ctrl+C để dừng chế độ theo dõi.

`rx_payload.bin` là payload sau CRC, không phải IQ. Gói sai CRC bị bộ thu loại bỏ; vì vậy PASS chứng minh các byte đã lưu khớp thông điệp, **chưa chứng minh mọi gói phát đều đến nơi**, chưa đo BER/PER hoặc lượng gói đã phát. Chưa có số thứ tự gói trong payload. Monitor chia file thành nhóm cố định 64 byte theo cấu hình thí nghiệm này.

## 5. Nếu không có dữ liệu

1. Xác nhận TX DATA đã bằng 1 và Terminal không báo lỗi khởi tạo UHD.
2. Kiểm tra đúng B210 A RX2, N321 RF0 TX/RX, đúng IP/serial. Hai bên phải cùng tần số và sample rate.
3. Xem phổ TX có xuất hiện khi bật dữ liệu không; xem phổ RX có thay đổi tương ứng không. Trục phổ hiện là tần số tương đối quanh 0, ứng với `center_freq` đã cấu hình.
4. Nếu thấy tín hiệu nhưng không giải mã được: tránh đặt ăng-ten quá gần; thử chỉnh RX gain từng bước nhỏ rồi chạy lại. Tăng gain quá cao có thể làm quá tải RX. Không nối trực tiếp TX vào RX bằng cáp nếu chưa có suy hao phù hợp.
5. Nếu có `U`/`O`, kiểm tra Ethernet N321, USB 3 của B210 và tải máy. Chưa thêm Throttle vào flowgraph phần cứng.
6. Hai USRP hiện dùng clock độc lập, không ép đồng bộ thời gian. Nếu phổ có tín hiệu nhưng vẫn không có payload sau khi chỉnh mức thu, cần kiểm tra lệch tần số và đồng bộ OFDM bằng log/thực nghiệm; bản này chưa bù offset thủ công.
7. Nếu `unexpected` tăng: kiểm tra thông điệp GRC và bản Python đang chạy có cùng cấu hình không, Generate lại sau khi sửa; dừng capture cũ và chạy lại.

## 6. Đổi thông điệp

Dừng flowgraph, sửa biến `message_text` trong GRC, dùng 1–64 byte ASCII, F5 rồi F6. Công cụ kiểm tra tự đọc thông điệp từ GRC nên không cần sửa hai nơi. Không dùng tiếng Việt có dấu ở bước kiểm tra này. Nếu sửa `packet_len`, công cụ cũng đọc lại độ dài đó, nhưng nên giữ 64 cho lần thử đầu.

## 7. Tự kiểm tra phần mềm

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE'
/usr/bin/python3 test_loopback.py
/usr/bin/python3 check_rx.py --file loopback_payload.bin --once
```

Loopback đọc các thông số OFDM từ GRC và nối TX → scale → RX trong phần mềm. Throttle chỉ dùng ở bài thử này vì không có USRP điều phối tốc độ. Không dùng bài thử này để xác nhận kết nối vô tuyến.

Kết quả đã chạy khi chuẩn bị bộ file: `grcc` 3.10.12.0 biên dịch thành công; loopback khớp 2.083 payload = 133.312 byte. Số payload ở lần chạy khác có thể thay đổi theo thời gian xử lý. Chưa bật phát RF hoặc xác minh đường truyền hai USRP thực tế.

## 8. Điều chỉnh sau khi đọc run_log.txt

Log thực tế báo TX bị làm tròn từ 1 MHz xuống khoảng 0.999 MHz, cảnh báo bộ đệm gửi UDP và underflow liên tục. Chưa xác định được nguyên nhân duy nhất của underflow.

Đã cập nhật GRC và sinh lại Python: N321 dùng `master_clock_rate=200e6`, cả TX/RX yêu cầu 500 kS/s để giảm tải và cho tỷ số clock/sample rate nguyên. Đã chạy lại vòng lặp phần mềm, khớp 1.037 payload = 66.368 byte. Kết quả 2.083 payload ở mục 7 là lần thử trước khi đổi tốc độ.

Sau khi dừng flowgraph, chạy lệnh UHD đề nghị trong log để tăng giới hạn bộ đệm gửi:

```bash
sudo sysctl -w net.core.wmem_max=2500000
```

Đây là thay đổi tạm thời của hệ điều hành, không sửa cấu hình khởi động. Chưa chạy lệnh này thay bạn. Việc bỏ cảnh báo bộ đệm không bảo đảm hết underflow.

Chạy lại từ đúng thư mục, ghi log mới để giữ nguyên log cũ:

```bash
/usr/bin/python3 -u n321_b210_ofdm_baseline.py > run_log_500k.txt 2>&1
```

Bật TX DATA=1 khoảng 5–10 giây rồi đóng cửa sổ. Kiểm tra log mới còn cảnh báo làm tròn tốc độ hoặc underflow liên tục không; chạy `check_rx.py --once` và gửi cả log cùng kết quả. Nếu còn underflow, bước tiếp theo là kiểm tra streaming TX riêng và đường Ethernet, chưa tăng gain hoặc thêm nhiễu.

Tài liệu đối chiếu: https://kb.ettus.com/N320/N321 và https://files.ettus.com/manual/page_transport.html.

## 9. Thử TX gain 10 dB

Theo yêu cầu, đã đổi `tx_gain=10` trong GRC và sinh lại Python bằng grcc. RX gain vẫn 20 dB, sample rate vẫn 500 kS/s. Đây là gain dB, không phải công suất phát dBm.

Dừng mọi flowgraph cũ, rồi chạy từ Terminal:

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE'
/usr/bin/python3 -u n321_b210_ofdm_baseline.py > run_log_tx10.txt 2>&1
```

Giữ TX DATA=0 khoảng 5 giây và chụp phổ RX, sau đó TX DATA=1 khoảng 10 giây và chụp lần hai. Chuyển về 0 rồi đóng cửa sổ biểu đồ. Kiểm tra file payload sau khi dừng:

```bash
/usr/bin/python3 check_rx.py --once > check_rx_tx10.txt 2>&1
cat check_rx_tx10.txt
```

Gửi hai ảnh, `run_log_tx10.txt` và `check_rx_tx10.txt`. Mỗi lần chạy các lệnh chuyển hướng này sẽ ghi đè file log tương ứng; file RX cũng bị ghi đè khi khởi động flowgraph. Chưa chạy phát RF thay bạn.

## 10. Kiểm tra đường RF bằng tone +50 kHz

Sau lần thử TX gain 10 dB, log không báo underflow nhưng payload vẫn 0 byte. Hai file mới `N321_B210_RF_TONE_CHECK.grc` và `n321_b210_rf_tone_check.py` dùng cùng hai USRP, cùng tần số 2.45 GHz, tốc độ 500 kS/s và gain 10/20 dB; thay OFDM bằng tone phức +50 kHz. Biên độ tone sau scale là 0.01. Không giải mã payload, không ghi đè rx_payload.bin. Chỉ chạy một flowgraph tại một thời điểm.

```bash
cd '/home/keindeptrai/Desktop/ISAC TESTBED/N321_B210_OFDM_BASELINE'
/usr/bin/python3 -u n321_b210_rf_tone_check.py > run_log_tone.txt 2>&1
```

Chụp hai phổ khi TX DATA=0 và khi =1, mỗi trạng thái chờ 5 giây. Khi =1, phổ TX phải có đỉnh ở +50 kHz; tìm đỉnh xuất hiện tương ứng trên phổ B210 gần +50 kHz (có thể lệch do clock độc lập). Đỉnh ở 0 kHz có sẵn cả khi TX=0 không đủ để xác nhận nhận tone. Nếu không thấy đỉnh thay đổi theo bật/tắt, kiểm tra cáp, ăng-ten và ánh xạ cổng; chưa suy ra lỗi bộ giải mã OFDM. Khi xong, chuyển về 0 rồi đóng cửa sổ và gửi hai ảnh cùng run_log_tone.txt. Không dùng check_rx.py cho bài thử tone vì không truyền thông điệp. Chưa chạy RF thay bạn; biên dịch grcc và cú pháp Python đã kiểm tra thành công.

## 11. Kiểm tra tự động trực tiếp trên phần cứng

Đã truy cập N321 qua Ethernet/SSH và B210 qua USB. Các script diagnose_rf.py và diagnose_n321_internal.py là công cụ chẩn đoán, không phải bài truyền payload. Kết quả trong diagnostic_summary.json và các file diagnose_*_log.txt / *_results.json. Bản OFDM vẫn TX gain 10 dB, RX gain 20 dB, sample rate 500 kS/s. Các lần thử tăng RX gain và đường CAL không thay đổi giá trị mặc định của flowgraph. Các stream kiểm tra đã dừng.

Thông tin ăng-ten người dùng cung cấp: 617–960 / 1700–6000 MHz, AUG22; dải ghi trên nhãn bao gồm 2.45 GHz.

Phát hiện cần xử lý trước khi thử OFDM tiếp: benchmark_rate chính thức của UHD, chỉ thu N321, ở 500 kS/s trong 5 giây chỉ nhận 312.929 mẫu (xấp xỉ 62.586 mẫu/giây), không báo drop/overrun. Thử master clock 250 MHz và 625 kS/s trong 3 giây nhận 234.358 mẫu (xấp xỉ 78.119 mẫu/giây). Hai phép thử đều chỉ đạt khoảng 1/8 số mẫu dự kiến. Do vậy việc log không có U chưa đủ để kết luận streaming đã đúng. Đây là bất thường được đo, chưa xác định nguyên nhân duy nhất.

Host báo UHD 4.9.0.1; thiết bị báo MPM 4.8.0.0, FPGA 8.2 và git fffffff.dirty. Cần xác nhận nguồn gốc image và kiểm tra sự tương thích của bộ driver/image. Không kết luận chỉ từ git dirty rằng image đã bị người dùng sửa. Đã sao lưu n320.bin, n320.dts, n320.dtbo cùng mã MPM vào device_backup/n321_before_changes.tar và ghi SHA256 trong diagnostic_summary.json. Chưa nạp firmware, sửa EEPROM hoặc ghi bảng hiệu chuẩn. Không tự ghi đè image khi chưa biết đó có phải thiết kế riêng của phòng lab.

Các phép thử tone/CAL ngắn chưa thấy đỉnh theo bật/tắt phát; kết quả này chưa đủ để kết luận cáp, ăng-ten hay phần cứng bị hỏng, vì bất thường tốc độ và bộ đệm có thể ảnh hưởng thời điểm dữ liệu tới đầu phát. Giữ lại log để chẩn đoán tầng streaming trước.

Cập nhật chẩn đoán cuối: thông tin lịch sử image từ người dùng chưa rõ và thiết bị đã được nhiều nhóm dùng thiết kế FPGA. Giữ nguyên image hiện có. Thử nghiệm TX rate factor 8 gây underflow nên không áp dụng. Bộ UHD 4.8 giải nén riêng chưa chạy được do thiếu libpython3.13.so.1.0 và tải phụ thuộc bị timeout; chưa có kết quả đối chiếu phiên bản. Xem KET_QUA_KIEM_TRA.txt để biết kết quả đã đo và công việc chưa hoàn tất.

## 12. Sửa chuẩn hóa IQ trước UHD và kiểm tra RF trên image chuẩn

Bản trước thiếu chuẩn hóa đầu ra IFFT: ghi IQ thực tế ở tx_scale=0.8 cho đỉnh khoảng 59.289, vượt full scale mặc định 1.0 của UHD. Kiểm tra loopback float trong phần mềm không phát hiện lỗi này vì không đi qua bộ chuyển đổi IQ/DAC. Đã sửa baseline thành tx_scale=0.5/fft_len và sinh lại Python. Đỉnh IQ đã ghi lại sau sửa là 0.579, RMS khoảng 0.092. Các mục/lệnh lịch sử dùng tx_scale=0.20 hoặc 0.8 trực tiếp đã được thay thế bởi công thức chuẩn hóa mới; không tái sử dụng các mức scale cũ cho OFDM. Flowgraph tone có biên độ riêng nên không dùng công thức OFDM này.

IP quản trị trong baseline và tone đã cập nhật thành 192.168.3.102; địa chỉ streaming SFP vẫn 192.168.180.3. Image chuẩn hiện đã qua ba benchmark RX. Phép thử tone xuất hiện gần +61.4 kHz thay vì +50 kHz, dùng làm ước lượng ban đầu bù phía thu +11.4 kHz. Đây là ước lượng thực nghiệm, có thể thay đổi theo nhiệt độ/clock, chưa phải hiệu chuẩn tuyệt đối.

validate_ofdm_rf.py là phép thử RF tự động có giới hạn thời gian. Đọc cấu hình OFDM và thông điệp từ GRC; không thêm nhiễu, dừng cả hai stream khi xong. Payload/IQ và báo cáo nằm trong rf_validation/, tách khỏi rx_payload.bin của GUI. Kết quả CRC-passed vẫn chưa phải BER/PER. Thử ở TX gain 10 dB chưa nhận payload; đang kiểm tra 20 rồi tối đa 30 dB theo chấp thuận riêng của người dùng. Chưa đưa RX gain/frequency offset của thử nghiệm vào GUI cho đến khi có kết quả đúng.

Tham chiếu miền IQ UHD: https://files.ettus.com/manual_archive/v4.9.0.0/html/page_configuration.html (fullscale floating point mặc định 1.0).
