# Logic Phát Hiện Hít Đất

## 1. Giải nghĩa biến chính

- `leftShoulderY`, `rightShoulderY`: tọa độ dọc của vai trái và vai phải.
- `midShoulderY`: tọa độ dọc ở giữa 2 vai: `(leftShoulderY + rightShoulderY) / 2`
- `noseY`: tọa độ dọc của mũi.
- `headHeight`: khoảng cách dọc từ mũi tới trục giữa 2 vai: `midShoulderY - noseY`
- `smoothedSignal`: `headHeight` sau khi làm mượt bằng EMA.
- `upPositionThreshold`: mốc để coi là đang ở trên cao: `0.08`
- `downPositionThreshold`: mốc để coi là đang ở dưới thấp: `0.01`
- `positionHysteresis`: khoảng đệm chống nhảy trạng thái loạn quanh mép ngưỡng: `0.005`
- `motionTrendThreshold`: mốc để biết đầu đang lên hay đang xuống: `0.005`
- `shoulderConfidence`: độ tin cậy nhìn thấy rõ 2 vai.
- `readyHoldFrames`: số frame phải giữ tư thế sẵn sàng liên tục trước khi bắt đầu đếm: `8`

## 2. Diagram dễ hiểu

```text
          mũi
           *
           |  <- headHeight
-----------+-----------  <- trục giữa 2 vai (midShoulderY)
     vai trái     vai phải
```

```text
Sẵn sàng
   |
   v
up -> going_down -> down -> going_up -> up (+1 rep)
```

## 3. App đang đo cái gì

- Bắt buộc phải thấy mũi rõ: `noseConfidence > 0.4`
- Khi thấy mũi rõ: `headHeight = midShoulderY - noseY`
- Nếu không thấy mũi rõ: không tính `headHeight`
- Tín hiệu được làm mượt bằng EMA: `alpha = 0.55`
- App đọc `smoothedSignal` để quyết định đang ở trên, ở dưới, đang lên hay đang xuống

## 4. Khi nào được coi là sẵn sàng

- Thấy rõ mặt: `noseConfidence >= 0.45`
- Thấy rõ 2 vai: `shoulderConfidence >= 0.45`
- Thấy rõ 2 hông: `hipConfidence >= 0.45`
- Thấy rõ 2 khuỷu tay: `elbowJointConfidence >= 0.45`
- Mặt nhìn gần chính diện camera: `noseOffsetFromShoulderCenterRatio <= 0.35`
- Giữ đủ `8 frame` liên tiếp thì vào trạng thái sẵn sàng

## 5. Các số liệu đang dùng để đếm rep

- Tốc độ detect: khoảng `25 fps`
- Mốc trên để coi là ở cao: `0.08`
- Mốc dưới để coi là ở thấp: `0.01`
- Khoảng đệm chống nhảy loạn: `0.005`
- Mốc nhận biết đầu đang lên hoặc đang xuống: `0.005`
- Đổi pha chỉ khi giữ đủ điều kiện trong: `2 frame`
- Độ tin cậy tối thiểu để tiếp tục tracking: `shoulderConfidence >= 0.30`
- Thời gian một rep hợp lệ: `350 ms -> 12,000 ms`

## 6. Khi nào cộng 1 rep

- Sau khi sẵn sàng, app theo vòng: `up -> going_down -> down -> going_up -> up`
- Chỉ cộng `1 rep` khi vừa đi từ `going_up` quay lại `up`
- Nếu rep quá nhanh: `< 350 ms` thì không cộng
- Nếu rep quá lâu: `> 12,000 ms` thì không cộng

## 7. Cách đọc debug nhanh

- `Hướng hiện tại`: đầu đang `đi lên / đi xuống / đứng yên`
- `Mức cao/thấp hiện tại`: đầu đang ở `trên cao / ở giữa / dưới thấp`
- `Độ cao đầu hiện tại`: chính là `smoothedSignal`
- `Mốc trên để coi là ở cao`: ngưỡng để vào vùng trên
- `Mốc dưới để coi là ở thấp`: ngưỡng để vào vùng dưới
- `Trạng thái sẵn sàng`: đã qua bước kiểm tra tư thế ban đầu hay chưa

## 8. Tóm gọn

- App không đếm ngay: phải vào `tư thế sẵn sàng` trước.
- App đếm theo `độ cao đầu so với trục giữa 2 vai`.
- Đủ một vòng `lên xuống lên` thì cộng `1 rep`.
