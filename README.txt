CẬP NHẬT PHẠM VI 29/10/2026
Mặc định hiện là toàn vùng trong Vành đai 3 và dải đệm (~752 km²).
Xem README.md, region-report.html và data/rr3_provenance.json cho nguồn và
kiểm tra riêng. 124 thí nghiệm được mô tả bên dưới vẫn thuộc vùng nhỏ cũ.
Mạng lớn cần mở qua HTTP/GitHub Pages, không mở tệp trực tiếp.

HÀ NỘI: ĐƯỜNG MỚI, TRUY NHẬP VÀ HÀNG ĐỢI
Ngày tạo: 29/10/2026 (Asia/Bangkok)

MỞ BẢN CHẠY
Mở simulator.html trong trình duyệt. Tất cả dữ liệu và thư viện bản đồ đã nhúng
trong tệp này; không cần mạng hay cài đặt. report.html là báo cáo có nguồn,
công thức, giới hạn mô hình và kết quả 124 trường hợp thí nghiệm.

Đây là toy simulation dùng một phần mạng đường thật, KHÔNG phải dự báo đã
hiệu chỉnh thực địa của Hà Nội năm 2026. Nguồn dữ liệu lịch sử không đủ để
xác định nhu cầu OD, pha đèn và hành vi xe máy hiện tại.

TRONG GIAO DIỆN
- Vẽ trên bản đồ bên phải; bản đồ trái luôn là hiện trạng.
- Chọn Vẽ đường hoặc Thêm nhánh. Chấm lên đường có sẵn để đặt điểm đầu;
  chấm nền để thêm điểm giữa; chấm vào đường để nối điểm cuối và hoàn tất.
  Giữ Shift khi chấm để buộc thêm một điểm giữa, không tự bắt vào đường.
- Chọn Xóa tuyến rồi chấm lên đường / nhánh tự vẽ, hoặc dùng nút xóa trong
  Các tuyến đã vẽ. Xóa đường cũng xóa các nhánh phụ thuộc; có Hoàn tác.
- Bật Nối các giao cắt mới cùng mức để tự nối chỗ đường tự vẽ cắt mạng.
  Tắt lựa chọn này thì chỉ nối các đầu tuyến đã chọn. Vòng nhỏ đánh dấu
  các điểm nối được dựng trong mô hình. Giao lộ mới giả định đèn 90 giây.
- Nhập tổng chuyến xe mỗi ngày. Hai phương án dùng đúng CÙNG MỘT tập chuyến:
  cùng điểm đi/đến, giờ xuất phát và loại xe; không thêm nhu cầu phát sinh.
  Chỉ đường đi và xung đột được tính lại theo mạng của từng phương án.
- Chọn mẫu thời gian hoặc nhập 24 trọng số từ 00h đến 23h. Các trọng số
  tự chuẩn hóa; không cần cộng thành 100.
- Có thể đổi tỷ lệ xe máy, seed và cách phân bổ điểm đi theo dân cư.
  Bấm So sánh hai phương án để tính lại cả hai với cùng đồng hồ.
- Phát/dừng hoặc kéo thanh thời gian. Thoát mạng là tốc độ hoàn thành trong
  cửa sổ 15 phút gần nhất, quy đổi xe/giờ. Chờ và spillback là tích lũy.
- Mô phỏng 24 giờ phát sinh + 1 giờ xả. Xe chưa xong và xe chờ ngoài mạng
  vẫn được giữ và tính chờ. Chấm xe là vị trí minh họa, không phải quỹ đạo
  vi mô hoặc dữ liệu GPS. Dữ liệu dân cư là WorldPop 2020, không phải 2026.

CHẠY LẠI KHÔNG CẦN GIAO DIỆN
Mở cửa sổ lệnh trong thư mục này. Python 3.10+ và Node 18+ là đủ; động cơ
không cần cài thư viện bổ sung.

  python check_model.py
  python simulation.py --scenario S3 --seed 42 --demand 9000 --trace --out example_90min.json
  python experiment.py
  node run_daily.cjs daily_config.json daily_result.json
  node check_engines.cjs
  node check_editor.cjs
  node run_comparison.cjs editor_example_design.json daily_config.json paired_result.json

experiment.py chạy lại 124 trường hợp và ghi đè results.json/results.jsonl.
Nó dùng 2 tiến trình. Bộ thử chính gồm 40 lượt (5 kịch bản x 8 seed).
84 lượt còn lại quét nhu cầu, loại xe, PCU, dòng bão hòa, dung tích, đèn,
nhánh, nhu cầu phát sinh, bước thời gian và thời gian xả dài hơn.

