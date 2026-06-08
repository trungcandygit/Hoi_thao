using BanTraiCay.Exceptions;
using BanTraiCay.Interfaces;
using BanTraiCay.Models;

namespace BanTraiCay.Services
{
    /// <summary>
    /// Service xử lý nghiệp vụ đặt hàng.
    /// Phụ thuộc vào các interface → dễ thay thế & kiểm thử (Dependency Injection).
    /// </summary>
    public class DonHangService : IDonHangService
    {
        private readonly ISanPhamRepository _sanPhamRepo;
        private readonly IDonHangRepository _donHangRepo;
        private readonly IKhuyenMaiRepository _khuyenMaiRepo;
        private readonly ITinhGiaService _tinhGiaSvc;

        // Constructor Injection — tuân thủ Dependency Injection
        public DonHangService(
            ISanPhamRepository sanPhamRepo,
            IDonHangRepository donHangRepo,
            IKhuyenMaiRepository khuyenMaiRepo,
            ITinhGiaService tinhGiaSvc)
        {
            _sanPhamRepo  = sanPhamRepo;
            _donHangRepo  = donHangRepo;
            _khuyenMaiRepo = khuyenMaiRepo;
            _tinhGiaSvc   = tinhGiaSvc;
        }

        /// <summary>
        /// Xử lý toàn bộ luồng xác nhận đặt hàng:
        ///   1. Validate đầu vào
        ///   2. Kiểm tra tồn kho
        ///   3. Áp dụng khuyến mãi
        ///   4. Lưu đơn hàng
        ///   5. Cập nhật tồn kho
        /// </summary>
        public DonHang XacNhanDatHang(DonHang donHang)
        {
            try
            {
                // --- Bước 1: Validate đơn hàng ---
                KiemTraDonHangHopLe(donHang);

                // --- Bước 2: Kiểm tra & đồng bộ giá từ CSDL ---
                DongBoGiaSanPham(donHang);

                // --- Bước 3: Kiểm tra số lượng tồn kho ---
                KiemTraTonKho(donHang);

                // --- Bước 4: Áp dụng khuyến mãi ---
                ApDungKhuyenMai(donHang);

                // --- Bước 5: Lưu đơn hàng ---
                donHang.TrangThai = TrangThaiDonHang.DaXacNhan;
                var donHangDaLuu = _donHangRepo.Luu(donHang);

                // --- Bước 6: Trừ tồn kho ---
                CapNhatTonKho(donHang);

                Console.WriteLine($"\n  ✔ Đặt hàng thành công! Mã đơn: #{donHangDaLuu.MaDonHang}");
                return donHangDaLuu;
            }
            catch (NgoaiLeUngDung ex)
            {
                // Lỗi nghiệp vụ đã được định nghĩa rõ → log và ném lại để tầng trên xử lý
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"\n  [LỖI NGHIỆP VỤ] {ex.Message}");
                Console.ResetColor();
                throw;
            }
            catch (Exception ex)
            {
                // Lỗi hệ thống không mong đợi → bọc lại để che thông tin nội bộ
                Console.ForegroundColor = ConsoleColor.DarkRed;
                Console.WriteLine($"\n  [LỖI HỆ THỐNG] Không thể xử lý đơn hàng. Vui lòng thử lại.");
                Console.ResetColor();
                throw new NgoaiLeUngDung("Lỗi hệ thống khi xử lý đặt hàng.", ex);
            }
        }

        // ── Các phương thức hỗ trợ nội bộ ────────────────────────────────────

        private static void KiemTraDonHangHopLe(DonHang donHang)
        {
            if (donHang.DanhSachSanPham == null || donHang.DanhSachSanPham.Count == 0)
                throw new DonHangRongException();

            foreach (var ct in donHang.DanhSachSanPham)
            {
                if (ct.SoLuong <= 0)
                    throw new NgoaiLeUngDung($"Số lượng sản phẩm \"{ct.TenSanPham}\" phải lớn hơn 0.");
            }
        }

        private void DongBoGiaSanPham(DonHang donHang)
        {
            foreach (var ct in donHang.DanhSachSanPham)
            {
                var sanPham = _sanPhamRepo.LayTheoMa(ct.MaSanPham)
                    ?? throw new SanPhamKhongTonTaiException(ct.MaSanPham);

                // Lấy giá chính thức từ CSDL, không tin giá từ client
                ct.TenSanPham = sanPham.TenSanPham;
                ct.DonGia     = sanPham.GiaBan;
            }
        }

        private void KiemTraTonKho(DonHang donHang)
        {
            foreach (var ct in donHang.DanhSachSanPham)
            {
                var sanPham = _sanPhamRepo.LayTheoMa(ct.MaSanPham)!;
                if (sanPham.SoLuongTonKho < ct.SoLuong)
                    throw new TonKhoKhongDuException(sanPham.TenSanPham, ct.SoLuong, sanPham.SoLuongTonKho);
            }
        }

        private void ApDungKhuyenMai(DonHang donHang)
        {
            if (string.IsNullOrWhiteSpace(donHang.MaVoucher)) return;

            var khuyenMai = _khuyenMaiRepo.LayTheoMaVoucher(donHang.MaVoucher)
                ?? throw new VoucherKhongHopLeException(donHang.MaVoucher, "Mã voucher không tồn tại");

            if (!khuyenMai.ConHieuLuc)
                throw new VoucherKhongHopLeException(donHang.MaVoucher, "Voucher đã hết hạn sử dụng");

            if (donHang.TongTienGoc < khuyenMai.DonHangToiThieu)
                throw new VoucherKhongHopLeException(donHang.MaVoucher,
                    $"Đơn hàng tối thiểu {khuyenMai.DonHangToiThieu:N0} VNĐ để áp dụng mã này");

            donHang.SoTienGiam = _tinhGiaSvc.TinhSoTienGiam(donHang.TongTienGoc, khuyenMai);
        }

        private void CapNhatTonKho(DonHang donHang)
        {
            foreach (var ct in donHang.DanhSachSanPham)
            {
                var sanPham = _sanPhamRepo.LayTheoMa(ct.MaSanPham)!;
                _sanPhamRepo.CapNhatTonKho(ct.MaSanPham, sanPham.SoLuongTonKho - ct.SoLuong);
            }
        }
    }
}
