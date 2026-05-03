import tkinter as tk
from tkinter import ttk
import heapq
import random
import time
import math

CELL = 25
COLS, ROWS = 45, 25
DEFAULT_SPEED = 95
DEFAULT_START = (2, 2)
DEFAULT_END = (ROWS-3, COLS-3)
MAZE_WALL_PROB = 0.2

DELAY_START = 10    
DELAY_PAUSE = 50     
MAX_SPEED_DELAY = 101 # base ms for speed calculation

FONT = {
    'main':  ('Segoe UI', 9),
    'bold':  ('Segoe UI', 9, 'bold'),
    'title': ('Segoe UI', 12, 'bold'),
}

COLOR = {
    'empty': '#FFFFFF', 'wall': '#555555',
    'start': '#2E7D32', 'end': '#D32F2F',
    'open': '#74D377',  'closed': '#A5D6A7',
    'path': '#FFD600',  'grid': '#E0E0E0',
    'bg_main': '#FAFAFA', 'bg_panel': '#F5F5F5',
    'btn_fg': 'white',
    'btn_start': '#4CAF50', 'btn_pause': '#FFC107',
    'btn_step': '#607D8B',  'btn_clear_path': '#FF9800',
    'btn_clear_walls': '#E53935', 'btn_random': '#795548',
    'btn_compare': '#3F51B5',
    'compare_header': '#E0E0E0',
    'compare_row': '#F9FBE7',
    'compare_err': '#FFEBEE',
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("A* Pathfinding Visualizer")
        self.state('zoomed')

        self.grid_data = [[0]*COLS for _ in range(ROWS)]
        self.start = DEFAULT_START
        self.end = DEFAULT_END
        self.running = False
        self.paused = False
        self.step_mode = False
        self.step_event = False
        self.drag_node = None
        self.draw_mode = None
        self.visualized = False

        self.stats = {k: tk.StringVar(value='-') for k in
                      ('cost','visited','max_open','time','ops')}

        self._build_ui()
        self._draw_grid()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=COLOR['bg_main'], highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.bind('<Button-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)

        panel = tk.Frame(self, width=260, bg=COLOR['bg_panel'], padx=12, pady=10)
        panel.grid(row=0, column=1, sticky='ns')
        panel.grid_propagate(False)

        # Settings
        tk.Label(panel, text='Settings', font=FONT['title'],
                 bg=COLOR['bg_panel']).pack(anchor='w', pady=(0,6))

        tk.Label(panel, text='Heuristic:', bg=COLOR['bg_panel'],
                 font=FONT['main']).pack(anchor='w')
        self.heuristic = ttk.Combobox(panel, state='readonly', width=22,
            values=['Euclidean','Manhattan','Octile','Chebyshev','Dijkstra (h=0)'])
        self.heuristic.set('Euclidean')
        self.heuristic.pack(anchor='w', pady=(0,6))

        self.allow_diag = tk.BooleanVar(value=True)
        self.cross_corner = tk.BooleanVar()
        self.diag_cost1 = tk.BooleanVar()
        self.bidir = tk.BooleanVar()

        tk.Checkbutton(panel, text='Allow Diagonal', variable=self.allow_diag,
                       bg=COLOR['bg_panel'], font=FONT['main'],
                       command=self._toggle_diag).pack(anchor='w')
        self.cb_cross = tk.Checkbutton(panel, text="Don't Cross Corners",
                       variable=self.cross_corner, bg=COLOR['bg_panel'], font=FONT['main'])
        self.cb_cross.pack(anchor='w', padx=(16,0))
        self.cb_dcost = tk.Checkbutton(panel, text='Diagonal Cost = 1',
                       variable=self.diag_cost1, bg=COLOR['bg_panel'], font=FONT['main'])
        self.cb_dcost.pack(anchor='w', padx=(16,0))
        tk.Checkbutton(panel, text='Bi-directional', variable=self.bidir,
                       bg=COLOR['bg_panel'], font=FONT['main']).pack(anchor='w')

        tk.Label(panel, text='Speed:', bg=COLOR['bg_panel'],
                 font=FONT['main']).pack(anchor='w', pady=(8,0))
        self.speed = tk.Scale(panel, from_=1, to=100, orient='horizontal',
                              bg=COLOR['bg_panel'], highlightthickness=0, length=220)
        self.speed.set(DEFAULT_SPEED)
        self.speed.pack(anchor='w')

        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=8)
        tk.Label(panel, text='Controls', font=FONT['title'],
                 bg=COLOR['bg_panel']).pack(anchor='w', pady=(0,6))

        bf = tk.Frame(panel, bg=COLOR['bg_panel'])
        bf.pack(fill='x')

        self.btn_start = tk.Button(bf, text='Start', width=12, bg=COLOR['btn_start'],
                                   fg=COLOR['btn_fg'], font=FONT['bold'],
                                   relief='flat', command=self._toggle_run)
        self.btn_start.grid(row=0, column=0, padx=2, pady=2)
        tk.Button(bf, text='Next Step', width=12, bg=COLOR['btn_step'], fg=COLOR['btn_fg'],
                  font=FONT['main'], relief='flat',
                  command=self._next_step).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(bf, text='Clear Path', width=12, bg=COLOR['btn_clear_path'], fg=COLOR['btn_fg'],
                  font=FONT['main'], relief='flat',
                  command=self._clear_path).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(bf, text='Clear Walls', width=12, bg=COLOR['btn_clear_walls'], fg=COLOR['btn_fg'],
                  font=FONT['main'], relief='flat',
                  command=self._clear_walls).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(bf, text='Random Walls', width=12, bg=COLOR['btn_random'], fg=COLOR['btn_fg'],
                  font=FONT['main'], relief='flat',
                  command=self._random_walls).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(bf, text='Random Maze', width=12, bg=COLOR['btn_random'], fg=COLOR['btn_fg'],
                  font=FONT['main'], relief='flat',
                  command=self._random_maze).grid(row=2, column=1, padx=2, pady=2)
        tk.Button(bf, text='Compare All', width=26, bg=COLOR['btn_compare'], fg=COLOR['btn_fg'],
                  font=FONT['bold'], relief='flat',
                  command=self._compare_all).grid(row=3, column=0, columnspan=2, padx=2, pady=2)

        # Statistics
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=8)
        tk.Label(panel, text='Statistics', font=FONT['title'],
                 bg=COLOR['bg_panel']).pack(anchor='w', pady=(0,6))

        labels = [('Path Cost','cost'),
                  ('Visited Nodes','visited'),('Max Open Nodes','max_open'),
                  ('Search Time','time'),('Operations','ops')]
        for text, key in labels:
            f = tk.Frame(panel, bg=COLOR['bg_panel'])
            f.pack(fill='x', pady=1)
            tk.Label(f, text=f'{text}:', bg=COLOR['bg_panel'],
                     font=FONT['main']).pack(side='left')
            tk.Label(f, textvariable=self.stats[key], bg=COLOR['bg_panel'],
                     font=FONT['bold']).pack(side='right')

    def _toggle_diag(self):
        st = 'normal' if self.allow_diag.get() else 'disabled'
        self.cb_cross.config(state=st)
        self.cb_dcost.config(state=st)

    def _draw_grid(self):
        c = self.canvas
        c.delete('all')
        self.rects = {}
        for r in range(ROWS):
            for col in range(COLS):
                x1, y1 = col*CELL, r*CELL
                pos = (r, col)
                if pos == self.start:
                    color = COLOR['start']
                elif pos == self.end:
                    color = COLOR['end']
                elif self.grid_data[r][col]:
                    color = COLOR['wall']
                else:
                    color = COLOR['empty']
                self.rects[pos] = c.create_rectangle(
                    x1, y1, x1+CELL, y1+CELL,
                    fill=color, outline=COLOR['grid'], width=1)

    def _set_cell(self, r, col, ctype):
        self.canvas.itemconfig(self.rects[(r, col)], fill=COLOR[ctype])

    # * ── Sự kiện chuột ─────
    def _cell_at(self, e):
        col, r = e.x // CELL, e.y // CELL
        if 0 <= r < ROWS and 0 <= col < COLS:
            return (r, col)
        return None

    def _on_press(self, e):
        pos = self._cell_at(e)
        if not pos or self.running:
            return
        # Cho kéo start/end khi chưa chạy (không có visualization)
        if pos == self.start and not self.visualized:
            self.drag_node = 'start'
        elif pos == self.end and not self.visualized:
            self.drag_node = 'end'
        elif pos != self.start and pos != self.end and not self.visualized:
            self.draw_mode = 'erase' if self.grid_data[pos[0]][pos[1]] else 'wall'
            self._paint_wall(pos)

    def _on_drag(self, e):
        pos = self._cell_at(e)
        if not pos or self.running:
            return
        if self.drag_node:
            if pos != self.start and pos != self.end and not self.grid_data[pos[0]][pos[1]]:
                old = getattr(self, self.drag_node)
                self._set_cell(*old, 'empty')
                setattr(self, self.drag_node, pos)
                self._set_cell(*pos, self.drag_node)
        elif self.draw_mode:
            self._paint_wall(pos)

    def _on_release(self, e):
        self.drag_node = None
        self.draw_mode = None

    def _paint_wall(self, pos):
        if pos == self.start or pos == self.end:
            return
        r, c = pos
        if self.draw_mode == 'wall':
            self.grid_data[r][c] = 1
            self._set_cell(r, c, 'wall')
        else:
            self.grid_data[r][c] = 0
            self._set_cell(r, c, 'empty')

    # * ── Controls ────
    def _toggle_run(self):
        if self.running:
            if self.step_mode:
                self.step_mode = False
                self.paused = False
                self.btn_start.config(text='Pause', bg=COLOR['btn_pause'])
            else:
                self.paused = not self.paused
                self.btn_start.config(text='Start' if self.paused else 'Pause',
                                      bg=COLOR['btn_start'] if self.paused else COLOR['btn_pause'])
        else:
            self._clear_path()
            self.running = True
            self.paused = False
            self.step_mode = False
            self.btn_start.config(text='Pause', bg=COLOR['btn_pause'])
            self.after(DELAY_START, self._run_algorithm)

    def _next_step(self):
        if not self.running:
            self._clear_path()
            self.running = True
            self.paused = False
            self.step_mode = True
            self.btn_start.config(text='Start', bg=COLOR['btn_start'])
            self.after(DELAY_START, self._run_algorithm)
        else:
            self.step_mode = True
            self.paused = False
            self.step_event = True
            self.btn_start.config(text='Start', bg=COLOR['btn_start'])

    def _clear_path(self):
        self.running = False
        self.paused = False
        self.step_mode = False
        self.visualized = False
        self.btn_start.config(text='Start', bg=COLOR['btn_start'])
        for r in range(ROWS):
            for c in range(COLS):
                if (r,c) == self.start:
                    self._set_cell(r, c, 'start')
                elif (r,c) == self.end:
                    self._set_cell(r, c, 'end')
                elif self.grid_data[r][c]:
                    self._set_cell(r, c, 'wall')
                else:
                    self._set_cell(r, c, 'empty')
        for v in self.stats.values():
            v.set('-')

    def _clear_walls(self):
        self._clear_path()
        self.grid_data = [[0]*COLS for _ in range(ROWS)]
        self._draw_grid()

    def _random_walls(self):
        self._clear_walls()
        for r in range(ROWS):
            for c in range(COLS):
                if (r,c) != self.start and (r,c) != self.end and random.random() < MAZE_WALL_PROB:
                    self.grid_data[r][c] = 1
                    self._set_cell(r, c, 'wall')

    def _random_maze(self):
        # Tạo mê cung bằng Recursive Backtracking
        self._clear_walls()
        self.grid_data = [[0]*COLS for _ in range(ROWS)]
        for r in range(1, ROWS-1):
            for c in range(1, COLS-1):
                self.grid_data[r][c] = 1

        sr, sc = DEFAULT_START
        self.start, self.end = DEFAULT_START, DEFAULT_END

        stack = [(sr, sc)]
        self.grid_data[sr][sc] = 0
        while stack:
            cr, cc = stack[-1]
            neighbors = []
            for dr, dc in [(-2,0),(2,0),(0,-2),(0,2)]:
                nr, nc = cr+dr, cc+dc
                if 1 < nr < ROWS-2 and 1 < nc < COLS-2 and self.grid_data[nr][nc]:
                    neighbors.append((nr, nc, cr+dr//2, cc+dc//2))
            if neighbors:
                nr, nc, wr, wc = random.choice(neighbors)
                self.grid_data[wr][wc] = 0
                self.grid_data[nr][nc] = 0
                stack.append((nr, nc))
            else:
                stack.pop()

        self._draw_grid()

    # * ── Heuristic và láng giềng ────
    def _h(self, a, b, hname=None):
        dr, dc = abs(a[0]-b[0]), abs(a[1]-b[1])
        name = hname or self.heuristic.get()
        if name == 'Manhattan':
            return dr + dc
        if name == 'Euclidean':
            return math.hypot(dr, dc)
        if name == 'Octile':
            return max(dr,dc) + (math.sqrt(2)-1)*min(dr,dc)
        if name == 'Chebyshev':
            return max(dr, dc)
        return 0  # Dijkstra

    def _neighbors(self, pos):
        r, c = pos
        diag = self.allow_diag.get()
        dont_cross = self.cross_corner.get()
        dcost = 1 if self.diag_cost1.get() else math.sqrt(2)
        result = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and not self.grid_data[nr][nc]:
                result.append(((nr,nc), 1))
        if diag:
            for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and not self.grid_data[nr][nc]:
                    w1, w2 = self.grid_data[r+dr][c], self.grid_data[r][c+dc]
                    if dont_cross:
                        # Tích vào Don't Cross: Không cho phép đi sát 1 góc tường
                        if w1 or w2:
                            continue
                    else:
                        # Bình thường (không tích): Cho phép sát 1 góc, chặn khi kẹp giữa 2 vật cản
                        if w1 and w2:
                            continue
                    result.append(((nr,nc), dcost))
        return result

    # * ── Thuật toán A* ─────
    def _run_algorithm(self):
        if self.bidir.get():
            self._run_bidir()
        else:
            self._run_astar()

    def _run_astar(self, hname=None, instant=False):
        start, end = self.start, self.end
        g = {start: 0}
        came_from = {start: None}
        counter = 0
        ops = 1
        open_set = [(self._h(start, end, hname), counter, start)]
        closed = set()
        max_open = 1
        t0 = time.perf_counter()

        def step():
            nonlocal counter, ops, max_open
            if not instant:
                if not self.running: return False
                if self.paused and not self.step_mode:
                    self.after(DELAY_PAUSE, step)
                    return False
                if self.step_mode and not self.step_event and counter > 0:
                    self.after(DELAY_PAUSE, step)
                    return False
                self.step_event = False

            while open_set:
                _, _, current = heapq.heappop(open_set)
                if current not in closed: break
            else:
                return self._finish(None, g, len(closed), max_open, t0, ops, instant)

            ops += 1
            closed.add(current)
            if not instant and current != start and current != end:
                self._set_cell(*current, 'closed')

            if current == end:
                path = []
                node = current
                while node:
                    path.append(node)
                    node = came_from[node]
                return self._finish(path, g, len(closed), max_open, t0, ops, instant)

            for neighbor, cost in self._neighbors(current):
                if neighbor in closed: continue
                new_g = g[current] + cost
                if neighbor not in g or new_g < g[neighbor]:
                    if neighbor not in g:
                        ops += 1
                    g[neighbor] = new_g
                    came_from[neighbor] = current
                    counter += 1
                    heapq.heappush(open_set, (new_g + self._h(neighbor, end, hname), counter, neighbor))
                    if not instant and neighbor != end:
                        self._set_cell(*neighbor, 'open')

            max_open = max(max_open, len(open_set))
            
            if instant: return None
            delay = max(1, MAX_SPEED_DELAY - self.speed.get())
            self.after(delay, step)

        if instant:
            while True:
                res = step()
                if res is not None: return res
        else:
            step()

    def _run_bidir(self, hname=None, instant=False):
        start, end = self.start, self.end
        g = {start: 0, end: 0}
        came_from = {start: None, end: None}
        opened_by = {start: 'start', end: 'end'}
        closed = set()
        counter = 0
        ops = 2
        open_forward = [(self._h(start, end, hname), counter, start)]; counter += 1
        open_backward = [(self._h(end, start, hname), counter, end)]; counter += 1
        max_open = 2
        t0 = time.perf_counter()

        def step():
            nonlocal counter, ops, max_open
            if not instant:
                if not self.running: return False
                if self.paused and not self.step_mode:
                    self.after(DELAY_PAUSE, step)
                    return False
                if self.step_mode and not self.step_event and counter > 2:
                    self.after(DELAY_PAUSE, step)
                    return False
                self.step_event = False

            if not open_forward or not open_backward:
                return self._finish_bidir(None, None, came_from, len(closed), max_open, t0, ops, instant)

            # --- FORWARD ---
            while open_forward:
                _, _, current = heapq.heappop(open_forward)
                if current not in closed: break
            else: current = None

            if current:
                ops += 1
                closed.add(current)
                if not instant and current != start and current != end:
                    self._set_cell(*current, 'closed')

                for neighbor, cost in self._neighbors(current):
                    if neighbor in closed: continue
                    if opened_by.get(neighbor) == 'end':
                        return self._finish_bidir(current, neighbor, came_from, len(closed), max_open, t0, ops, instant)

                    new_g = g[current] + cost
                    if opened_by.get(neighbor) != 'start' or new_g < g.get(neighbor, float('inf')):
                        if opened_by.get(neighbor) is None: ops += 1
                        g[neighbor] = new_g
                        came_from[neighbor] = current
                        counter += 1
                        heapq.heappush(open_forward, (new_g + self._h(neighbor, end, hname), counter, neighbor))
                        opened_by[neighbor] = 'start'
                        if not instant and neighbor != start and neighbor != end:
                            self._set_cell(*neighbor, 'open')

            # --- BACKWARD ---
            while open_backward:
                _, _, current_b = heapq.heappop(open_backward)
                if current_b not in closed: break
            else: current_b = None

            if current_b:
                ops += 1
                closed.add(current_b)
                if not instant and current_b != start and current_b != end:
                    self._set_cell(*current_b, 'closed')

                for neighbor, cost in self._neighbors(current_b):
                    if neighbor in closed: continue
                    if opened_by.get(neighbor) == 'start':
                        return self._finish_bidir(neighbor, current_b, came_from, len(closed), max_open, t0, ops, instant)

                    new_g = g[current_b] + cost
                    if opened_by.get(neighbor) != 'end' or new_g < g.get(neighbor, float('inf')):
                        if opened_by.get(neighbor) is None: ops += 1
                        g[neighbor] = new_g
                        came_from[neighbor] = current_b
                        counter += 1
                        heapq.heappush(open_backward, (new_g + self._h(neighbor, start, hname), counter, neighbor))
                        opened_by[neighbor] = 'end'
                        if not instant and neighbor != start and neighbor != end:
                            self._set_cell(*neighbor, 'open')

            max_open = max(max_open, len(open_forward) + len(open_backward))
            
            if instant: return None
            delay = max(1, MAX_SPEED_DELAY - self.speed.get())
            self.after(delay, step)

        if instant:
            while True:
                res = step()
                if res is not None: return res
        else:
            step()

    def _set_stats(self, cost, visited, max_open, elapsed, ops):
        self.stats['cost'].set(cost)
        self.stats['visited'].set(str(visited))
        self.stats['max_open'].set(str(max_open))
        self.stats['time'].set(f'{elapsed:.2f} ms')
        self.stats['ops'].set(str(ops))
        self.running = False
        self.visualized = True
        self.btn_start.config(text='Start', bg=COLOR['btn_start'])

    def _draw_path(self, path):
        for p in path:
            if p != self.start and p != self.end:
                self._set_cell(*p, 'path')

    def _finish(self, path, g, visited, max_open, t0, ops, instant=False):
        elapsed = (time.perf_counter() - t0) * 1000
        cost = '-' if path is None else f'{g[self.end]:.2f}'
        
        if instant:
            return {'cost': cost, 'visited': visited, 'max_open': max_open, 'time': f'{elapsed:.2f}', 'ops': ops}
            
        if path: self._draw_path(path)
        self._set_stats(cost, visited, max_open, elapsed, ops)

    def _build_bidir_path(self, touch_forward, touch_backward, came_from):
        path = []
        node = touch_forward
        while node:
            path.append(node)
            node = came_from.get(node)
        path.reverse()
        
        node = touch_backward
        while node:
            path.append(node)
            node = came_from.get(node)
            
        return path

    def _path_cost(self, path):
        return sum(
            math.hypot(path[i][0]-path[i+1][0], path[i][1]-path[i+1][1])
            if not self.diag_cost1.get() else
            max(abs(path[i][0]-path[i+1][0]), abs(path[i][1]-path[i+1][1]))
            for i in range(len(path)-1))

    def _finish_bidir(self, touch_forward, touch_backward, came_from, visited, max_open, t0, ops, instant=False):
        elapsed = (time.perf_counter() - t0) * 1000
        
        if touch_forward is None:
            if instant: return {'cost': '-', 'visited': visited, 'max_open': max_open, 'time': f'{elapsed:.2f}', 'ops': ops}
            self._set_stats('-', visited, max_open, elapsed, ops)
        else:
            path = self._build_bidir_path(touch_forward, touch_backward, came_from)
            cost = f'{self._path_cost(path):.2f}'
            if instant: return {'cost': cost, 'visited': visited, 'max_open': max_open, 'time': f'{elapsed:.2f}', 'ops': ops}
            self._draw_path(path)
            self._set_stats(cost, visited, max_open, elapsed, ops)

    # * ── Compare All ────
    def _compare_all(self):
        if self.running:
            return
        heuristics = ['Euclidean','Manhattan','Octile','Chebyshev','Dijkstra (h=0)']
        results = []
        is_bidir = self.bidir.get()
        for h in heuristics:
            if is_bidir:
                r = self._run_bidir(hname=h, instant=True)
            else:
                r = self._run_astar(hname=h, instant=True)
            r['heuristic'] = h
            results.append(r)

        win = tk.Toplevel(self)
        win.title('Compare All Heuristics')
        win.resizable(False, False)

        cols = ['Heuristic','Path Cost','Visited Nodes',
                'Max Open Nodes','Search Time (ms)','Operations']
        keys = ['heuristic','cost','visited','max_open','time','ops']

        for j, col in enumerate(cols):
            tk.Label(win, text=col, font=FONT['bold'], bg=COLOR['compare_header'],
                     relief='ridge', padx=6, pady=4).grid(row=0, column=j, sticky='nsew')

        for i, r in enumerate(results):
            bg = COLOR['compare_row'] if r['cost'] != '-' else COLOR['compare_err']
            for j, k in enumerate(keys):
                tk.Label(win, text=str(r[k]), font=FONT['main'], bg=bg,
                         relief='ridge', padx=6, pady=3).grid(row=i+1, column=j, sticky='nsew')

        for j in range(len(cols)):
            win.columnconfigure(j, weight=1)

if __name__ == '__main__':
    App().mainloop()
