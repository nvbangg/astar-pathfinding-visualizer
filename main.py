import tkinter as tk
from tkinter import ttk
import heapq
import random
import time
import math

CELL_SIZE = 25
COLUMNS, ROWS = 45, 25
DEFAULT_SPEED = 95
DEFAULT_START = (2, 2)
DEFAULT_END = (ROWS - 3, COLUMNS - 3)
MAZE_WALL_PROBABILITY = 0.2

DELAY_START = 10
DELAY_PAUSE = 50
MAX_SPEED_DELAY = 101

FONTS = {
    'main':  ('Segoe UI', 9),
    'bold':  ('Segoe UI', 9, 'bold'),
    'title': ('Segoe UI', 12, 'bold'),
}

COLORS = {
    'empty': '#FFFFFF', 'wall': '#555555',
    'start': '#2E7D32', 'end': '#D32F2F',
    'open': '#74D377',  'closed': '#A5D6A7',
    'path': '#FFD600',  'grid': '#E0E0E0',
    'bg_main': '#FAFAFA', 'bg_panel': '#F5F5F5',
    'button_fg': 'white',
    'btn_start': '#4CAF50', 'btn_pause': '#FFC107',
    'btn_step': '#607D8B',  'btn_clear_path': '#FF9800',
    'btn_clear_walls': '#E53935', 'btn_random': '#795548',
    'btn_compare': '#3F51B5',
    'header': '#E0E0E0', 'row': '#F9FBE7', 'error': '#FFEBEE',
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("A* Pathfinding Visualizer")
        self.state('zoomed')

        self.grid_data = [[0] * COLUMNS for _ in range(ROWS)]
        self.start_node = DEFAULT_START
        self.end_node = DEFAULT_END
        self.is_running = False
        self.is_paused = False
        self.is_step_mode = False
        self.has_step_event = False
        self.dragged_node = None
        self.draw_mode = None
        self.is_visualized = False

        self.frames = []
        self.search_result = None

        self.stats_vars = {key: tk.StringVar(value='-') for key in
                           ('cost', 'visited', 'time', 'operations')}

        self._build_ui()
        self._draw_grid()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=COLORS['bg_main'], highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.bind('<Button-1>', self._handle_mouse_press)
        self.canvas.bind('<B1-Motion>', self._handle_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self._handle_mouse_release)

        panel = tk.Frame(self, width=260, bg=COLORS['bg_panel'], padx=12, pady=10)
        panel.grid(row=0, column=1, sticky='ns')
        panel.grid_propagate(False)

        # Settings
        tk.Label(panel, text='Settings', font=FONTS['title'], bg=COLORS['bg_panel']).pack(anchor='w', pady=(0, 6))
        tk.Label(panel, text='Heuristic:', bg=COLORS['bg_panel'], font=FONTS['main']).pack(anchor='w')
        self.heuristic_combo = ttk.Combobox(panel, state='readonly', width=22,
            values=['Euclidean', 'Manhattan', 'Octile', 'Chebyshev', 'Dijkstra (h=0)'])
        self.heuristic_combo.set('Euclidean')
        self.heuristic_combo.pack(anchor='w', pady=(0, 6))

        self.allow_diagonal = tk.BooleanVar(value=True)
        self.dont_cross_corners = tk.BooleanVar()
        self.diagonal_cost_one = tk.BooleanVar()

        tk.Checkbutton(panel, text='Allow Diagonal', variable=self.allow_diagonal,
                       bg=COLORS['bg_panel'], font=FONTS['main'],
                       command=self._update_ui_state).pack(anchor='w')
        self.check_corners = tk.Checkbutton(panel, text="Don't Cross Corners",
                       variable=self.dont_cross_corners, bg=COLORS['bg_panel'], font=FONTS['main'])
        self.check_corners.pack(anchor='w', padx=(16, 0))
        self.check_diag_cost = tk.Checkbutton(panel, text='Diagonal Cost = 1',
                       variable=self.diagonal_cost_one, bg=COLORS['bg_panel'], font=FONTS['main'])
        self.check_diag_cost.pack(anchor='w', padx=(16, 0))

        tk.Label(panel, text='Speed:', bg=COLORS['bg_panel'], font=FONTS['main']).pack(anchor='w', pady=(8, 0))
        self.speed_slider = tk.Scale(panel, from_=1, to=100, orient='horizontal',
                                     bg=COLORS['bg_panel'], highlightthickness=0, length=220)
        self.speed_slider.set(DEFAULT_SPEED)
        self.speed_slider.pack(anchor='w')

        # Controls
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=8)
        tk.Label(panel, text='Controls', font=FONTS['title'], bg=COLORS['bg_panel']).pack(anchor='w', pady=(0, 6))
        
        button_frame = tk.Frame(panel, bg=COLORS['bg_panel'])
        button_frame.pack(fill='x')

        self.start_button = tk.Button(button_frame, text='Start', width=12, bg=COLORS['btn_start'],
                                      fg=COLORS['button_fg'], font=FONTS['bold'], relief='flat',
                                      command=self._toggle_execution)
        self.start_button.grid(row=0, column=0, padx=2, pady=2)
        tk.Button(button_frame, text='Next Step', width=12, bg=COLORS['btn_step'], fg=COLORS['button_fg'],
                  font=FONTS['main'], relief='flat', command=self._step_execution).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(button_frame, text='Clear Path', width=12, bg=COLORS['btn_clear_path'], fg=COLORS['button_fg'],
                  font=FONTS['main'], relief='flat', command=self._clear_search_path).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(button_frame, text='Clear Walls', width=12, bg=COLORS['btn_clear_walls'], fg=COLORS['button_fg'],
                  font=FONTS['main'], relief='flat', command=self._clear_all_walls).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(button_frame, text='Random Walls', width=12, bg=COLORS['btn_random'], fg=COLORS['button_fg'],
                  font=FONTS['main'], relief='flat', command=self._generate_random_walls).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(button_frame, text='Random Maze', width=12, bg=COLORS['btn_random'], fg=COLORS['button_fg'],
                  font=FONTS['main'], relief='flat', command=self._generate_random_maze).grid(row=2, column=1, padx=2, pady=2)
        tk.Button(button_frame, text='Compare All', width=26, bg=COLORS['btn_compare'], fg=COLORS['button_fg'],
                  font=FONTS['bold'], relief='flat', command=self._compare_all_heuristics).grid(row=3, column=0, columnspan=2, padx=2, pady=2)

        # Statistics
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=8)
        tk.Label(panel, text='Statistics', font=FONTS['title'], bg=COLORS['bg_panel']).pack(anchor='w', pady=(0, 6))

        for label_text, key in [('Path Cost', 'cost'), ('Visited Nodes', 'visited'),
                                ('Execute Time', 'time'), ('Operations', 'operations')]:
            stat_frame = tk.Frame(panel, bg=COLORS['bg_panel'])
            stat_frame.pack(fill='x', pady=1)
            tk.Label(stat_frame, text=f'{label_text}:', bg=COLORS['bg_panel'], font=FONTS['main']).pack(side='left')
            tk.Label(stat_frame, textvariable=self.stats_vars[key], bg=COLORS['bg_panel'], font=FONTS['bold']).pack(side='right')

    def _update_ui_state(self):
        state = 'normal' if self.allow_diagonal.get() else 'disabled'
        self.check_corners.config(state=state)
        self.check_diag_cost.config(state=state)

    def _draw_grid(self):
        self.canvas.delete('all')
        self.rectangles = {}
        rows, columns = len(self.grid_data), len(self.grid_data[0])
        for row in range(rows):
            for col in range(columns):
                x1, y1 = col * CELL_SIZE, row * CELL_SIZE
                position = (row, col)
                if position == self.start_node:
                    color = COLORS["start"]
                elif position == self.end_node:
                    color = COLORS["end"]
                elif self.grid_data[row][col]:
                    color = COLORS["wall"]
                else:
                    color = COLORS["empty"]
                self.rectangles[position] = self.canvas.create_rectangle(
                    x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE,
                    fill=color, outline=COLORS['grid'], width=1)

    def _update_cell_color(self, row, column, cell_type):
        self.canvas.itemconfig(self.rectangles[(row, column)], fill=COLORS[cell_type])

    def _get_cell_at(self, event):
        column, row = event.x // CELL_SIZE, event.y // CELL_SIZE
        if 0 <= row < len(self.grid_data) and 0 <= column < len(self.grid_data[0]):
            return (row, column)
        return None

    def _handle_mouse_press(self, event):
        position = self._get_cell_at(event)
        if not position or self.is_running:
            return
        if position == self.start_node and not self.is_visualized:
            self.dragged_node = 'start_node'
        elif position == self.end_node and not self.is_visualized:
            self.dragged_node = 'end_node'
        elif position != self.start_node and position != self.end_node and not self.is_visualized:
            self.draw_mode = 'erase' if self.grid_data[position[0]][position[1]] else 'wall'
            self._paint_wall(position)

    def _handle_mouse_drag(self, event):
        position = self._get_cell_at(event)
        if not position or self.is_running:
            return
        if self.dragged_node:
            if position != self.start_node and position != self.end_node and not self.grid_data[position[0]][position[1]]:
                old_position = getattr(self, self.dragged_node)
                self._update_cell_color(*old_position, 'empty')
                setattr(self, self.dragged_node, position)
                self._update_cell_color(*position, 'start' if self.dragged_node == 'start_node' else 'end')
        elif self.draw_mode:
            self._paint_wall(position)

    def _handle_mouse_release(self, event):
        self.dragged_node = self.draw_mode = None

    def _paint_wall(self, position):
        if position in (self.start_node, self.end_node):
            return
        row, column = position
        is_wall = (self.draw_mode == 'wall')
        self.grid_data[row][column] = 1 if is_wall else 0
        self._update_cell_color(row, column, 'wall' if is_wall else 'empty')

    def _toggle_execution(self):
        if self.is_running:
            if self.is_step_mode:
                self.is_step_mode = self.is_paused = False
                self.start_button.config(text='Pause', bg=COLORS['btn_pause'])
            else:
                self.is_paused = not self.is_paused
                self.start_button.config(text='Start' if self.is_paused else 'Pause',
                                         bg=COLORS['btn_start'] if self.is_paused else COLORS['btn_pause'])
        else:
            self._clear_search_path()
            self._run_astar_algorithm()
            self.is_running = True
            self.is_paused = self.is_step_mode = False
            self.start_button.config(text='Pause', bg=COLORS['btn_pause'])
            self.after(DELAY_START, self._playback_visualization)

    def _step_execution(self):
        if not self.is_running:
            self._clear_search_path()
            self._run_astar_algorithm()
            self.is_running = True
            self.is_paused = False
            self.is_step_mode = True
            self.start_button.config(text='Start', bg=COLORS['btn_start'])
            self.after(DELAY_START, self._playback_visualization)
        else:
            self.is_step_mode = True
            self.is_paused = False
            self.has_step_event = True
            self.start_button.config(text='Start', bg=COLORS['btn_start'])

    def _clear_search_path(self):
        self.is_running = self.is_paused = self.is_step_mode = self.is_visualized = False
        self.frames, self.search_result = [], None
        self.start_button.config(text='Start', bg=COLORS['btn_start'])
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        for r in range(rows):
            for c in range(cols):
                pos = (r, c)
                if pos == self.start_node:
                    self._update_cell_color(r, c, "start")
                elif pos == self.end_node:
                    self._update_cell_color(r, c, "end")
                elif self.grid_data[r][c]:
                    self._update_cell_color(r, c, "wall")
                else:
                    self._update_cell_color(r, c, "empty")
        for var in self.stats_vars.values():
            var.set("-")

    def _clear_all_walls(self):
        self._clear_search_path()
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        self.grid_data = [[0] * cols for _ in range(rows)]
        self._draw_grid()

    def _generate_random_walls(self):
        self._clear_all_walls()
        for r in range(len(self.grid_data)):
            for c in range(len(self.grid_data[0])):
                if (r, c) not in (self.start_node, self.end_node) and random.random() < MAZE_WALL_PROBABILITY:
                    self.grid_data[r][c] = 1
                    self._update_cell_color(r, c, 'wall')

    def _generate_random_maze(self):
        self._clear_all_walls()
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                self.grid_data[r][c] = 1
        
        stack = [DEFAULT_START]
        self.grid_data[DEFAULT_START[0]][DEFAULT_START[1]] = 0
        while stack:
            curr_r, curr_c = stack[-1]
            neighbors = []
            for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 1 < nr < rows - 2 and 1 < nc < cols - 2 and self.grid_data[nr][nc]:
                    neighbors.append((nr, nc, curr_r + dr // 2, curr_c + dc // 2))
            if neighbors:
                nr, nc, wr, wc = random.choice(neighbors)
                self.grid_data[wr][wc] = self.grid_data[nr][nc] = 0
                stack.append((nr, nc))
            else:
                stack.pop()
        self._draw_grid()

    def _calculate_heuristic(self, node_a, node_b, name=None):
        dr, dc = abs(node_a[0] - node_b[0]), abs(node_a[1] - node_b[1])
        name = name or self.heuristic_combo.get()
        if name == "Manhattan":
            return dr + dc
        if name == "Euclidean":
            return math.hypot(dr, dc)
        if name == "Octile":
            return max(dr, dc) + (math.sqrt(2) - 1) * min(dr, dc)
        if name == "Chebyshev":
            return max(dr, dc)
        return 0

    def _get_neighbors(self, position):
        row, col = position
        allow_diag = self.allow_diagonal.get()
        no_cross = self.dont_cross_corners.get()
        diag_cost = 1.0 if self.diagonal_cost_one.get() else math.sqrt(2)
        neighbors = []
        rows, cols = len(self.grid_data), len(self.grid_data[0])
        
        for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols and not self.grid_data[nr][nc]:
                neighbors.append(((nr, nc), 1.0))
        
        if allow_diag:
            for dr, dc in [(-1, -1), (-1, 1), (1, 1), (1, -1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < rows and 0 <= nc < cols and not self.grid_data[nr][nc]:
                    w1, w2 = self.grid_data[row + dr][col], self.grid_data[row][col + dc]
                    if (no_cross and (w1 or w2)) or (not no_cross and (w1 and w2)):
                        continue
                    neighbors.append(((nr, nc), diag_cost))
        return neighbors

    def _run_astar_algorithm(self, heuristic_name=None):
        start, end = self.start_node, self.end_node
        g_scores = {start: 0.0}
        came_from = {start: None}
        counter, operations = 0, 1
        open_set = [(self._calculate_heuristic(start, end, heuristic_name), counter, start)]
        closed_set = set()
        frames = []
        start_time = time.perf_counter()

        while open_set:
            _, _, current = heapq.heappop(open_set)
            if current in closed_set:
                continue
            
            operations += 1
            closed_set.add(current)
            if current not in (start, end):
                frames.append(("closed", current))

            if current == end:
                path = []
                node = end
                while node:
                    path.append(node)
                    node = came_from[node]
                elapsed = (time.perf_counter() - start_time) * 1000
                self.frames = frames
                self.search_result = {'cost': f'{g_scores[end]:.2f}', 'visited': len(closed_set),
                                     'time': f'{elapsed:.2f}', 'operations': operations, 'path': path}
                self._refresh_stats()
                return self.search_result

            for neighbor, cost in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue
                new_g = g_scores[current] + cost
                if neighbor not in g_scores or new_g < g_scores[neighbor]:
                    if neighbor not in g_scores:
                        operations += 1
                        if neighbor != end:
                            frames.append(("open", neighbor))
                    g_scores[neighbor] = new_g
                    came_from[neighbor] = current
                    counter += 1
                    priority = new_g + self._calculate_heuristic(neighbor, end, heuristic_name)
                    heapq.heappush(open_set, (priority, counter, neighbor))

        elapsed = (time.perf_counter() - start_time) * 1000
        self.frames = frames
        self.search_result = {'cost': '-', 'visited': len(closed_set),
                             'time': f'{elapsed:.2f}', 'operations': operations, 'path': None}
        self._refresh_stats()
        return self.search_result

    def _refresh_stats(self):
        res = self.search_result
        self.stats_vars['cost'].set(res['cost'])
        self.stats_vars['visited'].set(str(res['visited']))
        self.stats_vars['time'].set(f"{res['time']} ms")
        self.stats_vars['operations'].set(str(res['operations']))

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
        if index < len(self.frames):
            cell_type, pos = self.frames[index]
            self._update_cell_color(*pos, cell_type)
            delay = max(1, MAX_SPEED_DELAY - self.speed_slider.get())
            self.after(delay, self._playback_visualization, index + 1)
        else:
            if self.search_result and self.search_result['path']:
                for p in self.search_result['path']:
                    if p not in (self.start_node, self.end_node):
                        self._update_cell_color(*p, "path")
            self.is_running, self.is_visualized = False, True
            self.start_button.config(text='Start', bg=COLORS['btn_start'])

    def _compare_all_heuristics(self):
        if self.is_running:
            return
        heuristics = ['Euclidean', 'Manhattan', 'Octile', 'Chebyshev', 'Dijkstra (h=0)']
        results = []
        for h in heuristics:
            res = self._run_astar_algorithm(heuristic_name=h)
            res['heuristic'] = h
            results.append(res)

        window = tk.Toplevel(self)
        window.title('Compare All Heuristics')
        window.resizable(False, False)

        headers = ['Heuristic', 'Path Cost', 'Visited Nodes', 'Execute Time (ms)', 'Operations']
        keys = ['heuristic', 'cost', 'visited', 'time', 'operations']

        for column, text in enumerate(headers):
            tk.Label(window, text=text, font=FONTS['bold'], bg=COLORS['header'],
                     relief='ridge', padx=6, pady=4).grid(row=0, column=column, sticky='nsew')

        for row_idx, res in enumerate(results):
            bg = COLORS['row'] if res['cost'] != '-' else COLORS['error']
            for col_idx, key in enumerate(keys):
                tk.Label(window, text=str(res[key]), font=FONTS['main'], bg=bg,
                         relief='ridge', padx=6, pady=3).grid(row=row_idx+1, column=col_idx, sticky='nsew')
        for col in range(len(headers)):
            window.columnconfigure(col, weight=1)

if __name__ == '__main__':
    App().mainloop()