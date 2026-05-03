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
        - Allow Cross Corners: Cho phép đi sát 1 góc tường. Vẫn bị Chặn đi chéo khi bị kẹp giữa hai vật cản
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
