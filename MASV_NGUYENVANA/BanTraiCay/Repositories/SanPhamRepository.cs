using BanTraiCay.Interfaces;
using BanTraiCay.Models;

namespace BanTraiCay.Repositories
{
    /// <summary>
    /// Triển khai repository sản phẩm — dữ liệu giả lập trong bộ nhớ
    /// (thực tế sẽ thay bằng Entity Framework + SQL Server)
    /// </summary>
    public class SanPhamRepository : ISanPhamRepository
    {
        // Dữ liệu giả lập — thay thế bằng DbContext trong dự án thực
        private readonly List<SanPham> _danhSachSanPham = new()
        {
            new SanPham { MaSanPham = 1, TenSanPham = "Xoài Cát Hòa Lộc", GiaBan = 85_000, SoLuongTonKho = 50 },
            new SanPham { MaSanPham = 2, TenSanPham = "Sầu Riêng Ri6",     GiaBan = 120_000, SoLuongTonKho = 30 },
            new SanPham { MaSanPham = 3, TenSanPham = "Bưởi Da Xanh",      GiaBan = 45_000, SoLuongTonKho = 80 },
            new SanPham { MaSanPham = 4, TenSanPham = "Chôm Chôm Đồng Nai", GiaBan = 35_000, SoLuongTonKho = 100 },
            new SanPham { MaSanPham = 5, TenSanPham = "Nhãn Lồng Hưng Yên", GiaBan = 55_000, SoLuongTonKho = 60 },
        };

        public SanPham? LayTheoMa(int maSanPham)
            => _danhSachSanPham.FirstOrDefault(sp => sp.MaSanPham == maSanPham);

        public IEnumerable<SanPham> LayTatCa() => _danhSachSanPham;

        public void CapNhatTonKho(int maSanPham, int soLuongMoi)
        {
            var sanPham = _danhSachSanPham.FirstOrDefault(sp => sp.MaSanPham == maSanPham);
            if (sanPham != null)
                sanPham.SoLuongTonKho = soLuongMoi;
        }
    }
}
