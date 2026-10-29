# Hà Nội Traffic Lab

[Mở trình giả lập](https://loveless2001.github.io/hanoi-traffic-lab/) · [Báo cáo](https://loveless2001.github.io/hanoi-traffic-lab/report.html)

Tự vẽ đường và thêm/xóa đường nhánh trên một phần mạng đường Hà Nội, rồi chạy
hiện trạng và phương án mới với **chính xác cùng một tập chuyến đi**: cùng
điểm đi–đến, giờ xuất phát và loại xe.

Đây là **mô phỏng thử nghiệm dùng mạng đường thật**, chưa hiệu chỉnh thực địa
và không phải dự báo giao thông Hà Nội năm 2026.

## Sử dụng

1. Chọn **Vẽ đường** hoặc **Thêm nhánh** và vẽ ở bản đồ bên phải.
2. Chấm điểm đầu trên đường, thêm điểm giữa trên nền, rồi chấm vào một đường
   để kết thúc. Giữ Shift khi chấm để buộc tạo điểm giữa.
3. Dùng **Xóa tuyến / Hoàn tác** để chỉnh sửa. Xóa đường mẹ sẽ xóa cả nhánh phụ thuộc.
4. Chọn tổng chuyến/ngày và phân bố 24 giờ, rồi bấm **So sánh hai phương án**.
5. Phát/dừng hoặc tua thời gian chung để xem số chuyến hoàn thành, thời gian chờ,
   spillback, throughput và xe còn chờ ngoài mạng.

Hai phương án giữ nguyên nhu cầu; không tự cộng nhu cầu phát sinh cho đường mới.
Bật nối giao cắt để giả định các giao cắt mới cùng mức, hoặc tắt để chỉ nối các
đầu tuyến được chọn. Phương án được lưu trong trình duyệt đang sử dụng.

## Chạy cục bộ và cập nhật trang

Ứng dụng là trang tĩnh, không cần backend hay bước cài đặt thư viện JavaScript.
Tệp `index.html` đã nhúng mạng đường, dân cư và D3; có thể mở trực tiếp.

```sh
python -m http.server 8765 --bind 127.0.0.1
```

Mở `http://127.0.0.1:8765/`. Sau khi sửa mã nguồn hoặc giao diện, dựng lại:

```sh
python scripts/build_site.py
node check_engines.cjs
node check_editor.cjs
python check_model.py
```

Commit và push `main` để GitHub Pages cập nhật từ thư mục gốc của repo.
`scripts/build_site.py` dùng thư viện chuẩn Python; không cần Node packages.

## Tệp chính

| Tệp | Vai trò |
| --- | --- |
| `index.html`, `simulator.html` | Bản chạy đã dựng, dùng trên GitHub Pages hoặc offline |
| `viewer.js` | Giao diện vẽ đường, bản đồ và so sánh đồng bộ |
| `editor.js` | Chia cạnh tại điểm nối, dựng giao lộ, tính lại đường đi |
| `engine.js` | Động cơ hàng đợi hữu hạn, hai loại xe |
| `simulation.py`, `experiment.py` | Bộ thí nghiệm Python và 124 trường hợp khảo sát |
| `scripts/simulator-fragment.html` | Mẫu giao diện và các nhãn điều khiển |
| `scripts/build_site.py` | Dựng trang tĩnh từ mã nguồn và dữ liệu |
| `network_base.json`, `network_base.geojson` | Mạng đường trục chính OSM đã rút gọn |
| `population.json`, `population_worldpop_2020_clip.tif` | Lớp dân cư WorldPop 2020 |
| `report.html`, `sources.json` | Phương pháp, kết quả, giả định và nguồn |

## Kiểm định và tái lập

13 kiểm tra mạng tự vẽ: định tuyến, đường mới được sử dụng, xóa nhánh, bảo toàn
xe, dung tích hữu hạn, giữ nguyên offset của nút không thay đổi và cùng nhu cầu.
Ba fixture đối chiếu JavaScript với Python khớp đến sai số số thực dưới 10⁻⁶.
Kết quả kiểm tra giao diện gồm vẽ bằng chuột/chạm, xóa/hoàn tác, tuyến nhiều điểm,
tua giờ, khôi phục thiết kế và bố cục màn hình nhỏ.

```sh
node run_comparison.cjs paired_example_design.json paired_example_config.json paired_result.json
```

Đọc `README.txt` để xem định nghĩa chỉ số, toàn bộ tệp dữ liệu và bộ thí nghiệm.
Các kiểm tra triển khai không thay thế hiệu chỉnh và kiểm định bằng đo đạc thực địa.

## Nguồn và giấy phép

- [OpenStreetMap contributors](https://www.openstreetmap.org/copyright): hình học,
  kết nối và đường một chiều; dữ liệu và cơ sở dữ liệu dẫn xuất theo ODbL.
- [WorldPop 2020](https://hub.worldpop.org/geodata/summary?id=6449): ước tính dân cư
  khoảng 100 m; CC BY 4.0. Không phải dân số đo đạc năm 2026.
- [JICA BRT Hà Nội 2016](https://openjicareport.jica.go.jp/pdf/12266391_02.pdf):
  tư liệu lịch sử và giới hạn nguồn. Repo liên kết về bản gốc, không lưu lại PDF.
- [D3 v7.9.0](https://github.com/d3/d3): thư viện bản đồ, giấy phép ISC.

Mã nguồn mô hình và giao diện theo MIT (`LICENSE`). Xem `LICENSE-DATA.txt` cho dữ liệu.
Không cần tài khoản, không gửi thiết kế đường lên máy chủ; việc tính toán chạy trong trình duyệt.
