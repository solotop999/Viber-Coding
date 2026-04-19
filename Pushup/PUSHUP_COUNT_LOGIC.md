# Cách Đếm Hiện Tại

## App đang lấy gì để đếm

App lấy `độ cao đầu` làm chính.

- nếu thấy mũi rõ:
  - `độ cao đầu = giữa 2 vai - mũi`
- nếu không thấy mũi:
  - `độ cao đầu = giữa hông - giữa vai`

Hiểu đơn giản:

- ở trên cao: số này lớn hơn
- hạ xuống: số này nhỏ đi

## Góc tay dùng để làm gì

Góc tay chỉ là kiểm tra phụ.

- xuống đáy: góc tay < `140`
- lên đỉnh: góc tay > `145`

Nếu tay không thấy rõ đủ, app bỏ qua bước này.

## Lấy mốc ban đầu

App lấy `25` khung hình khi bạn giữ tư thế chống cao.

Sau đó tính:

- `mốc gốc = trung bình độ cao đầu`

## Các ngưỡng đang dùng

- `ngưỡng lên = mốc gốc x 0.75`
- `ngưỡng xuống = mốc gốc x 0.52`

## Khi nào được cộng 1 cái

Phải đi đủ vòng này:

1. đang ở trên
2. hạ xuống qua `ngưỡng lên`
3. xuống thấp hơn `ngưỡng xuống`
4. đi lên lại
5. vượt lại `ngưỡng lên`
6. nếu hợp lệ thì cộng `1`

## Điều kiện chống đếm sai

- nhanh hơn `500ms` thì không tính
- lâu hơn `12s` thì không tính
- độ tin cậy tối thiểu khoảng `0.45`

## Các số quan trọng nhất trên màn debug

- `Head raw`: độ cao đầu thật
- `Head mượt`: độ cao đầu app đang dùng để quyết định
- `Nền`: mốc gốc
- `Ngưỡng lên`
- `Ngưỡng xuống`
- `Pha`
- `Tạm block`

## Phần số liệu cần nhìn

### 1. Biên độ xuống

- `biên độ xuống = Nền - Head mượt thấp nhất`

Nếu xuống mà vẫn không vào đáy:

- thường là `Head mượt thấp nhất` vẫn chưa nhỏ hơn `Ngưỡng xuống`

### 2. Biên độ lên

- nhìn xem lúc lên cao nhất, `Head mượt` có vượt lại `Ngưỡng lên` chưa

Nếu chưa vượt:

- app không cộng số

## Cách đọc nhanh

### Không lấy được mốc

Nhìn:

- `Hiệu chỉnh`
- `Frame vào calib`

Nếu:

- `Hiệu chỉnh` không tăng
- `Frame vào calib = no`

thì app chưa lấy được mốc.

### Không xuống đủ sâu

Nhìn:

- `Head mượt thấp nhất`
- `Ngưỡng xuống`

Nếu:

- `Head mượt thấp nhất > Ngưỡng xuống`

thì ngưỡng xuống đang quá gắt hoặc biên độ xuống chưa đủ.

### Lên rồi mà vẫn không cộng

Nhìn:

- `Head mượt cao nhất khi lên`
- `Ngưỡng lên`
- `Tạm block`
- `Thời gian rep`

Nếu:

- `Head mượt` chưa vượt `Ngưỡng lên`

thì chưa lên đủ cao.

Nếu đã vượt mà vẫn không cộng:

- thường bị chặn bởi góc tay hoặc thời gian.

## Tóm tắt rất ngắn

App đang đếm theo kiểu:

- đầu đi xuống đủ sâu
- rồi đi lên đủ cao

Muốn biết cần chỉnh gì thì nhìn 3 số:

- `Nền`
- `Ngưỡng lên`
- `Ngưỡng xuống`

và so với:

- `Head mượt` lúc trên cao nhất
- `Head mượt` lúc dưới thấp nhất
