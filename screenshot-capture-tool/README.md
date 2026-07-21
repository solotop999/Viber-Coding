# Solotop Capture

- Công cụ chụp màn hình cho Windows: nhẹ, nhanh và đẹp.
- Hỗ trợ ghi chú, bo viền, tạo nền mờ/nền màu để làm nổi bật nội dung
- Có khung hướng dẫn tỉ lệ và cảnh báo ảnh nhỏ để đăng lên X (Twitter) rõ nét hơn.

100% Open-source. Chạy offline, không thu thập dữ liệu, không tracking, không chạy nền, không quảng cáo, sạch và minh bạch.

![Screenshot 2026-03-31 113711](https://github.com/user-attachments/assets/791753f6-d48e-454e-80b8-b9cc235af507)

---

## Đổi watermark

Watermark chữ được bật sẵn với nội dung `𝕏: @solotop999`. Watermark chỉ xuất hiện ở góc phải phía dưới của **Background**, không đè lên nội dung ảnh chụp.

1. Sau khi chụp ảnh, giữ **Background** ở trạng thái bật.
2. Bấm **Mark** trên thanh công cụ.
3. Bật hoặc tắt watermark, nhập nội dung mới và chỉnh **Opacity**.
4. Bấm **Save** trong hộp thoại. Thiết lập được lưu cục bộ cho lần mở sau.

Watermark được áp dụng cho cả **Copy** và **Save**. Khi tắt **Background**, watermark sẽ không xuất hiện.

---

## Chèn icon vào ảnh

Sau khi chụp, assets/icon.png được thêm tự động ở góc dưới bên trái của ảnh đầu ra.

- Kéo icon đến bất kỳ vị trí nào, kể cả phần **Background** bên ngoài screenshot.
- Kéo tay nắm ở góc trên bên phải để phóng to hoặc thu nhỏ mà không làm méo ảnh.
- Bấm nút **Icon** trên toolbar để bật hoặc tắt icon.
- Trạng thái bật/tắt được lưu cho lần capture và lần mở ứng dụng tiếp theo.
- Kích thước icon hiện tại được ghi nhớ khi bấm **Copy**; vị trí mặc định vẫn là góc dưới bên trái.
- Icon được áp dụng cho cả **Copy** và **Save**.

---
### Ảnh đẹp ngay khi chụp — sẵn sàng đăng X

Đây là tính năng hay nhất.

Khi bạn chụp xong, ảnh screenshot tự động được **bo góc mềm mại**. Bật **Background** lên là có ngay một lớp nền phía sau ảnh chụp — biến một screenshot thường thành một hình ảnh có bố cục đẹp, sẵn sàng đăng bài.


**Layouts chuẩn tỉ lệ mạng xã hội:**
| Layout | Tỉ lệ | Dùng cho |
|--------|--------|----------|
| Original | Giữ nguyên | Chia sẻ nhanh |
| Portrait | 4:5 | Post Instagram, X |
| Landscape | 16:9 | Banner, header |
| Phone | 9:16 | Story, Reels |

Ảnh xuất ra có shadow, bo góc, background — không cần qua Figma hay Canva.

---

## Chạy từ source

```bash
pip install -r requirements.txt
python main.py
```

## Build `.exe`

```bash
python -m PyInstaller --clean --noconfirm build.spec
```

Output: `dist/capture.exe`

## Bản phát hành sẵn

- **[⬇️ Tải Solotop Capture cho Windows](https://github.com/solotop999/Viber-Coding/raw/refs/heads/main/screenshot-capture-tool/Solotop%20Capture.exe)**
- File dùng ngay: `Solotop Capture.exe` — tải về và mở, không cần cài đặt
- Kích thước: `39,617,170 bytes` (~37.8 MiB)
- MD5: `5520A9580333D37ED427C744B5906C91`
- SHA-256: `73FD1FFAF5747FC4B44637E5F00AF0F03D67076AB85E93384FA017E1C0DDD73A`

## Hỗ trợ

- Windows 10
- Windows 11

---

### An toàn tuyệt đối

Tool này **không kết nối mạng**. Không có server, không có tài khoản, không có analytics, không có crash reporting, không có auto-update.

Cụ thể hơn:
- Code ứng dụng không gửi network request; các network client Python và Qt WebEngine không dùng đã được loại khỏi bản build.
- Không có `eval`, `exec`, `subprocess`, hay bất kỳ cách nào chạy code bên ngoài.
- Không auto-start cùng Windows. Không system tray. Không chạy nền.
- Ảnh chỉ rời khỏi app khi bạn chủ động bấm **Copy** hoặc **Save**.
- Settings lưu tại `%LOCALAPPDATA%` dưới dạng JSON thuần, chỉ chứa các tùy chọn giao diện và background.
- Background image custom chỉ chấp nhận **đường dẫn local tuyệt đối** — chặn UNC path và network path.

**Redact an toàn:**
Khi bạn dùng Redact để che thông tin nhạy cảm, vùng đó bị **ghi đè hoàn toàn** bằng solid fill. Không phải blur, không phải mosaic — pixel gốc bị hủy, không có cách khôi phục. Ảnh export ra ngoài không còn chứa dữ liệu cũ của vùng redact.

### Open source, dễ kiểm tra

Code Python + PyQt6, khoảng 1500 dòng, cấu trúc rõ ràng. Bạn có thể đọc toàn bộ source trong 30 phút. Không có thành phần ẩn, không có dependency lạ.

Chạy từ source hoặc build thành `.exe` — tùy bạn.

### Nhanh và nhẹ

- Mở app là vào capture ngay, không splash screen, không loading.
- Bấm **New** để chụp lại — editor mở gần như tức thì.
- Chuyển đổi ảnh dùng direct memory transfer thay vì encode/decode PNG, nhanh hơn đáng kể.
- Dependencies tối thiểu: PyQt6, Pillow, mss — không có gì thừa.

---

## Tính năng

- Chụp màn hình chọn vùng, hỗ trợ multi-monitor
- Chỉnh lại vùng chọn bằng cách kéo, resize rồi bấm **Xác nhận**
- Khung hướng dẫn tỉ lệ `16:9`, `1:1`, `4:5` và cảnh báo đỏ khi ảnh rộng dưới 300 px
- Hẹn giờ chụp: không trễ, 3 giây, 5 giây hoặc 10 giây
- **Rect** — khung chữ nhật, kéo để đổi vị trí sau khi vẽ
- **Arrow** — mũi tên
- **Label** — nhãn đánh số
- **Text** — ghi chú dạng note card, kéo thả và resize được
- **Redact** — che thông tin, solid fill không khôi phục được
- **Icon** — overlay kéo/resize trên toàn ảnh và background, có nút bật/tắt và lưu thiết lập
- **Undo** / **Clear**
- **Copy** (`Ctrl+C`) / **Save** (`Ctrl+S`) / **New** (`Ctrl+N`)
- Toast "Copied" xác nhận copy thành công
- Lưu lại màu nền và style cho lần mở sau
- Watermark chữ tùy chỉnh, lưu cục bộ và chỉ nằm trên phần background

---

## Công nghệ

`Python` · `PyQt6` · `Pillow` · `mss` · `PyInstaller`
