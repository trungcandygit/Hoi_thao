namespace BanTraiCay.Models
{
    /// <summary>
    /// Trạng thái xử lý đơn hàng
    /// </summary>
    public enum TrangThaiDonHang
    {
        ChoDuyet,
        DaXacNhan,
        DangGiao,
        HoanThanh,
        DaHuy
    }

    /// <summary>
    /// Đơn hàng đặt trái cây
    /// </summary>
    public class DonHang
    {
        public int MaDonHang { get; set; }
        public int MaKhachHang { get; set; }
        public string TenKhachHang { get; set; } = string.Empty;
        public string DiaChi { get; set; } = string.Empty;
        public DateTime NgayDatHang { get; set; } = DateTime.Now;
        public TrangThaiDonHang TrangThai { get; set; } = TrangThaiDonHang.ChoDuyet;

        public List<ChiTietDonHang> DanhSachSanPham { get; set; } = new();

        /// <summary>
        /// Mã voucher được áp dụng (có thể null nếu không dùng khuyến mãi)
        /// </summary>
        public string? MaVoucher { get; set; }

        public decimal TongTienGoc => DanhSachSanPham.Sum(sp => sp.ThanhTien);
        public decimal SoTienGiam { get; set; }
        public decimal TongTienSauGiam => TongTienGoc - SoTienGiam;

        public void HienThiDonHang()
        {
            Console.WriteLine("═══════════════════════════════════════════════════");
            Console.WriteLine($"  ĐƠN HÀNG #{MaDonHang} - {NgayDatHang:dd/MM/yyyy HH:mm}");
            Console.WriteLine("═══════════════════════════════════════════════════");
            Console.WriteLine($"  Khách hàng : {TenKhachHang}");
            Console.WriteLine($"  Địa chỉ    : {DiaChi}");
            Console.WriteLine("───────────────────────────────────────────────────");
            Console.WriteLine($"  {"Sản Phẩm",-20} {"SL",5} {"Đơn Giá",12} {"Thành Tiền",14}");
            Console.WriteLine("───────────────────────────────────────────────────");
            foreach (var ct in DanhSachSanPham)
                Console.WriteLine($"  {ct.TenSanPham,-20} {ct.SoLuong,5} {ct.DonGia,12:N0} {ct.ThanhTien,14:N0}");
            Console.WriteLine("───────────────────────────────────────────────────");
            Console.WriteLine($"  {"Tổng Tiền Gốc:",-30} {TongTienGoc,14:N0} VNĐ");
            if (SoTienGiam > 0)
            {
                Console.WriteLine($"  {"Giảm Giá (" + MaVoucher + "):",-30} -{SoTienGiam,13:N0} VNĐ");
                Console.WriteLine($"  {"Tổng Tiền Thanh Toán:",-30} {TongTienSauGiam,14:N0} VNĐ");
            }
            Console.WriteLine($"  Trạng thái : {TrangThai}");
            Console.WriteLine("═══════════════════════════════════════════════════");
        }
    }
}
