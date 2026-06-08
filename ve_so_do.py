import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

os.makedirs('/home/user/Hoi_thao/diagrams', exist_ok=True)

# ─── Màu sắc theme ────────────────────────────────────────────────────────
C_HEADER  = '#1e3a5f'   # Navy đậm — header bảng
C_PK      = '#2e86ab'   # Blue — PK row
C_FK      = '#e8f4f8'   # Light blue — FK row
C_ROW     = '#ffffff'   # Trắng — row thường
C_BORDER  = '#1e3a5f'
C_TEXT_W  = 'white'
C_TEXT_D  = '#1e3a5f'
C_LINE    = '#e74c3c'   # Đỏ — đường quan hệ
C_NEW     = '#27ae60'   # Xanh lá — bảng mới

# ════════════════════════════════════════════════════════════════════════════
# HÀM TIỆN ÍCH
# ════════════════════════════════════════════════════════════════════════════

def ve_bang_erd(ax, x, y, ten_bang, cot_list, w=3.2, row_h=0.38, is_new=False):
    """
    cot_list: list of (icon, ten_cot, kieu_du_lieu)
    icon: 'PK', 'FK', ''
    Trả về (x_left, y_top, x_right, y_bottom, dict anchor)
    """
    header_h = 0.52
    n = len(cot_list)
    total_h = header_h + n * row_h

    header_color = C_NEW if is_new else C_HEADER

    # Viền ngoài
    border = FancyBboxPatch((x, y - total_h), w, total_h,
                            boxstyle="round,pad=0.04",
                            linewidth=1.8, edgecolor=C_BORDER,
                            facecolor='none', zorder=3)
    ax.add_patch(border)

    # Header
    hdr = FancyBboxPatch((x, y - header_h), w, header_h,
                         boxstyle="round,pad=0.02",
                         linewidth=0, edgecolor='none',
                         facecolor=header_color, zorder=2)
    ax.add_patch(hdr)
    ax.text(x + w/2, y - header_h/2, ten_bang,
            ha='center', va='center', fontsize=9.5, fontweight='bold',
            color='white', zorder=4)

    # Các cột
    anchors = {}
    for i, (icon, name, dtype) in enumerate(cot_list):
        ry = y - header_h - i * row_h
        if icon == 'PK':
            bg = '#dbeeff'
        elif icon == 'FK':
            bg = '#fff3cd'
        else:
            bg = C_ROW if i % 2 == 0 else '#f8f9fa'

        row_patch = plt.Rectangle((x, ry - row_h), w, row_h,
                                  linewidth=0.5, edgecolor='#dee2e6',
                                  facecolor=bg, zorder=2)
        ax.add_patch(row_patch)

        # Icon PK / FK
        if icon in ('PK', 'FK'):
            badge_color = '#2e86ab' if icon == 'PK' else '#e67e22'
            badge = FancyBboxPatch((x + 0.08, ry - row_h + 0.06), 0.38, row_h - 0.12,
                                  boxstyle="round,pad=0.02",
                                  facecolor=badge_color, edgecolor='none', zorder=3)
            ax.add_patch(badge)
            ax.text(x + 0.27, ry - row_h/2, icon,
                    ha='center', va='center', fontsize=6, fontweight='bold',
                    color='white', zorder=4)
            name_x = x + 0.54
        else:
            name_x = x + 0.14

        ax.text(name_x, ry - row_h/2, name,
                ha='left', va='center', fontsize=7.8, color='#212529', zorder=4)
        ax.text(x + w - 0.1, ry - row_h/2, dtype,
                ha='right', va='center', fontsize=7, color='#6c757d',
                style='italic', zorder=4)

        anchors[name] = (x + w/2, ry - row_h/2)

    return x, y, x + w, y - total_h, anchors


def ve_duong_quan_he(ax, x1, y1, x2, y2, label='', color=C_LINE):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=1.6, connectionstyle='arc3,rad=0.05'))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.12, label, ha='center', va='bottom',
                fontsize=7.5, color=color, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor=color, boxstyle='round,pad=0.2', lw=0.8))


# ════════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 1 — ERD đầy đủ
# ════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(18, 11))
ax.set_xlim(0, 18)
ax.set_ylim(0, 11)
ax.axis('off')
fig.patch.set_facecolor('#f0f4f8')
ax.set_facecolor('#f0f4f8')

ax.text(9, 10.7, 'SƠ ĐỒ ERD — HỆ THỐNG BÁN TRÁI CÂY (MỞ RỘNG MODULE KHUYẾN MÃI)',
        ha='center', va='center', fontsize=13, fontweight='bold', color=C_HEADER)
