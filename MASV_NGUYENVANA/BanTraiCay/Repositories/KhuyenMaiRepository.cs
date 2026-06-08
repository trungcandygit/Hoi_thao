using BanTraiCay.Interfaces;
using BanTraiCay.Models;

namespace BanTraiCay.Repositories
{
    /// <summary>
    /// Triển khai repository khuyến mãi — dữ liệu giả lập trong bộ nhớ
    /// </summary>
    public class KhuyenMaiRepository : IKhuyenMaiRepository
    {
        private readonly List<KhuyenMai> _danhSachKhuyenMai = new()
        {
            new KhuyenMai
            {
                MaKhuyenMai  = 1,
                MaVoucher    = "GIAM50K",
                TenKhuyenMai = "Giảm 50.000 VNĐ cho đơn từ 200.000 VNĐ",
                LoaiKhuyenMai    = LoaiKhuyenMai.GiamTheoTienMat,
                GiaTriGiam   = 50_000,
                DonHangToiThieu = 200_000,
                NgayBatDau   = new DateTime(2025, 1, 1),
                NgayKetThuc  = new DateTime(2026, 12, 31)
            },
            new KhuyenMai
            {
                MaKhuyenMai  = 2,
                MaVoucher    = "GIAM10PCT",
                TenKhuyenMai = "Giảm 10% tối đa 100.000 VNĐ",
                LoaiKhuyenMai    = LoaiKhuyenMai.GiamTheoPhantram,
                GiaTriGiam   = 10,          // 10%
                DonHangToiThieu = 100_000,
                NgayBatDau   = new DateTime(2025, 1, 1),
                NgayKetThuc  = new DateTime(2026, 12, 31)
            },
            new KhuyenMai
            {
                MaKhuyenMai  = 3,
                MaVoucher    = "HET_HAN",
                TenKhuyenMai = "Voucher đã hết hạn",
                LoaiKhuyenMai    = LoaiKhuyenMai.GiamTheoTienMat,
                GiaTriGiam   = 30_000,
                DonHangToiThieu = 0,
                NgayBatDau   = new DateTime(2020, 1, 1),
                NgayKetThuc  = new DateTime(2021, 12, 31)
            }
        };

        public KhuyenMai? LayTheoMaVoucher(string maVoucher)
            => _danhSachKhuyenMai.FirstOrDefault(
                km => km.MaVoucher.Equals(maVoucher, StringComparison.OrdinalIgnoreCase));

        public IEnumerable<KhuyenMai> LayKhuyenMaiDangHieuLuc()
            => _danhSachKhuyenMai.Where(km => km.ConHieuLuc);
    }
}
