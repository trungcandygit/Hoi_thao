namespace BanTraiCay.Exceptions
{
    /// <summary>
    /// Ngoại lệ gốc của ứng dụng — tất cả lỗi nghiệp vụ kế thừa từ đây
    /// </summary>
    public class NgoaiLeUngDung : Exception
    {
        public NgoaiLeUngDung(string thongBao) : base(thongBao) { }
        public NgoaiLeUngDung(string thongBao, Exception cauBenTrong) : base(thongBao, cauBenTrong) { }
    }

    /// <summary>
    /// Sản phẩm không tồn tại trong hệ thống
    /// </summary>
    public class SanPhamKhongTonTaiException : NgoaiLeUngDung
    {
        public int MaSanPham { get; }
        public SanPhamKhongTonTaiException(int maSanPham)
            : base($"Sản phẩm với mã [{maSanPham}] không tồn tại trong hệ thống.")
        {
            MaSanPham = maSanPham;
        }
    }

    /// <summary>
    /// Số lượng tồn kho không đủ để xử lý đơn hàng
    /// </summary>
    public class TonKhoKhongDuException : NgoaiLeUngDung
    {
        public string TenSanPham { get; }
        public int YeuCau { get; }
        public int HienCo { get; }

        public TonKhoKhongDuException(string tenSanPham, int yeuCau, int hienCo)
            : base($"Sản phẩm \"{tenSanPham}\" không đủ tồn kho. Yêu cầu: {yeuCau}, Hiện có: {hienCo}.")
        {
            TenSanPham = tenSanPham;
            YeuCau = yeuCau;
            HienCo = hienCo;
        }
    }

    /// <summary>
    /// Mã voucher không hợp lệ hoặc đã hết hạn
    /// </summary>
    public class VoucherKhongHopLeException : NgoaiLeUngDung
    {
        public string MaVoucher { get; }
        public VoucherKhongHopLeException(string maVoucher, string lyDo)
            : base($"Mã voucher \"{maVoucher}\" không hợp lệ: {lyDo}.")
        {
            MaVoucher = maVoucher;
        }
    }

    /// <summary>
    /// Đơn hàng rỗng — không có sản phẩm nào
    /// </summary>
    public class DonHangRongException : NgoaiLeUngDung
    {
        public DonHangRongException()
            : base("Đơn hàng phải có ít nhất một sản phẩm.") { }
    }
}
