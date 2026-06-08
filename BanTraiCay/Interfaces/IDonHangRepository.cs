using BanTraiCay.Models;

namespace BanTraiCay.Interfaces
{
    /// <summary>
    /// Hợp đồng lưu trữ đơn hàng (Repository Pattern)
    /// </summary>
    public interface IDonHangRepository
    {
        DonHang Luu(DonHang donHang);
        DonHang? LayTheoMa(int maDonHang);
        IEnumerable<DonHang> LayTatCa();
    }
}
