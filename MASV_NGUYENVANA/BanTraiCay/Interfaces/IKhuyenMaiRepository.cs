using BanTraiCay.Models;

namespace BanTraiCay.Interfaces
{
    /// <summary>
    /// Hợp đồng truy xuất dữ liệu khuyến mãi (Repository Pattern)
    /// </summary>
    public interface IKhuyenMaiRepository
    {
        KhuyenMai? LayTheoMaVoucher(string maVoucher);
        IEnumerable<KhuyenMai> LayKhuyenMaiDangHieuLuc();
    }
}
