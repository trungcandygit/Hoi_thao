# BL-K_IO VN30

Tái lập nghiên cứu **Inverse Black-Litterman + K-means clustering** trên rổ **VN30**
(mở rộng từ 25 cổ phiếu ngân hàng sang toàn rổ VN30).

---

## Cấu trúc dự án

```
BL_K_IO_VN30/
├── config.yaml              # Mọi tham số (ngày, cửa sổ, k, TC, …)
├── main.py                  # Điểm vào pipeline
├── requirements.txt
├── data/
│   ├── raw/                 # CSV thủ công hoặc dữ liệu tải về
│   └── processed/           # Parquet cache (tự động tạo)
├── src/
│   ├── data_loader.py
│   ├── features.py
│   ├── clustering.py
│   ├── black_litterman.py
│   ├── optimizer.py
│   ├── backtest.py
│   ├── metrics.py
│   ├── robustness.py
│   └── visualization.py
├── tests/
│   ├── test_black_litterman.py
│   └── test_optimizer.py
├── notebooks/               # Phân tích khám phá (tùy chọn)
└── results/                 # Output: CSV, PNG (tự động tạo)
```

---

## Cài đặt

```bash
pip install -r requirements.txt
```

---

## Cách cấp dữ liệu thủ công (khuyến nghị)

Đặt file CSV vào `data/raw/`. DataLoader sẽ đọc trực tiếp (ưu tiên hơn vnstock).

### 1. `prices.csv` — Giá đóng cửa điều chỉnh theo tháng

| Cột       | Kiểu        | Mô tả                              |
|-----------|-------------|-------------------------------------|
| `date`    | YYYY-MM-DD  | Ngày cuối tháng (hoặc ngày bất kỳ trong tháng) |
| `ticker`  | string      | Mã CK (VD: ACB, VCB)               |
| `close`   | float       | Giá đóng cửa đã điều chỉnh cổ tức  |

Ví dụ:
```
date,ticker,close
2014-06-30,ACB,12500
2014-06-30,VCB,35200
...
```

Nguồn: FiinPro, Wichart, TCBS, SSI ResearchGateway, hoặc export từ Bloomberg.

### 2. `market_cap.csv` — Vốn hóa thị trường theo tháng

| Cột          | Kiểu        | Mô tả                     |
|--------------|-------------|---------------------------|
| `date`       | YYYY-MM-DD  |                           |
| `ticker`     | string      |                           |
| `market_cap` | float       | Vốn hóa (tỷ VND hoặc VND, nhất quán) |

### 3. `vn30_constituents.csv` — Thành phần VN30 theo kỳ *(tùy chọn nhưng khuyến nghị)*

| Cột              | Kiểu        | Mô tả                              |
|------------------|-------------|-------------------------------------|
| `effective_date` | YYYY-MM-DD  | Ngày kỳ review bắt đầu có hiệu lực |
| `ticker`         | string      |                                     |

Nếu không cấp file này, code dùng danh sách VN30 hiện tại (có survivorship bias).

### 4. `risk_free.csv` — Lãi suất phi rủi ro *(tùy chọn)*

| Cột    | Kiểu  | Mô tả                              |
|--------|-------|-------------------------------------|
| `year` | int   | Năm                                 |
| `rate` | float | Lãi suất TPCP 10Y dạng thập phân (VD: 0.055 = 5.5%) |

Nếu không cấp, code dùng 5.5%/năm cố định.

---

## Chạy pipeline

```bash
# Chạy toàn bộ (cần có dữ liệu trong data/raw/)
python main.py

# Bỏ qua robustness (nhanh hơn để kiểm tra)
python main.py --skip-robustness

# Tải lại dữ liệu (xóa cache)
python main.py --force-reload

# Dùng config tùy chỉnh
python main.py --config my_config.yaml
```

---

## Chạy unit tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Kết quả đầu ra (`results/`)

| File                        | Nội dung                                      |
|-----------------------------|-----------------------------------------------|
| `oos_returns.csv`           | Lợi suất tháng OOS mỗi chiến lược             |
| `weights_log.csv`           | Trọng số BL_K_IO tại mỗi bước                 |
| `metrics.csv`               | Bảng chỉ số (full / bull / disrupted)         |
| `sharpe_tests.csv`          | Bootstrap Sharpe difference tests             |
| `cumulative_returns.png`    | Biểu đồ cumulative return                     |
| `drawdown.png`              | Biểu đồ drawdown                              |
| `metrics_table.png`         | Bảng chỉ số dạng hình                         |
| `robustness_sweep.csv`      | Kết quả param sweep                           |
| `heatmap_sweep.png`         | Heatmap Sharpe (window × max_weight)           |
| `mc_robustness.csv`         | Phân phối Sharpe Monte Carlo                  |
| `mc_distribution.png`       | Biểu đồ MC                                    |

---

## Phương pháp tóm tắt

1. **K-means clustering**: phân cụm cổ phiếu theo idiosyncratic momentum (6-1) và
   low-volatility, được chuẩn hóa z-score. Chọn k tối ưu bằng 5 tiêu chí (Elbow,
   Silhouette, Calinski-Harabász, Davies-Bouldin, Gap statistic).

2. **View vector**: cụm momentum cao nhất = long view, cụm thấp nhất = short view.
   Ma trận P (2×N) và vector q xây dựng từ kết quả phân cụm.

3. **Inverse Black-Litterman** (Bertsimas et al., 2012):
   `μ_post = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹ [(τΣ)⁻¹Π + PᵀΩ⁻¹q]`

4. **SLSQP**: cực đại Sharpe ratio với ràng buộc Σwᵢ=1, 0≤wᵢ≤MAX_WEIGHT.

5. **Rolling OOS**: cửa sổ 36 tháng, test 1 tháng, dynamic basket.

6. **Chi phí giao dịch**: khấu trừ `tc_bps/10000 × 0.5×Σ|Δw|` mỗi tháng.

---

## Trích dẫn

- Bertsimas, D., Gupta, V., & Paschalidis, I. C. (2012). *Inverse optimization: A new
  perspective on the Black-Litterman model.*
- DeMiguel, V., Garlappi, L., & Uppal, R. (2009). *Optimal versus naive diversification.*
- Tibshirani, R., Walther, G., & Hastie, T. (2001). *Estimating the number of clusters
  in a data set via the gap statistic.*