simulation.py: thử nghiệm 60 phút nhu cầu + 30 phút xả, phân bố tam giác,
20 điểm đi tổng hợp, chọn điểm đến cách ít nhất 1 km. Dùng RNG Python.
run_daily.cjs (giao diện phiên bản đầu): 24 trọng số theo giờ, 45.000 chuyến
gốc/ngày, 80% xe máy, S3 tăng 20%. Tùy chọn điểm đi theo dân cư; điểm đến
vẫn tổng hợp. Dùng RNG Mulberry32 của JavaScript. Vì thiết kế nhu cầu và RNG
khác nhau, không so trực tiếp giá trị của lượt chạy ngày với bộ 90 phút.
check_engines.cjs đưa cùng chính xác tập chuyến sang hai động cơ để đối chiếu.
simulator.html hiện tại / run_comparison.cjs dùng mạng tự vẽ và nhu cầu cố
định theo cặp. run_comparison.cjs luôn tắt phát sinh thêm nhu cầu, kể cả khi
tệp cấu hình cũ ghi S3 hoặc induction > 0.

DỮ LIỆU VÀ KẾT QUẢ
- network_base.json / .geojson: mạng trục chính OSM rút gọn.
- ui_data.json: mạng kịch bản và đường đi đã biên dịch cho giao diện.
- population_worldpop_2020_clip.tif / population.json: dữ liệu dân cư đã cắt.
- historical_observations.json: bảng JICA và giới hạn diễn giải từng bảng.
- sources.json: URL, loại nguồn và cách sử dụng.
- results.json / .jsonl: mỗi lượt có tham số, bảo toàn theo loại xe, hoàn
  thành, chờ, spillback, xe chưa xong, throughput và số đo kiểm tra.
- summary.json: trung bình, khoảng 95% và chênh lệch ghép cùng seed.
- checks.json: 11 kiểm tra số học/cơ chế. Không phải kiểm định thực địa.
- cross_language_checks.json: đối chiếu S0/S2/S3 giữa Python và JavaScript.
- browser_checks.json: kiểm tra điều khiển, đầu vào sai và bố cục 360 px.
- editor.js / viewer.js: biên dịch đường tự vẽ thành mạng và giao diện so sánh.
- editor_model_checks.json: 13 kiểm tra mạng, tuyến mới, xóa nhánh, cùng nhu cầu;
  giữ nguyên mã nút/offset ở giao lộ không đổi khi thêm nhánh ở nơi khác.
- editor_browser_checks.json: vẽ bằng thao tác bản đồ, xóa/hoàn tác, chạy ghép,
  tua giờ, khôi phục phương án và kiểm tra màn hình nhỏ.
- daily_result.json: kết quả mặc định của giao diện theo từng phút.
- reference_fixtures.json: tập chuyến cố định để đối chiếu động cơ.
- manifest.json: SHA-256 của các tệp cung cấp.

ĐỊNH NGHĨA
Spillback_link_min = tổng độ dài bước thời gian trên các cạnh có ít nhất
một lần đầu hàng đủ điều kiện đi bị từ chối vì cạnh sau không còn đủ chỗ,
đổi sang đoạn-phút. Không phải chiều dài hàng đợi đo thực địa.
Throughput của thử nghiệm 90 phút = số hành trình hoàn thành / 1,5 giờ.
Total_wait_veh_h gồm chờ tại nguồn và chờ nội mạng của mọi xe, kể cả xe
chưa hoàn thành. Mean/p95_completed_delay chỉ xét xe đã xong, có thiên lệch
cắt ngang; không dùng làm thước đo duy nhất.

TÁI TẠO MẠNG / BÁO CÁO / GIAO DIỆN
Các tệp nguồn xây dựng nằm trong reproduction. Chỉ bước này cần cài thêm
networkx, numpy, matplotlib hoặc rasterio, tùy tác vụ.

  python reproduction/build_network.py --source reproduction/osm_snapshot.json --output .
  python reproduction/export_ui.py --model-dir . --data-only
  python reproduction/build_report.py --model-dir .
  python reproduction/build_ui.py --model-dir . --fragment reproduction/simulator-fragment.html --d3 reproduction/d3.min.js --inline-path preview-fragment.html

OSM snapshot đã được thu nhỏ về các way đường trục và các node tham chiếu;
không có sửa hình học. Các quan hệ cấm rẽ chưa được đưa vào động cơ.
GeoTIFF dân cư đã cắt là dữ liệu nguồn đủ để tái vẽ và tạo trọng số điểm đi.
Đường mới và bốn nhánh chỉ là hình học thí nghiệm, không phải đề xuất
quy hoạch hoặc thiết kế đã xét giải phóng mặt bằng.

Đọc LICENSE-DATA.txt và LICENSE-CODE.txt trước khi phân phối lại.
