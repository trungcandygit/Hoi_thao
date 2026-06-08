namespace BanTraiCay.Models
{
    /// <summary>
    /// Một dòng sản phẩm trong đơn hàng
    /// </summary>
    public class ChiTietDonHang
    {
        public int MaSanPham { get; set; }
        public string TenSanPham { get; set; } = string.Empty;
        public int SoLuong { get; set; }
        public decimal DonGia { get; set; }
        public decimal ThanhTien => SoLuong * DonGia;
    }
}
