using BanTraiCay.Interfaces;
using BanTraiCay.Models;

namespace BanTraiCay.Repositories
{
    /// <summary>
    /// Triển khai repository đơn hàng — dữ liệu giả lập trong bộ nhớ
    /// </summary>
    public class DonHangRepository : IDonHangRepository
    {
        private readonly List<DonHang> _danhSachDonHang = new();
        private int _soThuTu = 1;

        public DonHang Luu(DonHang donHang)
        {
            donHang.MaDonHang = _soThuTu++;
            _danhSachDonHang.Add(donHang);
            return donHang;
        }

        public DonHang? LayTheoMa(int maDonHang)
            => _danhSachDonHang.FirstOrDefault(dh => dh.MaDonHang == maDonHang);

        public IEnumerable<DonHang> LayTatCa() => _danhSachDonHang;
    }
}
