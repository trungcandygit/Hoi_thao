# BÁO CÁO THIẾT KẾ — HỆ THỐNG BÁN TRÁI CÂY
## Môn: Kiến Trúc Và Thiết Kế Phần Mềm

---

## CÂU 1 — MỞ RỘNG THIẾT KẾ

### 1.1 Sơ Đồ ERD — Module Quản Lý Khuyến Mãi

```
┌─────────────────────┐         ┌─────────────────────────┐
│      KHACH_HANG      │         │         DON_HANG         │
├─────────────────────┤         ├─────────────────────────┤
│ PK  MaKhachHang INT │◄────────┤ PK  MaDonHang    INT    │
│     HoTen      NVARCHAR│      │ FK  MaKhachHang  INT    │
│     SoDienThoai NVARCHAR│     │ FK  MaVoucher    NVARCHAR│
│     DiaChi     NVARCHAR│      │     NgayDatHang  DATETIME│
└─────────────────────┘         │     TrangThai    NVARCHAR│
                                │     TongTienGoc  DECIMAL │
                                │     SoTienGiam   DECIMAL │
                                │     TongTienThanhToan DECIMAL│
                                └──────────┬──────────────┘
                                           │ 1
                                           │
                                           │ N
                                ┌──────────▼──────────────┐
                                │    CHI_TIET_DON_HANG     │
                                ├─────────────────────────┤
                                │ PK  MaChiTiet    INT    │
                                │ FK  MaDonHang    INT    │
                                │ FK  MaSanPham    INT    │
                                │     SoLuong      INT    │
                                │     DonGia       DECIMAL│
                                │     ThanhTien    DECIMAL│
                                └──────────┬──────────────┘
                                           │ N
                                           │
                                           │ 1
                                ┌──────────▼──────────────┐
                                │         SAN_PHAM         │
                                ├─────────────────────────┤
                                │ PK  MaSanPham    INT    │
                                │     TenSanPham   NVARCHAR│
                                │     GiaBan       DECIMAL│
                                │     SoLuongTonKho INT   │
                                │     DonViTinh    NVARCHAR│
                                └─────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     KHUYEN_MAI                           │
├─────────────────────────────────────────────────────────┤
│ PK  MaKhuyenMai     INT                                 │
│     MaVoucher       NVARCHAR  (UNIQUE — dùng làm FK)    │
│     TenKhuyenMai    NVARCHAR                            │
│     LoaiKhuyenMai   NVARCHAR  -- TienMat/PhanTram/MuaTang│
│     GiaTriGiam      DECIMAL   -- số tiền hoặc %         │
│     DonHangToiThieu DECIMAL                             │
│     NgayBatDau      DATETIME                            │
│     NgayKetThuc     DATETIME                            │
└─────────────────────────────────────────────────────────┘

  DON_HANG.MaVoucher ──(FK, nullable)──► KHUYEN_MAI.MaVoucher
```

**Mối Quan Hệ:**
| Bảng A | Quan Hệ | Bảng B | Ghi Chú |
|---|---|---|---|
| KHACH_HANG | 1 — N | DON_HANG | Một khách hàng có nhiều đơn hàng |
| DON_HANG | 1 — N | CHI_TIET_DON_HANG | Một đơn hàng có nhiều dòng sản phẩm |
| SAN_PHAM | 1 — N | CHI_TIET_DON_HANG | Một sản phẩm xuất hiện trong nhiều đơn |
| KHUYEN_MAI | 1 — N | DON_HANG | Một mã voucher dùng cho nhiều đơn (nullable) |

---

### 1.2 Interface Dịch Vụ Tính Giá

```
«interface»
ITinhGiaService
──────────────────────────────────────────
+ TinhSoTienGiam(tongTienGoc: decimal,
                 khuyenMai: KhuyenMai) : decimal
+ TinhTongTienSauGiam(tongTienGoc: decimal,
                      khuyenMai: KhuyenMai?) : decimal
          ▲
          │ implements
          │
┌─────────────────────────────┐
│      TinhGiaService         │
├─────────────────────────────┤
│ - GiamToiDaTheoPhantram     │
│   = 100_000 VNĐ             │
├─────────────────────────────┤
│ + TinhSoTienGiam(...)       │  ← switch theo LoaiKhuyenMai:
│                             │    • GiamTheoTienMat  → giảm cố định
│                             │    • GiamTheoPhantram → giảm % (có trần)
│                             │    • MuaNTangM        → tặng kg tương đương
│ + TinhTongTienSauGiam(...)  │
└─────────────────────────────┘
```

