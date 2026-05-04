import tkinter as tk
from tkinter import ttk
import heapq
import random
import time
import math

CELL_SIZE = 25
GRID_COLUMNS, GRID_ROWS = 45, 25
DEFAULT_SPEED = 95
DEFAULT_START_POS = (2, 2)
DEFAULT_END_POS = (GRID_COLUMNS - 3, GRID_ROWS - 3)
WALL_PROBABILITY = 0.2

DELAY_START = 10
DELAY_PAUSE = 50
MAX_SPEED_DELAY = 101

COLORS = {
    'empty': '#FFFFFF', 'wall': '#555555',
    'start': '#2E7D32', 'end': '#D32F2F',
    'open': '#74D377',  'closed': '#A5D6A7',
    'path': '#FFD600',  'grid': '#E0E0E0',
    'background_main': '#FAFAFA', 'background_panel': '#F5F5F5',
    'button_foreground': 'white',
    'button_start': '#4CAF50', 'button_pause': '#FF9800',
    'button_step': '#607D8B',  'button_clear_path': '#E53935',
    'button_clear_walls': '#E53935', 'button_random': '#795548',
    'button_compare': '#3F51B5',
    'header': '#E0E0E0', 'row': '#F9FBE7', 'error': '#FFEBEE',
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("A* Pathfinding Visualizer")
        self.geometry("1450x700")

        self.grid_data = [[0] * GRID_COLUMNS for _ in range(GRID_ROWS)]
        self.start_node = DEFAULT_START_POS
        self.end_node = DEFAULT_END_POS
        self.is_running = False
        self.is_paused = False
        self.is_step_mode = False
        self.has_step_event = False
        self.dragged_node_type = None
        self.draw_mode = None
        self.is_visualized = False

        self.animation_frames = []
        self.algorithm_result = None

        self.stats_vars = {key: tk.StringVar(value='-') for key in
                           ('path_cost', 'visited_nodes', 'execution_time', 'operations_count')}

        self._build_ui()
        self._draw_grid()

    def _build_ui(self):
        self.option_add('*TCombobox*Listbox.font', ('', 11))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=COLORS['background_main'], highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.bind('<Button-1>', self._handle_mouse_press)
        self.canvas.bind('<B1-Motion>', self._handle_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self._handle_mouse_release)

        panel = tk.Frame(self, width=320, bg=COLORS['background_panel'], padx=15, pady=15)
        panel.grid(row=0, column=1, sticky='ns')
        panel.grid_propagate(False)

        # Settings
        tk.Label(panel, text='Settings', font=('', 14, 'bold'), bg=COLORS['background_panel']).pack(anchor='w', pady=(0, 4))
        tk.Label(panel, text='Heuristic:', font=('', 11), bg=COLORS['background_panel']).pack(anchor='w')
        self.combobox_heuristic = ttk.Combobox(panel, state='readonly', width=30, font=('', 11),
            values=['Euclidean', 'Manhattan', 'Octile', 'Chebyshev', 'Dijkstra (h=0)'])
        self.combobox_heuristic.set('Euclidean')
        self.combobox_heuristic.pack(anchor='w', pady=(0, 8))

        self.allow_diagonal = tk.BooleanVar(value=True)
        self.dont_cross_corners = tk.BooleanVar()
        self.diagonal_cost_one = tk.BooleanVar()

        self.checkbutton_allow_diagonal = tk.Checkbutton(panel, text='Allow Diagonal', variable=self.allow_diagonal,
                       font=('', 11), bg=COLORS['background_panel'], command=self._update_ui_state)
        self.checkbutton_allow_diagonal.pack(anchor='w')
        
        self.checkbutton_dont_cross_corners = tk.Checkbutton(panel, text="Don't Cross Corners",
                       variable=self.dont_cross_corners, font=('', 11), bg=COLORS['background_panel'])
        self.checkbutton_dont_cross_corners.pack(anchor='w', padx=(20, 0))
        
        self.checkbutton_diagonal_cost_one = tk.Checkbutton(panel, text='Diagonal Cost = 1',
                       variable=self.diagonal_cost_one, font=('', 11), bg=COLORS['background_panel'])
        self.checkbutton_diagonal_cost_one.pack(anchor='w', padx=(20, 0))

        tk.Label(panel, text='Speed:', font=('', 11), bg=COLORS['background_panel']).pack(anchor='w', pady=(10, 0))
        self.slider_speed = tk.Scale(panel, from_=1, to=100, orient='horizontal',
                                     bg=COLORS['background_panel'], highlightthickness=0, length=280)
        self.slider_speed.set(DEFAULT_SPEED)
        self.slider_speed.pack(anchor='w', pady=(0, 0))

        # Controls
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=12)
        tk.Label(panel, text='Controls', font=('', 14, 'bold'), bg=COLORS['background_panel']).pack(anchor='w', pady=(0, 6))
        
        button_frame = tk.Frame(panel, bg=COLORS['background_panel'])
        button_frame.pack(fill='x')

        self.button_start_pause = tk.Button(button_frame, text='Start', width=14, bg=COLORS['button_start'],
                                         fg=COLORS['button_foreground'], font=('', 10, 'bold'), relief='flat',
                                         pady=4, command=self._toggle_execution)
        self.button_start_pause.grid(row=0, column=0, padx=3, pady=3)
        
        tk.Button(button_frame, text='Next Step', width=14, bg=COLORS['button_step'], fg=COLORS['button_foreground'],
                  font=('', 10, 'bold'), relief='flat', pady=4, command=self._step_execution).grid(row=0, column=1, padx=3, pady=3)
                  
        tk.Button(button_frame, text='Clear Path', width=14, bg=COLORS['button_clear_path'], fg=COLORS['button_foreground'],
                  font=('', 10, 'bold'), relief='flat', pady=4, command=self._clear_search_path).grid(row=1, column=0, padx=3, pady=3)
                  
        tk.Button(button_frame, text='Clear Walls', width=14, bg=COLORS['button_clear_walls'], fg=COLORS['button_foreground'],
                  font=('', 10, 'bold'), relief='flat', pady=4, command=self._clear_all_walls).grid(row=1, column=1, padx=3, pady=3)
                  
        tk.Button(button_frame, text='Random Walls', width=14, bg=COLORS['button_random'], fg=COLORS['button_foreground'],
                  font=('', 10, 'bold'), relief='flat', pady=4, command=self._generate_random_walls).grid(row=2, column=0, padx=3, pady=3)
                  
        tk.Button(button_frame, text='Random Maze', width=14, bg=COLORS['button_random'], fg=COLORS['button_foreground'],
                  font=('', 10, 'bold'), relief='flat', pady=4, command=self._generate_random_maze).grid(row=2, column=1, padx=3, pady=3)
                  
        tk.Button(button_frame, text='Compare All', width=30, bg=COLORS['button_compare'], fg=COLORS['button_foreground'],
                  font=('', 10, 'bold'), relief='flat', pady=4, command=self._compare_all_heuristics).grid(row=3, column=0, columnspan=2, padx=3, pady=3)

        # Statistics
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=12)
        tk.Label(panel, text='Statistics', font=('', 14, 'bold'), bg=COLORS['background_panel']).pack(anchor='w', pady=(0, 6))

        for label_text, key in [('Path Cost', 'path_cost'), ('Visited Nodes', 'visited_nodes'),
                                ('Execute Time', 'execution_time'), ('Operations', 'operations_count')]:
            stat_frame = tk.Frame(panel, bg=COLORS['background_panel'])
            stat_frame.pack(fill='x', pady=2)
            tk.Label(stat_frame, text=f'{label_text}:', font=('', 11), bg=COLORS['background_panel']).pack(side='left')
            tk.Label(stat_frame, textvariable=self.stats_vars[key], bg=COLORS['background_panel'], font=('', 11, 'bold')).pack(side='right')

    def _update_ui_state(self):
        state_value = 'normal' if self.allow_diagonal.get() else 'disabled'
        self.checkbutton_dont_cross_corners.config(state=state_value)
        self.checkbutton_diagonal_cost_one.config(state=state_value)

    def _draw_grid(self):
        self.rectangles = {}
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        for y in range(rows):
            for x in range(cols):
                x1, y1 = x * CELL_SIZE, y * CELL_SIZE
                color = COLORS['empty']
                if (x, y) == self.start_node:
                    color = COLORS["start"]
                elif (x, y) == self.end_node:
                    color = COLORS["end"]
                elif self.grid_data[y][x]:
                    color = COLORS["wall"]
                
                self.rectangles[(x, y)] = self.canvas.create_rectangle(
                    x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE,
                    fill=color, outline=COLORS['grid'], width=1)

    def _update_cell_color(self, x, y, cell_type):
        self.canvas.itemconfig(self.rectangles[(x, y)], fill=COLORS[cell_type])

    def _get_cell_at(self, event):
        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE
        if 0 <= y < GRID_ROWS and 0 <= x < GRID_COLUMNS:
            return (x, y)
        return None

    def _handle_mouse_press(self, event):
        position = self._get_cell_at(event)
        if not position or self.is_running:
            return
        if position == self.start_node and not self.is_visualized:
            self.dragged_node_type = 'start_node'
        elif position == self.end_node and not self.is_visualized:
            self.dragged_node_type = 'end_node'
        elif position != self.start_node and position != self.end_node and not self.is_visualized:
            x, y = position
            self.draw_mode = 'erase' if self.grid_data[y][x] else 'wall'
            self._paint_wall(position)

    def _handle_mouse_drag(self, event):
        position = self._get_cell_at(event)
        if not position or self.is_running:
            return
        if self.dragged_node_type:
            x, y = position
            if position != self.start_node and position != self.end_node and not self.grid_data[y][x]:
                old_position = getattr(self, self.dragged_node_type)
                self._update_cell_color(*old_position, 'empty')
                setattr(self, self.dragged_node_type, position)
                self._update_cell_color(*position, 'start' if self.dragged_node_type == 'start_node' else 'end')
        elif self.draw_mode:
            self._paint_wall(position)

    def _handle_mouse_release(self, event):
        self.dragged_node_type = None
        self.draw_mode = None

    def _paint_wall(self, position):
        x, y = position
        is_wall = (self.draw_mode == 'wall')
        if self.grid_data[y][x] != is_wall:
            self.grid_data[y][x] = is_wall
            self._update_cell_color(x, y, 'wall' if is_wall else 'empty')

    def _toggle_execution(self):
        if self.is_running:
            if self.is_step_mode:
                self.is_step_mode = self.is_paused = False
                self.button_start_pause.config(text='Pause', bg=COLORS['button_pause'])
            else:
                self.is_paused = not self.is_paused
                self.button_start_pause.config(text='Start' if self.is_paused else 'Pause',
                                         bg=COLORS['button_start'] if self.is_paused else COLORS['button_pause'])
        else:
            self._clear_search_path()
            result, frames = self._run_astar_algorithm()
            self.algorithm_result = result
            self.animation_frames = frames
            self._refresh_stats()
            self.is_running = True
            self.is_paused = self.is_step_mode = False
            self.button_start_pause.config(text='Pause', bg=COLORS['button_pause'])
            self.after(DELAY_START, self._playback_visualization)

    def _step_execution(self):
        if not self.is_running:
            self._clear_search_path()
            result, frames = self._run_astar_algorithm()
            self.algorithm_result = result
            self.animation_frames = frames
            self._refresh_stats()
            self.is_running = True
            self.is_paused = False
            self.is_step_mode = True
            self.button_start_pause.config(text='Start', bg=COLORS['button_start'])
            self.after(DELAY_START, self._playback_visualization)
        else:
            self.is_step_mode = True
            self.is_paused = False
            self.has_step_event = True
            self.button_start_pause.config(text='Start', bg=COLORS['button_start'])

    def _clear_search_path(self):
        self.is_running = self.is_visualized = False
        self.animation_frames = []
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        for y in range(rows):
            for x in range(cols):
                if (x, y) not in (self.start_node, self.end_node) and not self.grid_data[y][x]:
                    self._update_cell_color(x, y, 'empty')
        for var in self.stats_vars.values():
            var.set("-")

    def _clear_all_walls(self):
        self.grid_data = [[0] * GRID_COLUMNS for _ in range(GRID_ROWS)]
        self._clear_search_path()
        for (x, y), rect_id in self.rectangles.items():
            color = 'empty'
            if (x, y) == self.start_node:
                color = "start"
            elif (x, y) == self.end_node:
                color = "end"
            self.canvas.itemconfig(rect_id, fill=COLORS[color])

    def _generate_random_walls(self):
        self._clear_all_walls()
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        for y in range(rows):
            for x in range(cols):
                if (x, y) not in (self.start_node, self.end_node) and random.random() < WALL_PROBABILITY:
                    self.grid_data[y][x] = 1
                    self._update_cell_color(x, y, 'wall')

    def _generate_random_maze(self):
        # Sử dụng thuật toán Recursive Backtracking (DFS) để tạo mê cung dạng cây
        self._clear_all_walls()
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        for y in range(1, rows - 1):
            for x in range(1, cols - 1):
                self.grid_data[y][x] = 1
                self._update_cell_color(x, y, 'wall')

        stack = [(1, 1)]
        self.grid_data[1][1] = 0
        self._update_cell_color(1, 1, 'empty')

        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy in [(0, -2), (2, 0), (0, 2), (-2, 0)]:
                nx, ny = cx + dx, cy + dy
                if 1 <= nx < GRID_COLUMNS - 1 and 1 <= ny < GRID_ROWS - 1 and self.grid_data[ny][nx]:
                    neighbors.append((nx, ny))
            
            if neighbors:
                nx, ny = random.choice(neighbors)
                self.grid_data[ny][nx] = 0
                self.grid_data[cy + (ny - cy) // 2][cx + (nx - cx) // 2] = 0
                self._update_cell_color(nx, ny, 'empty')
                self._update_cell_color(cx + (nx - cx) // 2, cy + (ny - cy) // 2, 'empty')
                stack.append((nx, ny))
            else:
                stack.pop()

    def _calculate_heuristic(self, node_a, node_b, name=None):
        dx, dy = abs(node_a[0] - node_b[0]), abs(node_a[1] - node_b[1])
        name = name or self.combobox_heuristic.get()
        if name == "Manhattan":
            return dx + dy
        if name == "Euclidean":
            return math.hypot(dx, dy)
        if name == "Octile":
            return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        if name == "Chebyshev":
            return max(dx, dy)
        return 0.0

    def _get_neighbors(self, position):
        x, y = position
        allow_diagonal = self.allow_diagonal.get()
        no_cross_corners = self.dont_cross_corners.get()
        diagonal_cost = 1.0 if self.diagonal_cost_one.get() else math.sqrt(2)
        neighbors_list = []
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and not self.grid_data[ny][nx]:
                neighbors_list.append(((nx, ny), 1.0))
        
        if allow_diagonal:
            for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < cols and 0 <= ny < rows and not self.grid_data[ny][nx]:
                    wall_ortho_1 = self.grid_data[y + dy][x]
                    wall_ortho_2 = self.grid_data[y][x + dx]
                    if no_cross_corners:
                        if wall_ortho_1 or wall_ortho_2:
                            continue
                    elif wall_ortho_1 and wall_ortho_2:
                        continue
                    neighbors_list.append(((nx, ny), diagonal_cost))
        return neighbors_list

    def _run_astar_algorithm(self, heuristic_name=None):
        start, end = self.start_node, self.end_node
        g_scores = {start: 0.0}
        came_from = {start: None}
        # tie_break_counter giúp ưu tiên ô tìm thấy trước (FIFO) khi bằng điểm F
        tie_break_counter, operations_count = 0, 1
        open_set = [(self._calculate_heuristic(start, end, heuristic_name), tie_break_counter, start)]
        closed_set = set()
        animation_frames = []
        start_time = time.perf_counter()

        while open_set:
            _, _, current = heapq.heappop(open_set)
            if current in closed_set:
                continue
            
            operations_count += 1
            closed_set.add(current)
            if current not in (start, end):
                animation_frames.append(("closed", current))

            if current == end:
                path = []
                cursor = end
                while cursor:
                    path.append(cursor)
                    cursor = came_from[cursor]
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    'path_cost': f'{g_scores[end]:.2f}', 'visited_nodes': len(closed_set),
                    'execution_time': f'{elapsed_ms:.2f}', 'operations_count': operations_count, 
                    'path': path
                }, animation_frames

            for neighbor, move_cost in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue
                new_g = g_scores[current] + move_cost
                if neighbor not in g_scores or new_g < g_scores[neighbor]:
                    if neighbor not in g_scores:
                        operations_count += 1
                        if neighbor != end:
                            animation_frames.append(("open", neighbor))
                    g_scores[neighbor] = new_g
                    came_from[neighbor] = current
                    tie_break_counter += 1
                    priority = new_g + self._calculate_heuristic(neighbor, end, heuristic_name)
                    heapq.heappush(open_set, (priority, tie_break_counter, neighbor))

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return {
            'path_cost': '-', 'visited_nodes': len(closed_set),
            'execution_time': f'{elapsed_ms:.2f}', 'operations_count': operations_count, 
            'path': None
        }, animation_frames

    def _refresh_stats(self):
        res = self.algorithm_result
        self.stats_vars['path_cost'].set(res['path_cost'])
        self.stats_vars['visited_nodes'].set(str(res['visited_nodes']))
        self.stats_vars['execution_time'].set(f"{res['execution_time']} ms")
        self.stats_vars['operations_count'].set(str(res['operations_count']))

    def _playback_visualization(self, index=0):
        if not self.is_running:
            return
        if self.is_paused and not self.is_step_mode:
            self.after(DELAY_PAUSE, self._playback_visualization, index)
            return
        if self.is_step_mode and not self.has_step_event and index > 0:
            self.after(DELAY_PAUSE, self._playback_visualization, index)
            return

        self.has_step_event = False
        if index < len(self.animation_frames):
            cell_type, position = self.animation_frames[index]
            self._update_cell_color(*position, cell_type)
            # Tốc độ hiển thị tỷ lệ nghịch với độ trễ (Delay)
            delay_ms = max(1, MAX_SPEED_DELAY - self.slider_speed.get())
            self.after(delay_ms, self._playback_visualization, index + 1)
        else:
            if self.algorithm_result and self.algorithm_result['path']:
                for path_node in self.algorithm_result['path']:
                    if path_node not in (self.start_node, self.end_node):
                        self._update_cell_color(*path_node, "path")
            self.is_running, self.is_visualized = False, True
            self.button_start_pause.config(text='Start', bg=COLORS['button_start'])

    def _compare_all_heuristics(self):
        heuristics = ['Euclidean', 'Manhattan', 'Octile', 'Chebyshev', 'Dijkstra (h=0)']
        results = []
        for h in heuristics:
            result, _ = self._run_astar_algorithm(heuristic_name=h)
            result['heuristic'] = h
            results.append(result)

        window = tk.Toplevel(self)
        window.title('Heuristic Comparison')
        window.resizable(False, False)

        headers = ['Heuristic', 'Path Cost', 'Visited Nodes', 'Execution Time (ms)', 'Operations']
        keys = ['heuristic', 'path_cost', 'visited_nodes', 'execution_time', 'operations_count']

        for column_index, header_text in enumerate(headers):
            tk.Label(window, text=header_text, font=('', 11, 'bold'), bg=COLORS['header'],
                     relief='ridge', padx=10, pady=6).grid(row=0, column=column_index, sticky='nsew')

        for row_index, result in enumerate(results):
            background_color = COLORS['row'] if result['path_cost'] != '-' else COLORS['error']
            for column_index, key in enumerate(keys):
                tk.Label(window, text=str(result[key]), bg=background_color, font=('', 11),
                         relief='ridge', padx=10, pady=5).grid(row=row_index+1, column=column_index, sticky='nsew')
        for column_index in range(len(headers)):
            window.columnconfigure(column_index, weight=1)
        
        window.update_idletasks()
        self.tk.call('tk::PlaceWindow', window, 'center')

if __name__ == '__main__':
    App().mainloop()