ax.text(9, 10.35, '⬛ Bảng hiện có     🟩 Bảng mới (Module Quản Lý Khuyến Mãi)',
        ha='center', va='center', fontsize=9, color='#555')

# ── Bảng KHACH_HANG (1.0, 9.8) ───────────────────────────────────────────
x1,y1,x1r,y1b,_ = ve_bang_erd(ax, 1.0, 9.8, 'KHACH_HANG', [
    ('PK', 'MaKhachHang',  'INT'),
    ('',   'HoTen',        'NVARCHAR(100)'),
    ('',   'SoDienThoai',  'NVARCHAR(15)'),
    ('',   'DiaChi',       'NVARCHAR(255)'),
    ('',   'Email',        'NVARCHAR(100)'),
], w=3.4)

# ── Bảng DON_HANG (6.3, 9.8) ─────────────────────────────────────────────
x2,y2,x2r,y2b,_ = ve_bang_erd(ax, 6.3, 9.8, 'DON_HANG', [
    ('PK', 'MaDonHang',        'INT'),
    ('FK', 'MaKhachHang',      'INT'),
    ('FK', 'MaVoucher',        'NVARCHAR(50)'),
    ('',   'NgayDatHang',      'DATETIME'),
    ('',   'TrangThai',        'NVARCHAR(30)'),
    ('',   'TongTienGoc',      'DECIMAL(18,2)'),
    ('',   'SoTienGiam',       'DECIMAL(18,2)'),
    ('',   'TongTienThanhToan','DECIMAL(18,2)'),
], w=3.6)

# ── Bảng CHI_TIET_DON_HANG (11.5, 9.8) ──────────────────────────────────
x3,y3,x3r,y3b,_ = ve_bang_erd(ax, 11.5, 9.8, 'CHI_TIET_DON_HANG', [
    ('PK', 'MaChiTiet',   'INT'),
    ('FK', 'MaDonHang',   'INT'),
    ('FK', 'MaSanPham',   'INT'),
    ('',   'SoLuong',     'INT'),
    ('',   'DonGia',      'DECIMAL(18,2)'),
    ('',   'ThanhTien',   'DECIMAL(18,2)'),
], w=3.6)

# ── Bảng SAN_PHAM (11.5, 4.8) ────────────────────────────────────────────
x4,y4,x4r,y4b,_ = ve_bang_erd(ax, 11.5, 4.8, 'SAN_PHAM', [
    ('PK', 'MaSanPham',       'INT'),
    ('',   'TenSanPham',      'NVARCHAR(100)'),
    ('',   'GiaBan',          'DECIMAL(18,2)'),
    ('',   'SoLuongTonKho',   'INT'),
    ('',   'DonViTinh',       'NVARCHAR(10)'),
    ('',   'MoTa',            'NVARCHAR(500)'),
], w=3.6)

# ── Bảng KHUYEN_MAI (1.0, 5.5) — MỚI ────────────────────────────────────
x5,y5,x5r,y5b,_ = ve_bang_erd(ax, 1.0, 5.5, 'KHUYEN_MAI  (MỚI)', [
    ('PK', 'MaKhuyenMai',     'INT'),
    ('',   'MaVoucher',       'NVARCHAR(50) UNIQUE'),
    ('',   'TenKhuyenMai',    'NVARCHAR(200)'),
    ('',   'LoaiKhuyenMai',   'NVARCHAR(30)'),
    ('',   'GiaTriGiam',      'DECIMAL(18,2)'),
    ('',   'DonHangToiThieu', 'DECIMAL(18,2)'),
    ('',   'NgayBatDau',      'DATETIME'),
    ('',   'NgayKetThuc',     'DATETIME'),
], w=3.8, is_new=True)

# ── Đường quan hệ ─────────────────────────────────────────────────────────
# KHACH_HANG → DON_HANG  (1:N)
ve_duong_quan_he(ax, x1r, (y1+y1b)/2, x2, (y2+y2b)/2, '1 : N')

# DON_HANG → CHI_TIET_DON_HANG  (1:N)
ve_duong_quan_he(ax, x2r, (y2+y2b)/2, x3, (y3+y3b)/2, '1 : N')

# SAN_PHAM → CHI_TIET_DON_HANG  (1:N) — đường dọc
ve_duong_quan_he(ax, (x3+x3r)/2, y3b, (x4+x4r)/2, y4, '1 : N', color='#8e44ad')

# KHUYEN_MAI → DON_HANG  (1:N) — đường mới
ve_duong_quan_he(ax, x5r, (y5+y5b)/2 + 0.5,
                 x2, y2b + 0.3, '1 : N  (nullable)', color=C_NEW)

