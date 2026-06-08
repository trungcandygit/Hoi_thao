namespace BanTraiCay.Models
{
    /// <summary>
    /// Thông tin khách hàng đặt hàng
    /// </summary>
    public class KhachHang
    {
        public int MaKhachHang { get; set; }
        public string HoTen { get; set; } = string.Empty;
        public string SoDienThoai { get; set; } = string.Empty;
        public string DiaChi { get; set; } = string.Empty;
    }
}
