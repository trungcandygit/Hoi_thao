namespace BanTraiCay.Models
{
    /// <summary>
    /// Đại diện cho một sản phẩm trái cây trong hệ thống
    /// </summary>
    public class SanPham
    {
        public int MaSanPham { get; set; }
        public string TenSanPham { get; set; } = string.Empty;
        public decimal GiaBan { get; set; }           // Đơn vị: VNĐ/kg
        public int SoLuongTonKho { get; set; }        // Đơn vị: kg
        public string DonViTinh { get; set; } = "kg";

        public override string ToString()
            => $"[{MaSanPham}] {TenSanPham} - Giá: {GiaBan:N0} VNĐ/{DonViTinh} - Tồn kho: {SoLuongTonKho} {DonViTinh}";
    }
}