# ── Chú thích loại quan hệ ───────────────────────────────────────────────
legend_x, legend_y = 1.0, 1.8
ax.text(legend_x, legend_y, 'CHÚ THÍCH:', fontsize=8.5, fontweight='bold', color=C_HEADER)
items = [
    ('#2e86ab', 'PK — Khóa chính (Primary Key)'),
    ('#e67e22', 'FK — Khóa ngoại (Foreign Key)'),
    (C_LINE,    '── Quan hệ bảng hiện có'),
    (C_NEW,     '── Quan hệ bảng mới (Khuyến Mãi)'),
    ('#8e44ad', '── Quan hệ Sản Phẩm → Chi Tiết'),
]
for i, (color, text) in enumerate(items):
    ax.add_patch(plt.Rectangle((legend_x, legend_y - 0.45*(i+1)), 0.28, 0.22,
                               facecolor=color, edgecolor='none'))
    ax.text(legend_x + 0.38, legend_y - 0.45*(i+1) + 0.11, text,
            va='center', fontsize=7.5, color='#333')

plt.tight_layout()
plt.savefig('/home/user/Hoi_thao/diagrams/erd.png', dpi=150, bbox_inches='tight',
            facecolor='#f0f4f8')
plt.close()
print('✔ ERD xong')


# ════════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 2 — Interface ITinhGiaService (Class Diagram)
# ════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(13, 7))
ax.set_xlim(0, 13)
ax.set_ylim(0, 7)
ax.axis('off')
fig.patch.set_facecolor('#f0f4f8')

ax.text(6.5, 6.7, 'SƠ ĐỒ CLASS — INTERFACE TÍNH GIÁ & CÁC LOẠI KHUYẾN MÃI',
        ha='center', fontsize=12, fontweight='bold', color=C_HEADER)

def ve_class_box(ax, x, y, stereotype, ten, methods, w=3.6, is_interface=False):
    row_h = 0.42
    header_h = 0.88
    n = len(methods)
    total_h = header_h + n * row_h

    hdr_color = '#2e86ab' if is_interface else '#1e3a5f'
    border = FancyBboxPatch((x, y - total_h), w, total_h,
                            boxstyle="round,pad=0.05",
                            linewidth=2, edgecolor=hdr_color, facecolor='white', zorder=2)
    ax.add_patch(border)

    hdr = FancyBboxPatch((x, y - header_h), w, header_h,
                         boxstyle="round,pad=0.03",
                         linewidth=0, facecolor=hdr_color, zorder=3)
    ax.add_patch(hdr)

    ax.text(x + w/2, y - 0.28, f'«{stereotype}»',
            ha='center', va='center', fontsize=7.5, color='#aed6f1',
            style='italic', zorder=4)
    ax.text(x + w/2, y - 0.62, ten,
            ha='center', va='center', fontsize=9.5, fontweight='bold',
            color='white', zorder=4)

    ax.plot([x, x+w], [y - header_h, y - header_h], color=hdr_color, lw=1.2, zorder=4)

    for i, (vis, sig) in enumerate(methods):
        ry = y - header_h - i * row_h
        bg = '#f8f9fa' if i % 2 == 0 else 'white'
        ax.add_patch(plt.Rectangle((x, ry - row_h), w, row_h,
                                   facecolor=bg, edgecolor='#dee2e6', lw=0.5, zorder=2))
        vis_color = '#27ae60' if vis == '+' else '#e74c3c'
        ax.text(x + 0.14, ry - row_h/2, vis, ha='center', va='center',
                fontsize=9, color=vis_color, fontweight='bold', zorder=4)
        ax.text(x + 0.28, ry - row_h/2, sig, ha='left', va='center',
                fontsize=7.3, color='#212529', zorder=4)

    return x + w/2, y - total_h  # bottom center

# Interface
ix, iy = 4.7, 6.2
ve_class_box(ax, ix, iy, 'interface', 'ITinhGiaService', [
    ('+', 'TinhSoTienGiam(tongTienGoc, khuyenMai)'),
    ('+', ': decimal'),
    ('+', 'TinhTongTienSauGiam(tongTienGoc,'),
    ('+', '  khuyenMai?) : decimal'),
], w=3.6, is_interface=True)

# Impl
ix2, iy2 = 4.7, 2.9
bx2, by2 = ve_class_box(ax, ix2, iy2, 'class', 'TinhGiaService', [
    ('-', 'GiamToiDaTheoPhantram = 100.000 VNĐ'),
    ('+', 'TinhSoTienGiam(...) : decimal'),
    ('+', 'TinhTongTienSauGiam(...) : decimal'),
], w=3.6)