**Lý Do Thiết Kế Interface:**
- Tuân thủ **Open/Closed Principle** — thêm loại chiết khấu mới chỉ cần thêm `case` trong switch, không sửa các class khác.
- Dễ **kiểm thử** (unit test) bằng cách mock `ITinhGiaService`.
- Cho phép **thay thế chiến lược tính giá** trong tương lai (Strategy Pattern nếu cần).

---

## CÂU 2 — TRIỂN KHAI CHỨC NĂNG XÁC NHẬN ĐẶT HÀNG

### 2.1 Design Pattern Sử Dụng — Builder Pattern

```
«Builder Pattern»

DonHangBuilder
──────────────────────────────────────────
- _donHang : DonHang  (đối tượng đang xây dựng)
──────────────────────────────────────────
+ VoiKhachHang(maKH, hoTen, diaChi) : DonHangBuilder
+ ThemSanPham(maSanPham, soLuong)   : DonHangBuilder
+ ApDungVoucher(maVoucher)          : DonHangBuilder
+ Build()                           : DonHang
```

**Cách Sử Dụng (Method Chaining):**
```csharp
var donHang = new DonHangBuilder()
    .VoiKhachHang(101, "Nguyễn Văn An", "123 Lê Lợi, TP.HCM")
    .ThemSanPham(maSanPham: 1, soLuong: 2)
    .ThemSanPham(maSanPham: 3, soLuong: 3)
    .ApDungVoucher("GIAM50K")
    .Build();
```

**Lý Do Chọn Builder:**
- Đối tượng `DonHang` có nhiều thuộc tính tùy chọn (voucher, nhiều sản phẩm).
- Tránh "telescoping constructor" — quá nhiều tham số trong constructor.
- Code tạo đơn hàng đọc như ngôn ngữ tự nhiên, dễ bảo trì.

---

### 2.2 Kiến Trúc Phân Tầng

```
┌──────────────────────────────────────────────────────┐
│                   TẦNG TRÌNH BÀY                      │
│  Program.cs — Console, nhận input, hiển thị kết quả  │
└─────────────────────┬────────────────────────────────┘
                      │ gọi
┌─────────────────────▼────────────────────────────────┐
│                   TẦNG NGHIỆP VỤ                      │
│  DonHangService — xử lý logic đặt hàng               │
│  TinhGiaService — tính giá sau khuyến mãi            │
└──────┬──────────────────────┬────────────────────────┘
       │ dùng (DI)            │ dùng (DI)
┌──────▼──────┐   ┌───────────▼───────┐   ┌───────────┐
│TẦNG DỮ LIỆU│   │  TẦNG DỮ LIỆU    │   │TẦNG DỮ LI.│
│SanPhamRepo. │   │  DonHangRepo.    │   │KhuyenMai  │
│             │   │                  │   │Repository │
└─────────────┘   └──────────────────┘   └───────────┘
```

---

### 2.3 Luồng Xử Lý Xác Nhận Đặt Hàng

```
Người Dùng → Builder → DonHang (chưa có giá)
                              │
                              ▼
                    DonHangService.XacNhanDatHang()
                              │
              ┌───────────────┼───────────────────┐
              │               │                   │
              ▼               ▼                   ▼
        Validate          Đồng bộ giá        Kiểm tra
        đầu vào          từ Repository       Tồn Kho
              │               │                   │
              └───────────────┼───────────────────┘
                              │ (nếu tất cả OK)
                              ▼
                      Áp dụng Khuyến Mãi
                    (ITinhGiaService)
                              │
                              ▼
                    Lưu Đơn Hàng → Repository
                              │
                              ▼
                    Cập Nhật Tồn Kho
                              │
                              ▼
                    Trả Về DonHang Đã Xác Nhận
```

---

## CÂU 3 — TỐI ƯU HÓA KIẾN TRÚC — XỬ LÝ NGOẠI LỆ

### 3.1 Phân Cấp Ngoại Lệ

