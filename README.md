# Hà Nội Traffic Lab

[Mở trình giả lập](https://loveless2001.github.io/hanoi-traffic-lab/) · [Báo cáo](https://loveless2001.github.io/hanoi-traffic-lab/report.html)

Tự vẽ đường và thêm/xóa đường nhánh trên mạng đường Hà Nội phủ toàn vùng
trong Vành đai 3 và dải đệm, rồi chạy
hiện trạng và phương án mới với **chính xác cùng một tập chuyến đi**: cùng
điểm đi–đến, giờ xuất phát và loại xe.

Đây là **mô phỏng thử nghiệm dùng mạng đường thật**, chưa hiệu chỉnh thực địa
và không phải dự báo giao thông Hà Nội năm 2026.

## Sử dụng

Chọn **Toàn vùng trong Vành đai 3 + dải đệm** (mặc định), hoặc trở về vùng
Láng–Giảng Võ của các thí nghiệm ban đầu. Mạng mới có 57.175 nút hình học,
140.718 đoạn có hướng, 815 nút đèn suy ra từ OSM và 81 điểm đi–đến tổng hợp.
Khung phủ khoảng 752 km² là diện tích cả dải đệm, không phải diện tích một
đa giác chính thức của Vành đai 3. Phóng to để chỉnh sửa đường địa phương.
Thiết kế của từng vùng được lưu riêng trong trình duyệt.

**Chi tiết đường** mặc định là **Ẩn đường ngõ**: ẩn residential, living_street
và unclassified theo phân loại OSM; **Chỉ trục chính** ẩn thêm tertiary;
**Hiện tất cả** khôi phục toàn mạng trên bản đồ. Các đường nối `_link` của
nhóm được chọn vẫn hiện, cùng mọi đường/nhánh tự vẽ. Đây là bộ lọc hiển thị,
không xác định chính xác bề rộng đường ngoài thực tế. Không bắt điểm vẽ vào
đường đang ẩn.

**Chỉ mô phỏng đường đang hiện** mặc định được bật: loại đường bị ẩn cũng bị
loại khỏi mạng tính toán. Đổi bộ lọc cần chạy lại. Tập chuyến gốc giữ nguyên
số lượng, giờ xuất phát, loại xe và điểm địa lý. Những điểm đi–đến nằm ngoài
mạng còn lại được đưa tới các nút gần nhất, khác nhau, trong vùng liên thông
cho cả ô tô/xe máy của **hiện trạng sau lọc**. Phép gán này chỉ làm một lần,
dùng chung cho cả hai phương án; không tạo OD riêng để ưu ái đường mới.
Khoảng dịch điểm lớn nhất được ghi ở dòng kết quả. Chặng từ nhà/ngõ đến đường
chính không được mô phỏng, nên đây là thí nghiệm trên mạng trục, không phải
dự báo tác động đóng ngõ. Đường tự vẽ vẫn được giữ, nhưng một tuyến chỉ nối
với các ngõ đã bỏ có thể không được xe sử dụng.

Bỏ chọn **Chỉ mô phỏng đường đang hiện** để dùng bộ lọc như một lớp hiển thị:
mô phỏng vẫn dùng toàn mạng và đổi bộ lọc không xóa kết quả đang xem. Lựa chọn
được đồng bộ giữa hai bản đồ và lưu trong trình duyệt.

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
Mạng lớn được tải từ `regions/inside-ring3.json.gz` (~6,9 MB), giải nén trong
trình duyệt; có bản JSON dự phòng cho trình duyệt không hỗ trợ giải nén.
Hãy dùng máy chủ HTTP bên dưới hoặc GitHub Pages. Khi mở trực tiếp tệp HTML,
có thể dùng vùng Láng–Giảng Võ nhúng sẵn; mạng lớn cần được tải qua HTTP.
Phần mô phỏng chạy trong Web Worker, có nút **Dừng tính**; hai bản đồ vẫn kéo
và phóng được trong khi tính toán. Vùng lớn có thể mất vài chục giây đến vài
phút tùy thiết bị, số chuyến và phương án.

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
| `simulation-worker.js` | Chạy cặp mô phỏng ngoài luồng giao diện |
| `network-scope.js` | Lọc lớp đường, gán điểm đi–đến dùng chung, ánh xạ xe về bản đồ |
| `regions/inside-ring3.json`, `.json.gz` | Mạng mở rộng, lớp dân cư ~300 m, nước và điểm đi–đến |
| `data/rr3_*` | Snapshot OSM, raster dân cư gốc đã cắt, nguồn và hàm băm |
| `scripts/build_rr3.py` | Dựng lại mạng lớn và cộng dân cư 3×3 ô |
| `region-report.html`, `rr3_model_checks.json` | Giả định và kiểm tra riêng cho vùng lớn |
| `simulation.py`, `experiment.py` | Bộ thí nghiệm Python và 124 trường hợp khảo sát |
| `scripts/simulator-fragment.html` | Mẫu giao diện và các nhãn điều khiển |
| `scripts/build_site.py` | Dựng trang tĩnh từ mã nguồn và dữ liệu |
| `network_base.json`, `network_base.geojson` | Mạng đường trục chính OSM đã rút gọn |
| `population.json`, `population_worldpop_2020_clip.tif` | Lớp dân cư WorldPop 2020 |
| `report.html`, `sources.json` | Phương pháp, kết quả, giả định và nguồn |

## Kiểm định và tái lập

Đọc [phương pháp vùng mở rộng](https://loveless2001.github.io/hanoi-traffic-lab/region-report.html).
Mạng lớn lấy từ snapshot Geofabrik/OSM 27/10/2026. Chặn xe máy trên motorway
và cạnh có thẻ cấm tương ứng; không tự nối giao cắt mới với cầu/hầm, layer
khác 0 hoặc motorway. Nhánh và điểm nối do người dùng chọn vẫn tạo kết nối
thật trong đồ thị. Chưa có đầy đủ cấm rẽ và hạn chế phụ thuộc thời gian.
Nhu cầu 45.000 chuyến, tỷ lệ xe máy 80%, tốc độ, dung tích và chu kỳ đèn đều
là giả định, không phải số đo của toàn Hà Nội. Dân cư 2020 chỉ dùng cho lớp
hiển thị và trọng số điểm đi; điểm đến còn ngẫu nhiên, chưa có OD thực địa.

124 thí nghiệm và các khoảng tin cậy trong báo cáo cũ chỉ thuộc vùng nhỏ
8,15 km²; không được áp các kết luận đó sang vùng lớn. Chạy kiểm tra vùng mới:

```sh
node check_rr3.cjs
node check_scope.cjs
```

Kiểm tra này dùng 45.000 chuyến cho hiện trạng và phương án đường + nhánh
ngoài vùng cũ, đối chiếu bảo toàn xe, dung tích hữu hạn, định tuyến theo loại
xe và bộ lập lịch nhanh với quét toàn mạng. `rr3_model_checks.json` lưu kết quả.
Dựng lại dữ liệu đã đóng gói (cần Python, networkx, numpy, rasterio):

```sh
python scripts/build_rr3.py --source data/rr3_osm_snapshot.json.gz --population data/rr3_worldpop_2020_clip.tif
python scripts/build_site.py
```

`scripts/extract_rr3.py` (cần osmium) có thể trích lại snapshot từ PBF Vietnam
đúng ngày; URL và SHA-256 của PBF nằm trong `data/rr3_provenance.json`.

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
- [Geofabrik Vietnam](https://download.geofabrik.de/asia/vietnam.html): nguồn
  PBF cho vùng mở rộng, snapshot 27/10/2026 21:23:59 UTC.
- [WorldPop 2020](https://hub.worldpop.org/geodata/summary?id=6449): ước tính dân cư
  khoảng 100 m; CC BY 4.0. Không phải dân số đo đạc năm 2026.
- [JICA BRT Hà Nội 2016](https://openjicareport.jica.go.jp/pdf/12266391_02.pdf):
  tư liệu lịch sử và giới hạn nguồn. Repo liên kết về bản gốc, không lưu lại PDF.
- [D3 v7.9.0](https://github.com/d3/d3): thư viện bản đồ, giấy phép ISC.

Mã nguồn mô hình và giao diện theo MIT (`LICENSE`). Xem `LICENSE-DATA.txt` cho dữ liệu.
Không cần tài khoản, không gửi thiết kế đường lên máy chủ; việc tính toán chạy trong trình duyệt.