# Mũi tên implements (đứt nét)
ax.annotate('', xy=(ix + 1.8, iy - 0.88 - 3*0.42),
            xytext=(ix2 + 1.8, iy2),
            arrowprops=dict(arrowstyle='-|>', color='#2e86ab', lw=1.8,
                            linestyle='dashed',
                            connectionstyle='arc3,rad=0'))
ax.text(ix + 1.8 + 0.15, (iy - 0.88 - 3*0.42 + iy2)/2,
        'implements', fontsize=7.5, color='#2e86ab', style='italic')

# KhuyenMai enum box
ex, ey = 0.5, 5.2
ve_class_box(ax, ex, ey, 'enum', 'LoaiKhuyenMai', [
    ('+', 'GiamTheoTienMat'),
    ('+', 'GiamTheoPhantram'),
    ('+', 'MuaNTangM'),
], w=2.8, is_interface=False)

# KhuyenMai model
mx, my = 9.2, 6.2
ve_class_box(ax, mx, my, 'class', 'KhuyenMai', [
    ('+', 'MaKhuyenMai : int'),
    ('+', 'MaVoucher : string'),
    ('+', 'LoaiKhuyenMai : LoaiKhuyenMai'),
    ('+', 'GiaTriGiam : decimal'),
    ('+', 'DonHangToiThieu : decimal'),
    ('+', 'NgayBatDau / NgayKetThuc'),
    ('+', 'ConHieuLuc : bool  {get}'),
], w=3.5)

# Mũi tên uses
ax.annotate('', xy=(mx, my - 1.2), xytext=(ix + 3.6, iy - 0.5),
            arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=1.3,
                            connectionstyle='arc3,rad=-0.2'))
ax.text(8.3, 4.7, 'uses', fontsize=7.5, color='#7f8c8d', style='italic')

# Mũi tên enum
ax.annotate('', xy=(ex + 2.8, ey - 1.2),
            xytext=(mx + 0.5, my - 2.1),
            arrowprops=dict(arrowstyle='->', color='#8e44ad', lw=1.3,
                            connectionstyle='arc3,rad=0.3'))
ax.text(5.5, 3.6, 'type', fontsize=7.5, color='#8e44ad', style='italic')

plt.tight_layout()
plt.savefig('/home/user/Hoi_thao/diagrams/interface_tinh_gia.png', dpi=150,
            bbox_inches='tight', facecolor='#f0f4f8')
plt.close()
print('✔ Interface diagram xong')


# ════════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 3 — Kiến trúc phân tầng
# ════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')
fig.patch.set_facecolor('#f0f4f8')

ax.text(7, 7.7, 'KIẾN TRÚC PHÂN TẦNG — HỆ THỐNG BÁN TRÁI CÂY',
        ha='center', fontsize=12, fontweight='bold', color=C_HEADER)

layers = [
    (6.8, 7.0, '#1e3a5f', 'TẦNG TRÌNH BÀY  (Presentation Layer)',
     'Program.cs — Console App', '#aed6f1'),
    (6.8, 5.5, '#154360', 'TẦNG NGHIỆP VỤ  (Business Logic Layer)',
     'DonHangService  ·  TinhGiaService', '#a9cce3'),
    (6.8, 4.0, '#1a5276', 'TẦNG TRUY XUẤT DỮ LIỆU  (Data Access Layer)',
     'SanPhamRepository  ·  DonHangRepository  ·  KhuyenMaiRepository', '#a8d8ea'),
    (6.8, 2.5, '#1f618d', 'TẦNG DỮ LIỆU  (Data Layer)',
     'In-Memory Store  →  SQL Server (production)', '#aab7b8'),
]

for cx, cy, color, title, subtitle, sub_color in layers:
    box = FancyBboxPatch((cx - 5.8, cy - 0.95), 11.6, 1.3,
                         boxstyle="round,pad=0.1",
                         linewidth=2, edgecolor=color, facecolor=color+'22', zorder=2)
    ax.add_patch(box)
    left_bar = plt.Rectangle((cx - 5.8, cy - 0.95), 0.18, 1.3,
                              facecolor=color, zorder=3)
    ax.add_patch(left_bar)
    ax.text(cx - 5.3, cy + 0.1, title,
            ha='left', va='center', fontsize=9.5, fontweight='bold', color=color, zorder=4)
    ax.text(cx - 5.3, cy - 0.4, subtitle,
            ha='left', va='center', fontsize=8.5, color='#555', zorder=4)

# Mũi tên phân tầng
for y_from, y_to in [(6.05, 5.95), (4.55, 4.45), (3.05, 2.95)]:
    ax.annotate('', xy=(7, y_to), xytext=(7, y_from),
                arrowprops=dict(arrowstyle='<->', color='#c0392b', lw=2))

