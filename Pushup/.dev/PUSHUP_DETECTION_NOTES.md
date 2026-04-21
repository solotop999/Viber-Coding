# Ghi Chú Phát Triển Pushup Detection

## Mục tiêu của đợt chỉnh này

- Làm logic đếm rep dễ hiểu hơn để còn tinh chỉnh tiếp.
- Làm màn `video debug` đủ mạnh để soi lỗi tracking và lỗi đếm rep.
- Giảm cảm giác “đếm sai, nhảy loạn, khó hiểu” khi test thực tế.

## Những gì đã đổi trong logic detect

- Bỏ xác nhận rep bằng góc khuỷu tay trong logic chính.
- Chuyển sang đếm rep chủ yếu bằng `headHeight`:
  - `headHeight = midShoulderY - noseY`
- Bắt buộc phải thấy mũi rõ, không còn fallback kiểu `midHipY - midShoulderY`.
- Thêm bước `tư thế sẵn sàng` trước khi bắt đầu đếm:
  - thấy mặt
  - thấy 2 vai
  - thấy 2 hông
  - thấy 2 khuỷu tay
  - mặt nằm gần giữa 2 vai
  - giữ đủ `8 frame`
- Sau khi sẵn sàng, detector đi theo vòng:
  - `up -> going_down -> down -> going_up -> up`
- Chỉ cộng rep khi vừa quay lại `up`.
- Thêm `hysteresis` và xác nhận `2 frame` để giảm nhảy trạng thái loạn.
- Thêm `motionTrend` để debug biết đầu đang lên, đang xuống hay đứng yên.
- Giữ `repCount` khi video debug phát lại, không reset về `0` nữa.
- Khi thiếu landmark tạm thời, frame debug giữ rep cũ thay vì nháy về `0`.

## Những gì đã đổi trong video debug

- Video debug mặc định tự chạy và mặc định ở `0.5x`.
- Có chọn tốc độ: `0.25x`, `0.5x`, `0.75x`, `1x`.
- Có log debug để xuất file `.json`, nhưng mặc định không ghi.
- Chỉ khi bấm `Bật log` thì mới bắt đầu ghi.
- Khi video lặp lại:
  - detector reset pha tracking
  - nhưng vẫn giữ tổng số rep
- Có `ReadyCheckOverlay` hiện dấu check lớn giữa màn khi vào trạng thái sẵn sàng.
- Có cờ `SHOW_DEBUG_UI` để bật/tắt toàn bộ:
  - panel debug
  - cụm tốc độ
  - cụm log

## Những gì đã đổi trong phần debug hiển thị

- Dời debug lên góc trên trái.
- Bỏ nền đen che video ở panel debug.
- Chữ debug to hơn để dễ nhìn.
- Đổi cách đọc debug cho dễ hiểu hơn:
  - `Hướng hiện tại`
  - `Mức cao/thấp hiện tại`
  - `Độ cao đầu hiện tại`
  - `Mốc trên để coi là ở cao`
  - `Mốc dưới để coi là ở thấp`
  - `Trạng thái sẵn sàng`
- Bỏ checklist dài kiểu `M / V / H / K / Hướng`.

## Những gì đã đổi trong câu nhắc người dùng

- Dòng chữ to phía dưới không còn dùng message kiểu `Hạ xuống / Đẩy lên` từ detector nữa.
- UI tự quyết định `next action`:
  - `Hạ người xuống chậm`
  - `Đẩy mạnh người lên`
- Nếu tư thế chưa chuẩn hoặc tracking chưa rõ thì ưu tiên nhắc người dùng:
  - đưa mặt rõ hơn
  - giữ 2 vai rõ hơn
  - xoay mặt đối diện camera
  - giữ yên để xác nhận tư thế sẵn sàng

## Các số đang dùng hiện tại

- `DETECTION_INTERVAL_MS = 1000 / 25`
- `emaAlpha = 0.55`
- `upPositionThreshold = 0.08`
- `downPositionThreshold = 0.01`
- `positionHysteresis = 0.005`
- `motionTrendThreshold = 0.005`
- `phaseConfirmFrames = 2`
- `confidenceThreshold = 0.30`
- `readyVisibilityThreshold = 0.45`
- `readyFaceCenterToleranceRatio = 0.35`
- `readyHoldFrames = 8`
- `minRepDurationMs = 350`
- `maxRepDurationMs = 12_000`

## File chính nên đọc nếu muốn chỉnh tiếp

- [pushupDetector.ts](D:/Solana/Viber-Coding/Pushup/Pushup/src/features/pushup-detection/lib/pushupDetector.ts)
- [landmarkMath.ts](D:/Solana/Viber-Coding/Pushup/Pushup/src/features/pushup-detection/lib/landmarkMath.ts)
- [constants.ts](D:/Solana/Viber-Coding/Pushup/Pushup/src/features/pushup-detection/model/constants.ts)
- [detectorTypes.ts](D:/Solana/Viber-Coding/Pushup/Pushup/src/features/pushup-detection/model/detectorTypes.ts)
- [VideoDebugScreen.tsx](D:/Solana/Viber-Coding/Pushup/Pushup/src/features/pushup-detection/components/VideoDebugScreen.tsx)
- [DebugStrip.tsx](D:/Solana/Viber-Coding/Pushup/Pushup/src/features/pushup-detection/components/DebugStrip.tsx)
- [SessionGuide.tsx](D:/Solana/Viber-Coding/Pushup/Pushup/src/features/pushup-detection/components/SessionGuide.tsx)

## Việc nên làm tiếp nếu muốn chuẩn hơn

- Test thêm với nhiều góc camera khác nhau để xem ngưỡng `0.08 / 0.01` đã hợp lý chưa.
- Quyết định có nên giữ `25 fps` hay tăng lại nếu thấy tracking quá trễ.
- Đổi câu nhắc `next action` sang kiểu bớt lặp và thú vị hơn.
- Ghi thêm vài log tổng hợp ngắn gọn để đọc nhanh hơn thay vì chỉ xem log theo frame.
- Tách rõ logic “đếm rep” và logic “nhắc người dùng” để sau này chỉnh độc lập dễ hơn.
