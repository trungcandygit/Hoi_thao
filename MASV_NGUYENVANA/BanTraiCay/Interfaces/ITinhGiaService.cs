using BanTraiCay.Models;

namespace BanTraiCay.Interfaces
{
    /// <summary>
    /// Interface dịch vụ tính giá — cho phép mở rộng nhiều loại chiết khấu
    /// mà không sửa code hiện có (Open/Closed Principle).
    /// </summary>
    public interface ITinhGiaService
    {
        /// <summary>
        /// Tính số tiền được giảm dựa trên tổng tiền gốc và mã khuyến mãi.
        /// </summary>
        /// <param name="tongTienGoc">Tổng tiền trước khi giảm giá</param>
        /// <param name="khuyenMai">Thông tin khuyến mãi áp dụng</param>
        /// <returns>Số tiền được giảm (VNĐ)</returns>
        decimal TinhSoTienGiam(decimal tongTienGoc, KhuyenMai khuyenMai);

        /// <summary>
        /// Tính tổng tiền cuối cùng sau khi áp dụng khuyến mãi.
        /// </summary>
        decimal TinhTongTienSauGiam(decimal tongTienGoc, KhuyenMai? khuyenMai);
    }
}