# Interfaces DI
ax.text(9.5, 5.5, '«Dependency Injection»\nITinhGiaService\nIDonHangService',
        ha='center', va='center', fontsize=7.8, color='#2e86ab',
        bbox=dict(facecolor='white', edgecolor='#2e86ab', boxstyle='round,pad=0.4', lw=1.2))
ax.text(9.5, 4.0, '«Repository Pattern»\nISanPhamRepository\nIDonHangRepository\nIKhuyenMaiRepository',
        ha='center', va='center', fontsize=7.8, color='#27ae60',
        bbox=dict(facecolor='white', edgecolor='#27ae60', boxstyle='round,pad=0.4', lw=1.2))

plt.tight_layout()
plt.savefig('/home/user/Hoi_thao/diagrams/kien_truc_phan_tang.png', dpi=150,
            bbox_inches='tight', facecolor='#f0f4f8')
plt.close()
print('✔ Kiến trúc phân tầng xong')


# ════════════════════════════════════════════════════════════════════════════
# SƠ ĐỒ 4 — Luồng xử lý đặt hàng (Sequence/Flow)
# ════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14)
ax.set_ylim(0, 9)
ax.axis('off')
fig.patch.set_facecolor('#f0f4f8')

ax.text(7, 8.7, 'LUỒNG XỬ LÝ XÁC NHẬN ĐẶT HÀNG — Builder Pattern + DI',
        ha='center', fontsize=12, fontweight='bold', color=C_HEADER)

# Actors / components
actors = [
    (1.2,  'Người\nDùng',      '#e74c3c'),
    (3.4,  'DonHang\nBuilder', '#2e86ab'),
    (5.8,  'DonHang\nService', '#1e3a5f'),
    (8.0,  'SanPham\nRepo.',   '#27ae60'),
    (10.2, 'KhuyenMai\nRepo.', '#8e44ad'),
    (12.4, 'DonHang\nRepo.',   '#e67e22'),
]

for ax_x, label, color in actors:
    circle = plt.Circle((ax_x, 8.1), 0.38, color=color, zorder=3)
    ax.add_patch(circle)
    ax.text(ax_x, 8.1, label.split('\n')[0][0], ha='center', va='center',
            fontsize=10, fontweight='bold', color='white', zorder=4)
    ax.text(ax_x, 7.55, label, ha='center', va='top', fontsize=7.5,
            color=color, fontweight='bold', multialignment='center')
    ax.plot([ax_x, ax_x], [7.3, 0.3], color=color, lw=1, linestyle='--', alpha=0.4, zorder=1)

steps = [
    (1.2, 3.4, 7.2, '.VoiKhachHang(...)\n.ThemSanPham(...)\n.ApDungVoucher(...)\n.Build()', '#2e86ab'),
    (3.4, 5.8, 6.5, 'XacNhanDatHang(donHang)', '#1e3a5f'),
    (5.8, 8.0, 5.9, 'LayTheoMa(maSanPham)', '#27ae60'),
    (8.0, 5.8, 5.3, '← SanPham (giá chính thức)', '#27ae60'),
    (5.8, 8.0, 4.7, 'KiemTra TonKho', '#27ae60'),
    (5.8, 10.2, 4.1, 'LayTheoMaVoucher(maVoucher)', '#8e44ad'),
    (10.2, 5.8, 3.5, '← KhuyenMai (hợp lệ)', '#8e44ad'),
    (5.8, 12.4, 2.9, 'Luu(donHang) → MaDonHang', '#e67e22'),
    (5.8, 8.0, 2.3, 'CapNhatTonKho(maSanPham, soLuongMoi)', '#27ae60'),
    (5.8, 1.2, 1.7, '← DonHang (đã xác nhận)', '#e74c3c'),
]

for x1, x2, y, label, color in steps:
    direction = 1 if x2 > x1 else -1
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    mx = (x1 + x2) / 2
    ax.text(mx, y + 0.13, label, ha='center', va='bottom', fontsize=7,
            color=color,
            bbox=dict(facecolor='white', edgecolor=color, boxstyle='round,pad=0.15', lw=0.8, alpha=0.9))

plt.tight_layout()
plt.savefig('/home/user/Hoi_thao/diagrams/luong_dat_hang.png', dpi=150,
            bbox_inches='tight', facecolor='#f0f4f8')
plt.close()
print('✔ Luồng đặt hàng xong')

print('\nTất cả sơ đồ đã được lưu vào /home/user/Hoi_thao/diagrams/')
