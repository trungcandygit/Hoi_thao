using BanTraiCay.Models;

namespace BanTraiCay.Interfaces
{
    /// <summary>
    /// Hợp đồng nghiệp vụ xử lý đơn hàng
    /// </summary>
    public interface IDonHangService
    {
        /// <summary>
        /// Xác nhận & đặt hàng: kiểm tra tồn kho, áp dụng khuyến mãi, lưu đơn hàng
        /// </summary>
        DonHang XacNhanDatHang(DonHang donHang);
    }
}
