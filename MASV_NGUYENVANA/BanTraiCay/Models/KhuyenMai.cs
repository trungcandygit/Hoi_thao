namespace BanTraiCay.Models
{
    /// <summary>
    /// Loại khuyến mãi áp dụng cho đơn hàng
    /// </summary>
    public enum LoaiKhuyenMai
    {
        GiamTheoTienMat,    // Giảm cố định theo VNĐ
        GiamTheoPhantram,   // Giảm theo %
        MuaNTangM           // Mua N kg tặng M kg
    }

    /// <summary>
    /// Thông tin mã khuyến mãi / voucher
    /// </summary>
    public class KhuyenMai
    {
        public int MaKhuyenMai { get; set; }
        public string MaVoucher { get; set; } = string.Empty;
        public string TenKhuyenMai { get; set; } = string.Empty;
        public LoaiKhuyenMai LoaiKhuyenMai { get; set; }

        /// <summary>
        /// Giá trị giảm: số tiền (VNĐ) hoặc phần trăm (0-100) tuỳ LoaiKhuyenMai
        /// </summary>
        public decimal GiaTriGiam { get; set; }

        /// <summary>
        /// Giá trị đơn hàng tối thiểu để áp dụng mã
        /// </summary>
        public decimal DonHangToiThieu { get; set; }

        public DateTime NgayBatDau { get; set; }
        public DateTime NgayKetThuc { get; set; }
        public bool ConHieuLuc => DateTime.Now >= NgayBatDau && DateTime.Now <= NgayKetThuc;
    }
}
