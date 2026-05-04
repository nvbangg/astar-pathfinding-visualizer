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
DEFAULT_END_POS = (GRID_ROWS - 3, GRID_COLUMNS - 3)
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
        self.geometry("1450x650")

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
        self.canvas.delete('all')
        self.rectangles = {}
        rows_count, columns_count = len(self.grid_data), len(self.grid_data[0])
        for row_index in range(rows_count):
            for column_index in range(columns_count):
                x1, y1 = column_index * CELL_SIZE, row_index * CELL_SIZE
                position = (row_index, column_index)
                if position == self.start_node:
                    color = COLORS["start"]
                elif position == self.end_node:
                    color = COLORS["end"]
                elif self.grid_data[row_index][column_index]:
                    color = COLORS["wall"]
                else:
                    color = COLORS["empty"]
                self.rectangles[position] = self.canvas.create_rectangle(
                    x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE,
                    fill=color, outline=COLORS['grid'], width=1)

    def _update_cell_color(self, row_index, column_index, cell_type):
        self.canvas.itemconfig(self.rectangles[(row_index, column_index)], fill=COLORS[cell_type])

    def _get_cell_at(self, event):
        column_index, row_index = event.x // CELL_SIZE, event.y // CELL_SIZE
        if 0 <= row_index < len(self.grid_data) and 0 <= column_index < len(self.grid_data[0]):
            return (row_index, column_index)
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
            self.draw_mode = 'erase' if self.grid_data[position[0]][position[1]] else 'wall'
            self._paint_wall(position)

    def _handle_mouse_drag(self, event):
        position = self._get_cell_at(event)
        if not position or self.is_running:
            return
        if self.dragged_node_type:
            if position != self.start_node and position != self.end_node and not self.grid_data[position[0]][position[1]]:
                old_position = getattr(self, self.dragged_node_type)
                self._update_cell_color(*old_position, 'empty')
                setattr(self, self.dragged_node_type, position)
                self._update_cell_color(*position, 'start' if self.dragged_node_type == 'start_node' else 'end')
        elif self.draw_mode:
            self._paint_wall(position)

    def _handle_mouse_release(self, event):
        self.dragged_node_type = self.draw_mode = None

    def _paint_wall(self, position):
        if position in (self.start_node, self.end_node):
            return
        row_index, column_index = position
        is_wall = (self.draw_mode == 'wall')
        self.grid_data[row_index][column_index] = 1 if is_wall else 0
        self._update_cell_color(row_index, column_index, 'wall' if is_wall else 'empty')

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
        self.is_running = self.is_paused = self.is_step_mode = self.is_visualized = False
        self.animation_frames, self.algorithm_result = [], None
        self.button_start_pause.config(text='Start', bg=COLORS['button_start'])
        rows_count, columns_count = len(self.grid_data), len(self.grid_data[0])
        for row_index in range(rows_count):
            for column_index in range(columns_count):
                pos = (row_index, column_index)
                if pos == self.start_node:
                    self._update_cell_color(row_index, column_index, "start")
                elif pos == self.end_node:
                    self._update_cell_color(row_index, column_index, "end")
                elif self.grid_data[row_index][column_index]:
                    self._update_cell_color(row_index, column_index, "wall")
                else:
                    self._update_cell_color(row_index, column_index, "empty")
        for var in self.stats_vars.values():
            var.set("-")

    def _clear_all_walls(self):
        self._clear_search_path()
        rows_count, columns_count = len(self.grid_data), len(self.grid_data[0])
        self.grid_data = [[0] * columns_count for _ in range(rows_count)]
        self._draw_grid()

    def _generate_random_walls(self):
        self._clear_all_walls()
        for row_index in range(len(self.grid_data)):
            for column_index in range(len(self.grid_data[0])):
                if (row_index, column_index) not in (self.start_node, self.end_node) and random.random() < WALL_PROBABILITY:
                    self.grid_data[row_index][column_index] = 1
                    self._update_cell_color(row_index, column_index, 'wall')

    def _generate_random_maze(self):
        # Sử dụng thuật toán Recursive Backtracking (DFS) để tạo mê cung dạng cây
        self._clear_all_walls()
        rows_count, columns_count = len(self.grid_data), len(self.grid_data[0])
        for row_index in range(1, rows_count - 1):
            for column_index in range(1, columns_count - 1):
                self.grid_data[row_index][column_index] = 1
        
        stack = [DEFAULT_START_POS]
        self.grid_data[DEFAULT_START_POS[0]][DEFAULT_START_POS[1]] = 0
        while stack:
            curr_row, curr_col = stack[-1]
            neighbors = []
            for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                neighbor_row, neighbor_col = curr_row + dr, curr_col + dc
                if 1 < neighbor_row < rows_count - 2 and 1 < neighbor_col < columns_count - 2 and self.grid_data[neighbor_row][neighbor_col]:
                    neighbors.append((neighbor_row, neighbor_col, curr_row + dr // 2, curr_col + dc // 2))
            if neighbors:
                neighbor_row, neighbor_col, wall_row, wall_col = random.choice(neighbors)
                self.grid_data[wall_row][wall_col] = self.grid_data[neighbor_row][neighbor_col] = 0
                stack.append((neighbor_row, neighbor_col))
            else:
                stack.pop()
        self._draw_grid()

    def _calculate_heuristic(self, node_a, node_b, name=None):
        delta_row, delta_col = abs(node_a[0] - node_b[0]), abs(node_a[1] - node_b[1])
        name = name or self.combobox_heuristic.get()
        if name == "Manhattan":
            return delta_row + delta_col
        if name == "Euclidean":
            return math.hypot(delta_row, delta_col)
        if name == "Octile":
            return max(delta_row, delta_col) + (math.sqrt(2) - 1) * min(delta_row, delta_col)
        if name == "Chebyshev":
            return max(delta_row, delta_col)
        return 0.0

    def _get_neighbors(self, position):
        row_index, column_index = position
        allow_diagonal = self.allow_diagonal.get()
        no_cross_corners = self.dont_cross_corners.get()
        diagonal_cost = 1.0 if self.diagonal_cost_one.get() else math.sqrt(2)
        neighbors_list = []
        rows_count, columns_count = len(self.grid_data), len(self.grid_data[0])
        
        for delta_row, delta_col in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            neighbor_row, neighbor_col = row_index + delta_row, column_index + delta_col
            if 0 <= neighbor_row < rows_count and 0 <= neighbor_col < columns_count and not self.grid_data[neighbor_row][neighbor_col]:
                neighbors_list.append(((neighbor_row, neighbor_col), 1.0))
        
        if allow_diagonal:
            for delta_row, delta_col in [(-1, -1), (-1, 1), (1, 1), (1, -1)]:
                neighbor_row, neighbor_col = row_index + delta_row, column_index + delta_col
                if 0 <= neighbor_row < rows_count and 0 <= neighbor_col < columns_count and not self.grid_data[neighbor_row][neighbor_col]:
                    wall_orthogonal_1 = self.grid_data[row_index + delta_row][column_index]
                    wall_orthogonal_2 = self.grid_data[row_index][column_index + delta_col]
                    if no_cross_corners:
                        if wall_orthogonal_1 or wall_orthogonal_2:
                            continue
                    elif wall_orthogonal_1 and wall_orthogonal_2:
                        continue
                            
                    neighbors_list.append(((neighbor_row, neighbor_col), diagonal_cost))
        return neighbors_list

    def _run_astar_algorithm(self, heuristic_name=None):
        start_node, end_node = self.start_node, self.end_node
        g_scores = {start_node: 0.0}
        came_from = {start_node: None}
        
        # tie_break_counter giúp ưu tiên ô tìm thấy trước (FIFO) khi bằng điểm F
        tie_break_counter, operations_count = 0, 1
        open_set = [(self._calculate_heuristic(start_node, end_node, heuristic_name), tie_break_counter, start_node)]
        closed_set = set()
        animation_frames = []
        start_time = time.perf_counter()

        while open_set:
            _, _, current_node = heapq.heappop(open_set)
            if current_node in closed_set:
                continue
            
            operations_count += 1
            closed_set.add(current_node)
            if current_node not in (start_node, end_node):
                animation_frames.append(("closed", current_node))

            if current_node == end_node:
                final_path = []
                node_cursor = end_node
                while node_cursor:
                    final_path.append(node_cursor)
                    node_cursor = came_from[node_cursor]
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                result = {
                    'path_cost': f'{g_scores[end_node]:.2f}', 
                    'visited_nodes': len(closed_set),
                    'execution_time': f'{elapsed_ms:.2f}', 
                    'operations_count': operations_count, 
                    'path': final_path
                }
                return result, animation_frames

            for neighbor_node, movement_cost in self._get_neighbors(current_node):
                if neighbor_node in closed_set:
                    continue
                new_g_score = g_scores[current_node] + movement_cost
                if neighbor_node not in g_scores or new_g_score < g_scores[neighbor_node]:
                    if neighbor_node not in g_scores:
                        operations_count += 1
                        if neighbor_node != end_node:
                            animation_frames.append(("open", neighbor_node))
                    g_scores[neighbor_node] = new_g_score
                    came_from[neighbor_node] = current_node
                    tie_break_counter += 1
                    priority = new_g_score + self._calculate_heuristic(neighbor_node, end_node, heuristic_name)
                    heapq.heappush(open_set, (priority, tie_break_counter, neighbor_node))

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result = {
            'path_cost': '-', 
            'visited_nodes': len(closed_set),
            'execution_time': f'{elapsed_ms:.2f}', 
            'operations_count': operations_count, 
            'path': None
        }
        return result, animation_frames

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