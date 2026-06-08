using BanTraiCay.Interfaces;
using BanTraiCay.Models;

namespace BanTraiCay.Services
{
    /// <summary>
    /// Triển khai dịch vụ tính giá — hỗ trợ nhiều loại chiết khấu khác nhau.
    /// Thêm loại chiết khấu mới chỉ cần mở rộng switch, không sửa logic cũ.
    /// </summary>
    public class TinhGiaService : ITinhGiaService
    {
        // Giới hạn giảm tối đa cho loại GiamTheoPhantram để tránh giảm quá nhiều
        private const decimal GiamToiDaTheoPhantram = 100_000m;

        public decimal TinhSoTienGiam(decimal tongTienGoc, KhuyenMai khuyenMai)
        {
            return khuyenMai.LoaiKhuyenMai switch
            {
                LoaiKhuyenMai.GiamTheoTienMat =>
                    // Giảm cố định, không vượt quá tổng tiền
                    Math.Min(khuyenMai.GiaTriGiam, tongTienGoc),

                LoaiKhuyenMai.GiamTheoPhantram =>
                    // Giảm theo %, có áp trần GiamToiDaTheoPhantram
                    Math.Min(tongTienGoc * khuyenMai.GiaTriGiam / 100m, GiamToiDaTheoPhantram),

                LoaiKhuyenMai.MuaNTangM =>
                    // Mua N tặng M: GiaTriGiam = số kg tặng × đơn giá trung bình
                    // Ở đây đơn giản hoá: GiaTriGiam là số tiền tương đương hàng tặng
                    Math.Min(khuyenMai.GiaTriGiam, tongTienGoc),

                _ => 0m
            };
        }

        public decimal TinhTongTienSauGiam(decimal tongTienGoc, KhuyenMai? khuyenMai)
        {
            if (khuyenMai is null) return tongTienGoc;
            var soTienGiam = TinhSoTienGiam(tongTienGoc, khuyenMai);
            return Math.Max(tongTienGoc - soTienGiam, 0m);
        }
    }
}
