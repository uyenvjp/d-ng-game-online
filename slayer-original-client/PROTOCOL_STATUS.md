# Slayer Legend 700.0.4 — Giao thức server (bản kiểm kê có chứng cứ)

**Trạng thái:** PARTIAL / RESEARCH ONLY — chưa có server tương thích với client Unity gốc, chưa có file .proto đầy đủ và chưa có APK game đã sửa.

**Nguồn:** Logcat client Unity gốc ngày 05/11/2026; CSV PCAPdroid gồm 93 kết nối (05/11/2026 06:09:20–06:09:58); phân tích tĩnh Bước 26, 29, 35 đối chiếu libil2cpp.so và metadata người dùng cung cấp.

## 1. Transport & hosts

| Nhóm | Quan sát được | Hạn chế |
| --- | --- | --- |
| Integration / lookup | `integration-grpc-http2-api.gear2slayer.com:443` | Tên gợi ý gRPC/HTTP2; log xác nhận `LookupLoginConnect`; chưa bắt được tên service/method gRPC hoặc payload |
| Front AU | `https://product-au-slayer-front.gear2slayer.com:443` | Unity log `server address`; chưa xác định HTTP paths và schema |
| Realtime | `realtime.gear2slayer.com:52011` | CSV kết nối; Unity log `BestHTTP.SignalRCore.HubConnection` + `OnConnected`; chưa có hub methods, message framing |
| Firebase | `securetoken.googleapis.com:443` | Dịch vụ phát JWT khi login Google; không thay thế được bằng username/password đơn thuần |
| Telemetry | `grpc-prod-slayer-client-event-producer.data-aws.gear2slayer.com:443` | Analytics; không phải endpoint đăng nhập |
| IFix | `s3.ap-northeast-2.amazonaws.com/gear2slayer.cdn/root/LIVE/iFix/700.0.4/` | Thấy danh sách patch 4, 5, 6 ở log và `IFix Patch result : True`; không phải API nhân vật |

**IPs là quan sát có thời điểm, không hardcode.** HTTPS/gRPC/SignalR chưa được giải mã. Không gọi endpoint production hoặc trích token tài khoản.

## 2. Luồng login trong client gốc (quan sát + tĩnh)

```text
SignManager.Button_TapToStart()
   -> Firebase login / SetToken (Google hoặc Guest branch)
   -> Network.NetworkHandler.LookupLoginConnect
   -> Integration.LookupLoginResponse.jwt_
   -> GrowSlayer.SignInRequest.integrationJwtToken_
   -> Network.ValidateAuthAsyncV3
   -> GrowSlayer.LoginResponse
   -> SignManager.LoginResult_Func
   -> Network.NetworkHandler.SetupJWT
   -> UserInfoLoad.Load
   -> realtime OnConnected
```

**Các hàm cạnh nhau được xác minh từ static analysis; không phải mọi mũi tên đều là một packet trace.** Đăng nhập Google được thấy trong runtime; đường Guest có mặt trong mã, chưa kiểm thử runtime.

## 3. Cấu trúc dữ liệu từ IL2CPP

Các số hex sau là **offset trong đối tượng IL2CPP ở bộ nhớ**, KHÔNG PHẢI protobuf wire tags, không thể dùng để sinh trực tiếp `.proto`.

| Message | Field | IL2CPP offset |
| --- | --- | --- |
| Integration.LookupLoginResponse | jwt_ | 0x60 |
| Integration.LookupLoginResponse | isNewUser_ | 0x69 |
| GrowSlayer.SignInRequest | integrationJwtToken_ | 0x18 |
| GrowSlayer.SignInRequest | loginClientInfo_ | 0x28 |
| GrowSlayer.LoginResponse | jWT_ | 0x30 |
| GrowSlayer.LoginResponse | userInfo_ | 0x38 |
| GrowSlayer.LoginResponse | authKey_ | 0x48 |
| GrowSlayer.LoginResponse | sequenceNumber_ | 0x58 |
| GrowSlayer.UserInfo | equipmentState_ | 0xA0 |
| GrowSlayer.UserInfo | equipments_ | 0xA8 |
| GrowSlayer.EquipmentState | usingWeaponIndex_ | 0x18 |
| GrowSlayer.EquipmentState | usingAccessoryIndex_ | 0x1C |
| GrowSlayer.EquipmentState | usingSlayerClassIndex_ | 0x20 |
| GrowSlayer.EquipmentState | usingCharacterIndex_ | 0x24 |

## 4. API numeric IDs trong IL2CPP (không phải HTTP path)

- **115** — `APIManager.AcquireItems` -> `GrowSlayer.AcquireItemsRequest`, kiểm chứng tại call `APIManager.AddRequest` VA `0x50C23C0`.
  - Request: `dungeonType_` (0x18), `mainIndex_` (0x1C), `subIndex_` (0x20), `acquiredEquipments_` (0x28), `acquiredCurrencies_` (0x30), `sequenceNumber_` (0x38), `acquiredBigCurrencies_` (0x40).
  - Response: `resultCode_` (0x18), `dungeonType_` (0x1C), `equipments_` (0x20), `currencies_` (0x28), `sequenceNumber_` (0x30), `bigCurrencies_` (0x38).
- **86** — `APIManager.ChangeSkinData` (quan sát tại callsite VA `0x50C9608`), request có `selectedCharacterNumber_` và `isEvent_`.

Những số API này là mã dispatch nội bộ; **chưa xác minh cách mã hóa chúng trên network wire**.

## 5. Ranh giới công việc chưa giải quyết

1. Khôi phục chính xác protobuf field numbers/wire types và service RPC names, từ bảng metadata hoặc capture hợp lệ.
2. Xác định trình tự handshake và xác thực với endpoint lookup/front mà không dùng lại token sản xuất.
3. Khôi phục data tối thiểu của UserInfo/SignIn response và validate trên build thử nghiệm được cấp phép.
4. Xác định realtime SignalR transport và hợp đồng hub method.
5. Tạo backend riêng **chỉ sau khi** wire contract được xác minh. Không giả vờ Node auth demo là tương thích Unity client.
6. Build và ký lại client gốc, kiểm thử các phụ thuộc LIAPP/IFix; chưa thực hiện thành công.

**Không có:** `.proto` chuẩn, binary protocol decoder đầy đủ, emulator server, backend server tương thích, APK đã bỏ LIAPP. Bản này chỉ là **báo cáo bằng chứng**.
