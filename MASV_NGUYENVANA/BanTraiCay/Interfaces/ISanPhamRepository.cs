using BanTraiCay.Models;

namespace BanTraiCay.Interfaces
{
    /// <summary>
    /// Hợp đồng truy xuất dữ liệu sản phẩm (Repository Pattern)
    /// </summary>
    public interface ISanPhamRepository
    {
        SanPham? LayTheoMa(int maSanPham);
        IEnumerable<SanPham> LayTatCa();
        void CapNhatTonKho(int maSanPham, int soLuongMoi);
    }
}
