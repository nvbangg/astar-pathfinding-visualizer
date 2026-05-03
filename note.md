<!-- Chủ đề: Mô phỏng trực quan Sử dụng thuật toán tìm kiếm A* để tìm ra đường đi ngắn nhất từ điểm xuất phát đến điểm đích trong một lưới không gian 2 chiều có vật cản. -->
<!-- Tên: A star Pathfinding Visualizer -->

# 1. Thành phần trên trang hiển thị gồm phần:

## 1.1. Bản đồ lưới cố định
Hệ thống lưới 2D tương tác trực tiếp bằng chuột:

- Start Node (Xanh lá đậm): Điểm bắt đầu (Kéo đổi vị trí khi chưa chạy (sau clear path)).
- End Node (Đỏ): Điểm đích (Kéo để đổi vị trí khi chưa chạy (sau clear path)).
- Obstacles/Walls (Xám đậm):
    - Click chuột trái: Thêm tường.
    - Click vào ô tường hiện có: Xóa tường.
    - Click và kéo: Vẽ/Xóa tường liên tục.
- Open Set (Xanh lá): Các ô đang chờ xét.
- Closed Set (Xanh lá nhạt): Các ô đã duyệt qua.
- Final Path (Vàng): Các ô thuộc đường đi ngắn nhất tìm được.

## 1.2. Side Panel bên phải
Sắp xếp theo thứ tự từ trên xuống:

### 1.2.1. Settings
- Heuristic (Dropdown): Euclidean, Manhattan, Octile, Chebyshev, Dijkstra (h=0).
- Options (Checkboxes):
    - Allow Diagonal (Cho phép đi chéo). Nếu bật, hiển thị thêm:
        - Don't Cross Corners: Không cho phép đi chéo 1 góc tường. Bình thường Vẫn bị Chặn đi chéo khi bị kẹp giữa hai vật cản nhưng vẫn đi chéo 1 góc tường được.
        - Diagonal Cost = 1 (Mặc định không tích là $1.41$).
    - Bi-directional (Tìm kiếm hai chiều từ Start và End).
- Speed (Slider): Điều chỉnh tốc độ hiển thị quá trình tìm kiếm.

### 1.2.2 Controls
Tên các nút hiển thị trên giao diện:

- Start / Pause: Đổi màu Xanh (khi sẵn sàng) và Vàng (khi đang chạy).
- Next Step: Chạy từng bước một để quan sát logic.
- Clear Path: Xóa kết quả tìm kiếm (Open/Closed/Path), giữ lại tường.
- Clear Walls: Xóa sạch tường và kết quả, đưa lưới về trạng thái trống.
- Random Walls: Rải vật cản ngẫu nhiên trên bản đồ.
- Random Maze: Tạo mê cung có logic (ví dụ dùng thuật toán Recursive Backtracking).
- Compare All: Chạy lần lượt tất cả các Heuristic trên cùng một bản đồ, sau đó hiển thị bảng tổng hợp so sánh Statistics trong một cửa sổ riêng (có thể đóng lại)

### 1.2.3 Statistics
Hiển thị kết quả sau khi thuật toán kết thúc:
- Path Cost: Tổng chiều dài đường đi ngắn nhất (ô màu Vàng).
- Visited Nodes: Tổng số ô đã duyệt qua (ô Xanh lá nhạt).
- Max Open Nodes: Kích thước lớn nhất của danh sách chờ (Open Set) trong suốt quá trình chạy.
- Search Time: Thời gian tính toán trong compare all hoặc thời gian chạy hiển thị khi demo
- Operations: Tổng số lượt xử lý tính toán trong thuật toán. (không phụ thuộc cpu)

# 2. Lưu ý
- dùng python tkinter trong 1 file duy nhất
- cửa sổ có thể mở rộng toàn màn hình
- Giao diện đơn giản nhưng đầy đủ chức năng, thuật toán logic chính xác.
- Code tối ưu ngắn gọn đơn giản nhất có thể, tận dụng những thứ đã có sẵn mà không cần code lại, không có code thừa. Tên biến đặt dễ hiểu không viết tắt khi không cần thiết
- Chỉ comment bằng tiếng việt ở những nơi thật sự cần thiết để giải thích
- Đảm bảo thuật toán hoạt động chính xác, ngắn gọn,rõ ràng, dễ hiểu, dễ bảo trì

# 3. Xây dựng bộ test
## 3.1 Yêu cầu: 
- Giữ nguyên main.py, tạo file mới test_runner.py import class App từ main.py Nhờ vào hàm _run_astar(instant=True) đã xây dựng, bạn có thể gọi trực tiếp nó từ file test để lấy kết quả mà không cần chạy giao diện người dùng.
- Khi so sánh Actual và Expected, bạn nên sử dụng abs(actual - expected) < 0.01 thay vì so sánh bằng (==) để tránh lỗi do Python làm tròn số
- Định dạng hiển thị: Khi in Actual và Expected, hãy dùng :.2f để luôn hiển thị 2 chữ số sau dấu phẩy cho đẹp và đồng nhất.


## 3.2 Mẫu json chứa dữ liệu bộ test: file test_cases.json
```json
[
  {
    "name": "Mô tả kịch bản test",
    "matrix": [
      [0, 0, 0],
      [0, 1, 0],
      [0, 0, 0]
    ],
    "start": [0, 0],
    "end": [2, 2],
    "expected_costs": {
      "no_diagonal": 5.0,
      "diagonal_normal": 3.83,
      "diagonal_dont_cross": 5.0,
      "diagonal_cost1": 3.0,
      "diagonal_cost1_dont_cross": 5.0
    }
  }
]
```

## 3.2 Số lượng tổ hợp kết quả: 
Tổ hợp 1: Allow Diagonal = Tắt (Các option con không quan trọng).
Tổ hợp 2: Allow Diagonal = Bật | Don't Cross = Tắt | Diag Cost 1 = Tắt.
Tổ hợp 3: Allow Diagonal = Bật | Don't Cross = Bật | Diag Cost 1 = Tắt.
Tổ hợp 4: Allow Diagonal = Bật | Don't Cross = Tắt | Diag Cost 1 = Bật.
Tổ hợp 5: Allow Diagonal = Bật | Don't Cross = Bật | Diag Cost 1 = Bật.

## 3.3 Kết quả hiển thị:

----------
SCENARIO 1: Mô tả kịch bản test

[T1_No_Diag]
  - Euclidean  (Bi:OFF): PASS  | (Bi:ON): PASS
  - Manhattan  (Bi:OFF): PASS  | (Bi:ON): PASS
  - Octile     (Bi:OFF): PASS  | (Bi:ON): PASS
  - Chebyshev  (Bi:OFF): PASS  | (Bi:ON): PASS
  - Dijkstra   (Bi:OFF): PASS  | (Bi:ON): PASS
[T2_Diag_Normal]
  - Euclidean  (Bi:OFF): PASS  | (Bi:ON): FAIL (Expected: 3.83, Actual: 4.00)
  - Manhattan  (Bi:OFF): PASS  | (Bi:ON): PASS
  ... (tương tự)
[T3_Diag_Dont_Cross]
  ... (tương tự)
[T4_Diag_Cost1_Normal]
  ... (tương tự)
[T5_Diag_Cost1_Dont_Cross]
  ... (tương tự)

RESULT: 49/50 PASS.
----------
----------
SCENARIO 2: Mô tả kịch bản test 2
...
----------
