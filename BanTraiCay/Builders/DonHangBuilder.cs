using BanTraiCay.Models;

namespace BanTraiCay.Builders
{
    // ╔══════════════════════════════════════════════════════════════════╗
    // ║  BUILDER PATTERN — Tách rời việc xây dựng đối tượng DonHang    ║
    // ║  khỏi logic nghiệp vụ, giúp tạo đơn hàng linh hoạt và rõ ràng. ║
    // ╚══════════════════════════════════════════════════════════════════╝

    /// <summary>
    /// Builder tạo đối tượng <see cref="DonHang"/> theo từng bước — Builder Pattern.
    /// Sử dụng Method Chaining để code tạo đơn hàng dễ đọc như ngôn ngữ tự nhiên.
    /// </summary>
    public class DonHangBuilder
    {
        private readonly DonHang _donHang = new();

        public DonHangBuilder VoiKhachHang(int maKhachHang, string hoTen, string diaChi)
        {
            _donHang.MaKhachHang  = maKhachHang;
            _donHang.TenKhachHang = hoTen;
            _donHang.DiaChi       = diaChi;
            return this;
        }

        public DonHangBuilder ThemSanPham(int maSanPham, int soLuong)
        {
            _donHang.DanhSachSanPham.Add(new ChiTietDonHang
            {
                MaSanPham = maSanPham,
                SoLuong   = soLuong,
                // TenSanPham & DonGia sẽ được đồng bộ từ CSDL trong DonHangService
            });
            return this;
        }

        public DonHangBuilder ApDungVoucher(string maVoucher)
        {
            _donHang.MaVoucher = maVoucher;
            return this;
        }

        /// <summary>
        /// Hoàn thiện và trả về đối tượng DonHang đã được cấu hình.
        /// </summary>
        public DonHang Build() => _donHang;
    }
}