```
Exception (hệ thống)
    └── NgoaiLeUngDung          ← Lỗi gốc của ứng dụng
            ├── DonHangRongException
            ├── SanPhamKhongTonTaiException
            ├── TonKhoKhongDuException
            └── VoucherKhongHopLeException
```

### 3.2 Chiến Lược Xử Lý Ngoại Lệ Trong Service

```csharp
public DonHang XacNhanDatHang(DonHang donHang)
{
    try
    {
        // ... logic nghiệp vụ ...
    }
    catch (NgoaiLeUngDung ex)
    {
        // Lỗi nghiệp vụ đã biết → log + ném lại để tầng trên xử lý
        // KHÔNG wrap thêm để giữ nguyên thông tin lỗi
        throw;
    }
    catch (Exception ex)
    {
        // Lỗi hệ thống không mong đợi → bọc lại để che thông tin nội bộ
        // (tránh lộ stack trace ra ngoài)
        throw new NgoaiLeUngDung("Lỗi hệ thống khi xử lý đặt hàng.", ex);
    }
}
```

### 3.3 Nguyên Tắc Áp Dụng

| Nguyên Tắc | Áp Dụng Trong Dự Án |
|---|---|
| **Fail Fast** | Validate đơn hàng rỗng ngay đầu hàm, không chờ đến bước lưu |
| **Specific Exception** | Mỗi lỗi nghiệp vụ có class riêng với thông tin chi tiết |
| **No Silent Catch** | Không bao giờ `catch` rồi bỏ qua — luôn log hoặc throw |
| **Wrap External Errors** | Lỗi từ bên ngoài được bọc bởi `NgoaiLeUngDung` |
| **User-Friendly Message** | Thông điệp lỗi bằng tiếng Việt, rõ ràng cho người dùng cuối |

---

## CẤU TRÚC DỰ ÁN

```
BanTraiCay/
├── Models/
│   ├── SanPham.cs           — Sản phẩm trái cây
│   ├── KhachHang.cs         — Thông tin khách hàng
│   ├── KhuyenMai.cs         — Mã khuyến mãi / voucher
│   ├── ChiTietDonHang.cs    — Một dòng sản phẩm trong đơn
│   └── DonHang.cs           — Đơn hàng tổng hợp
├── Interfaces/
│   ├── ISanPhamRepository.cs
│   ├── IDonHangRepository.cs
│   ├── IKhuyenMaiRepository.cs
│   ├── ITinhGiaService.cs   — Interface tính giá (mở rộng được)
│   └── IDonHangService.cs
├── Repositories/
│   ├── SanPhamRepository.cs
│   ├── DonHangRepository.cs
│   └── KhuyenMaiRepository.cs
├── Services/
│   ├── TinhGiaService.cs    — Xử lý các loại chiết khấu
│   └── DonHangService.cs    — Nghiệp vụ xác nhận đặt hàng
├── Builders/
│   └── DonHangBuilder.cs    — Builder Pattern
├── Exceptions/
│   └── NgoaiLeUngDung.cs    — Phân cấp ngoại lệ tùy chỉnh
└── Program.cs               — Điểm khởi chạy console
```

---

## QUYẾT ĐỊNH KIẾN TRÚC

### Tại Sao Dùng Repository Pattern?
Repository Pattern tạo lớp trừu tượng giữa tầng nghiệp vụ và tầng dữ liệu. Khi cần chuyển từ dữ liệu giả lập (in-memory) sang SQL Server thực, chỉ cần tạo class repository mới implement cùng interface — không thay đổi bất kỳ dòng code nào trong Service.

### Tại Sao Dùng Dependency Injection?
`DonHangService` nhận các dependency qua constructor thay vì tự tạo. Điều này giúp:
- Dễ viết unit test (mock các dependency)
- Tuân thủ Dependency Inversion Principle
- Dễ thay thế implementation (ví dụ: đổi sang Redis cache cho repository)

### Tại Sao Dùng Builder Pattern Thay Vì Constructor?
`DonHang` có nhiều thuộc tính tùy chọn. Nếu dùng constructor, sẽ cần nhiều overload hoặc một constructor với quá nhiều tham số (khó đọc, dễ nhầm thứ tự). Builder cho phép tạo đơn hàng từng bước, dễ đọc và mở rộng.
