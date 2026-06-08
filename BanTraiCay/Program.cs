using BanTraiCay.Builders;
using BanTraiCay.Exceptions;
using BanTraiCay.Interfaces;
using BanTraiCay.Repositories;
using BanTraiCay.Services;

// ─── Đăng ký phụ thuộc thủ công (mô phỏng Dependency Injection) ───────────
ISanPhamRepository   sanPhamRepo   = new SanPhamRepository();
IDonHangRepository   donHangRepo   = new DonHangRepository();
IKhuyenMaiRepository khuyenMaiRepo = new KhuyenMaiRepository();
ITinhGiaService      tinhGiaSvc    = new TinhGiaService();

var donHangSvc = new DonHangService(sanPhamRepo, donHangRepo, khuyenMaiRepo, tinhGiaSvc);

Console.OutputEncoding = System.Text.Encoding.UTF8;
Console.WriteLine("╔═══════════════════════════════════════════════╗");
Console.WriteLine("║      HỆ THỐNG BÁN TRÁI CÂY — ĐẶT HÀNG       ║");
Console.WriteLine("╚═══════════════════════════════════════════════╝\n");

// ─── Hiển thị danh sách sản phẩm ─────────────────────────────────────────
Console.WriteLine("  DANH SÁCH SẢN PHẨM:");
foreach (var sp in sanPhamRepo.LayTatCa())
    Console.WriteLine($"  {sp}");

Console.WriteLine();

// ═══════════════════════════════════════════════════════════════════════════
// KỊCH BẢN 1 — Đặt hàng hợp lệ có dùng voucher giảm tiền mặt
// ═══════════════════════════════════════════════════════════════════════════
Console.WriteLine("══════════════════════════════════════════════════");
Console.WriteLine("  KỊCH BẢN 1: Đặt hàng hợp lệ + voucher GIAM50K");
Console.WriteLine("══════════════════════════════════════════════════");

var donHang1 = new DonHangBuilder()
    .VoiKhachHang(101, "Nguyễn Văn An", "123 Lê Lợi, TP.HCM")
    .ThemSanPham(maSanPham: 1, soLuong: 2)   // 2 kg Xoài
    .ThemSanPham(maSanPham: 3, soLuong: 3)   // 3 kg Bưởi
    .ApDungVoucher("GIAM50K")
    .Build();

try
{
    var ketQua1 = donHangSvc.XacNhanDatHang(donHang1);
    ketQua1.HienThiDonHang();
}
catch (NgoaiLeUngDung) { /* Đã xử lý trong service */ }

Console.WriteLine();

// ═══════════════════════════════════════════════════════════════════════════
// KỊCH BẢN 2 — Đặt hàng có dùng voucher giảm theo %
// ═══════════════════════════════════════════════════════════════════════════
Console.WriteLine("══════════════════════════════════════════════════");
Console.WriteLine("  KỊCH BẢN 2: Đặt hàng + voucher GIAM10PCT (10%)");
Console.WriteLine("══════════════════════════════════════════════════");

var donHang2 = new DonHangBuilder()
    .VoiKhachHang(102, "Trần Thị Bình", "456 Nguyễn Huệ, Hà Nội")
    .ThemSanPham(maSanPham: 2, soLuong: 1)   // 1 kg Sầu Riêng
    .ThemSanPham(maSanPham: 5, soLuong: 2)   // 2 kg Nhãn
    .ApDungVoucher("GIAM10PCT")
    .Build();

try
{
    var ketQua2 = donHangSvc.XacNhanDatHang(donHang2);
    ketQua2.HienThiDonHang();
}
catch (NgoaiLeUngDung) { }

Console.WriteLine();

// ═══════════════════════════════════════════════════════════════════════════
// KỊCH BẢN 3 — Lỗi: Không đủ tồn kho
// ═══════════════════════════════════════════════════════════════════════════
Console.WriteLine("══════════════════════════════════════════════════");
Console.WriteLine("  KỊCH BẢN 3: Lỗi — Số lượng vượt tồn kho");
Console.WriteLine("══════════════════════════════════════════════════");

var donHang3 = new DonHangBuilder()
    .VoiKhachHang(103, "Lê Văn Cường", "789 Trần Hưng Đạo, Đà Nẵng")
    .ThemSanPham(maSanPham: 2, soLuong: 999) // Sầu Riêng chỉ còn 30 kg
    .Build();

try
{
    donHangSvc.XacNhanDatHang(donHang3);
}
catch (TonKhoKhongDuException ex)
{
    Console.WriteLine($"  → Bắt được lỗi tồn kho: {ex.Message}");
}
catch (NgoaiLeUngDung) { }

Console.WriteLine();

// ═══════════════════════════════════════════════════════════════════════════
// KỊCH BẢN 4 — Lỗi: Voucher đã hết hạn
// ═══════════════════════════════════════════════════════════════════════════
Console.WriteLine("══════════════════════════════════════════════════");
Console.WriteLine("  KỊCH BẢN 4: Lỗi — Voucher hết hạn");
Console.WriteLine("══════════════════════════════════════════════════");

var donHang4 = new DonHangBuilder()
    .VoiKhachHang(104, "Phạm Thị Dung", "321 Hai Bà Trưng, Cần Thơ")
    .ThemSanPham(maSanPham: 4, soLuong: 5)
    .ApDungVoucher("HET_HAN")
    .Build();

try
{
    donHangSvc.XacNhanDatHang(donHang4);
}
catch (VoucherKhongHopLeException ex)
{
    Console.WriteLine($"  → Bắt được lỗi voucher: {ex.Message}");
}
catch (NgoaiLeUngDung) { }

Console.WriteLine();

// ─── Kiểm tra tồn kho sau khi đặt hàng ──────────────────────────────────
Console.WriteLine("══════════════════════════════════════════════════");
Console.WriteLine("  TỒN KHO SAU KHI ĐẶT HÀNG:");
Console.WriteLine("══════════════════════════════════════════════════");
foreach (var sp in sanPhamRepo.LayTatCa())
    Console.WriteLine($"  {sp}");

Console.WriteLine("\n  Nhấn phím bất kỳ để thoát...");
Console.ReadKey();
