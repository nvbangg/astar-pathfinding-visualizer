import tkinter as tk
from tkinter import ttk
import heapq
import random
import time
import math

CELL = 25
COLS, ROWS = 50, 30
COLOR = {
    'empty': '#FFFFFF', 'wall': '#555555',
    'start': '#2E7D32', 'end': '#D32F2F',
    'open': '#4CAF50', 'closed': '#A5D6A7',
    'path': '#FFD600', 'grid': '#E0E0E0',
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("A* Pathfinding Visualizer")
        self.state('zoomed')

        self.grid_data = [[0]*COLS for _ in range(ROWS)]
        self.start = (2, 2)
        self.end = (ROWS-3, COLS-3)
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

        self.canvas = tk.Canvas(self, bg='#FAFAFA', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.bind('<Button-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)

        panel = tk.Frame(self, width=260, bg='#F5F5F5', padx=12, pady=10)
        panel.grid(row=0, column=1, sticky='ns')
        panel.grid_propagate(False)

        # Settings
        tk.Label(panel, text='Settings', font=('Segoe UI',12,'bold'),
                 bg='#F5F5F5').pack(anchor='w', pady=(0,6))

        tk.Label(panel, text='Heuristic:', bg='#F5F5F5',
                 font=('Segoe UI',9)).pack(anchor='w')
        self.heuristic = ttk.Combobox(panel, state='readonly', width=22,
            values=['Euclidean','Manhattan','Octile','Chebyshev','Dijkstra (h=0)'])
        self.heuristic.set('Euclidean')
        self.heuristic.pack(anchor='w', pady=(0,6))

        self.allow_diag = tk.BooleanVar(value=True)
        self.cross_corner = tk.BooleanVar()
        self.diag_cost1 = tk.BooleanVar()
        self.bidir = tk.BooleanVar()

        tk.Checkbutton(panel, text='Allow Diagonal', variable=self.allow_diag,
                       bg='#F5F5F5', font=('Segoe UI',9),
                       command=self._toggle_diag).pack(anchor='w')
        self.cb_cross = tk.Checkbutton(panel, text='Allow Cross Corners',
                       variable=self.cross_corner, bg='#F5F5F5', font=('Segoe UI',9))
        self.cb_cross.pack(anchor='w', padx=(16,0))
        self.cb_dcost = tk.Checkbutton(panel, text='Diagonal Cost = 1',
                       variable=self.diag_cost1, bg='#F5F5F5', font=('Segoe UI',9))
        self.cb_dcost.pack(anchor='w', padx=(16,0))
        tk.Checkbutton(panel, text='Bi-directional', variable=self.bidir,
                       bg='#F5F5F5', font=('Segoe UI',9)).pack(anchor='w')

        tk.Label(panel, text='Speed:', bg='#F5F5F5',
                 font=('Segoe UI',9)).pack(anchor='w', pady=(8,0))
        self.speed = tk.Scale(panel, from_=1, to=100, orient='horizontal',
                              bg='#F5F5F5', highlightthickness=0, length=220)
        self.speed.set(95)
        self.speed.pack(anchor='w')

        # Controls
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=8)
        tk.Label(panel, text='Controls', font=('Segoe UI',12,'bold'),
                 bg='#F5F5F5').pack(anchor='w', pady=(0,6))

        bf = tk.Frame(panel, bg='#F5F5F5')
        bf.pack(fill='x')

        self.btn_start = tk.Button(bf, text='Start', width=12, bg='#4CAF50',
                                   fg='white', font=('Segoe UI',9,'bold'),
                                   relief='flat', command=self._toggle_run)
        self.btn_start.grid(row=0, column=0, padx=2, pady=2)
        tk.Button(bf, text='Next Step', width=12, bg='#607D8B', fg='white',
                  font=('Segoe UI',9), relief='flat',
                  command=self._next_step).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(bf, text='Clear Path', width=12, bg='#FF9800', fg='white',
                  font=('Segoe UI',9), relief='flat',
                  command=self._clear_path).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(bf, text='Clear Walls', width=12, bg='#E53935', fg='white',
                  font=('Segoe UI',9), relief='flat',
                  command=self._clear_walls).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(bf, text='Random Walls', width=12, bg='#795548', fg='white',
                  font=('Segoe UI',9), relief='flat',
                  command=self._random_walls).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(bf, text='Random Maze', width=12, bg='#795548', fg='white',
                  font=('Segoe UI',9), relief='flat',
                  command=self._random_maze).grid(row=2, column=1, padx=2, pady=2)
        tk.Button(bf, text='Compare All', width=26, bg='#3F51B5', fg='white',
                  font=('Segoe UI',9,'bold'), relief='flat',
                  command=self._compare_all).grid(row=3, column=0, columnspan=2, padx=2, pady=2)

        # Statistics
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=8)
        tk.Label(panel, text='Statistics', font=('Segoe UI',12,'bold'),
                 bg='#F5F5F5').pack(anchor='w', pady=(0,6))

        labels = [('Path Cost','cost'),
                  ('Visited Nodes','visited'),('Max Open Nodes','max_open'),
                  ('Search Time','time'),('Operations','ops')]
        for text, key in labels:
            f = tk.Frame(panel, bg='#F5F5F5')
            f.pack(fill='x', pady=1)
            tk.Label(f, text=f'{text}:', bg='#F5F5F5',
                     font=('Segoe UI',9)).pack(side='left')
            tk.Label(f, textvariable=self.stats[key], bg='#F5F5F5',
                     font=('Segoe UI',9,'bold')).pack(side='right')

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
        elif pos != self.start and pos != self.end:
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
            self.paused = not self.paused
            self.btn_start.config(text='Start' if self.paused else 'Pause',
                                  bg='#4CAF50' if self.paused else '#FFC107')
        else:
            self._clear_path()
            self.running = True
            self.paused = False
            self.step_mode = False
            self.btn_start.config(text='Pause', bg='#FFC107')
            self.after(10, self._run_algorithm)

    def _next_step(self):
        if not self.running:
            self._clear_path()
            self.running = True
            self.paused = False
            self.step_mode = True
            self.btn_start.config(text='Pause', bg='#FFC107')
            self.after(10, self._run_algorithm)
        else:
            self.step_event = True

    def _clear_path(self):
        self.running = False
        self.paused = False
        self.step_mode = False
        self.visualized = False
        self.btn_start.config(text='Start', bg='#4CAF50')
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
                if (r,c) != self.start and (r,c) != self.end and random.random() < 0.3:
                    self.grid_data[r][c] = 1
                    self._set_cell(r, c, 'wall')

    def _random_maze(self):
        # Tạo mê cung bằng Recursive Backtracking
        self._clear_walls()
        self.grid_data = [[1]*COLS for _ in range(ROWS)]

        sr, sc = 1, 1
        self.start = (sr, sc)
        er = ROWS-2 if (ROWS-2) % 2 == 1 else ROWS-3
        ec = COLS-2 if (COLS-2) % 2 == 1 else COLS-3
        self.end = (er, ec)

        stack = [(sr, sc)]
        self.grid_data[sr][sc] = 0
        while stack:
            cr, cc = stack[-1]
            neighbors = []
            for dr, dc in [(-2,0),(2,0),(0,-2),(0,2)]:
                nr, nc = cr+dr, cc+dc
                if 0 < nr < ROWS-1 and 0 < nc < COLS-1 and self.grid_data[nr][nc]:
                    neighbors.append((nr, nc, cr+dr//2, cc+dc//2))
            if neighbors:
                nr, nc, wr, wc = random.choice(neighbors)
                self.grid_data[wr][wc] = 0
                self.grid_data[nr][nc] = 0
                stack.append((nr, nc))
            else:
                stack.pop()

        self.grid_data[sr][sc] = 0
        self.grid_data[er][ec] = 0
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
        cross = self.cross_corner.get()
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
                    if cross:
                        # Cho phép sát 1 góc tường, chặn khi kẹp giữa 2 vật cản
                        if w1 and w2:
                            continue
                    else:
                        # Mặc định: không cho đi sát góc tường
                        if w1 or w2:
                            continue
                    result.append(((nr,nc), dcost))
        return result

    # * ── Thuật toán A* ─────
    def _run_algorithm(self):
        if self.bidir.get():
            self._run_bidir()
        else:
            self._run_astar()

    def _run_astar(self):
        start, end = self.start, self.end
        g = {start: 0}
        came_from = {start: None}
        counter = 0
        ops = 0
        open_set = [(self._h(start, end), counter, start)]
        in_open = {start}
        closed = set()
        max_open = 1
        t0 = time.perf_counter()

        def step():
            nonlocal counter, ops, max_open
            if not self.running:
                return

            if self.paused and not self.step_mode:
                self.after(50, step)
                return
            if self.step_mode and not self.step_event and counter > 0:
                self.after(50, step)
                return
            self.step_event = False

            if not open_set:
                self._finish(None, g, len(closed), max_open, t0, ops)
                return

            f, _, current = heapq.heappop(open_set)
            in_open.discard(current)
            ops += 1

            if current == end:
                path = []
                n = current
                while n:
                    path.append(n)
                    n = came_from[n]
                self._finish(path, g, len(closed), max_open, t0, ops)
                return

            closed.add(current)
            if current != start:
                self._set_cell(*current, 'closed')

            for nb, cost in self._neighbors(current):
                if nb in closed:
                    continue
                ng = g[current] + cost
                ops += 1
                if nb not in g or ng < g[nb]:
                    g[nb] = ng
                    came_from[nb] = current
                    counter += 1
                    heapq.heappush(open_set, (ng + self._h(nb, end), counter, nb))
                    in_open.add(nb)
                    if nb != end:
                        self._set_cell(*nb, 'open')

            max_open = max(max_open, len(in_open))
            delay = max(1, 101 - self.speed.get())
            self.after(delay, step)

        step()

    def _run_bidir(self):
        start, end = self.start, self.end
        gf, gb = {start: 0}, {end: 0}
        cf, cb = {start: None}, {end: None}
        counter = 0
        ops = 0
        of = [(self._h(start, end), counter, start)]
        counter += 1
        ob = [(self._h(end, start), counter, end)]
        inf_f, inf_b = {start}, {end}
        clf, clb = set(), set()
        max_open = 2
        best = float('inf')
        meet = None
        t0 = time.perf_counter()

        def step():
            nonlocal counter, ops, max_open, best, meet
            if not self.running:
                return
            if self.paused and not self.step_mode:
                self.after(50, step)
                return
            if self.step_mode and not self.step_event and counter > 2:
                self.after(50, step)
                return
            self.step_event = False

            if not of and not ob:
                self._finish_bidir(meet, cf, cb, gf, len(clf)+len(clb), max_open, t0, ops)
                return

            # Mở rộng 1 phía mỗi step
            for oset, g_cur, came, g_other, closed_cur, in_cur, closed_other, target in [
                (of, gf, cf, gb, clf, inf_f, clb, end),
                (ob, gb, cb, gf, clb, inf_b, clf, start)]:
                if not oset:
                    continue
                f, _, current = heapq.heappop(oset)
                in_cur.discard(current)
                ops += 1

                closed_cur.add(current)
                if current != start and current != end:
                    self._set_cell(*current, 'closed')

                if current in closed_other:
                    total = g_cur[current] + g_other[current]
                    if total < best:
                        best = total
                        meet = current

                for nb, cost in self._neighbors(current):
                    if nb in closed_cur:
                        continue
                    ng = g_cur[current] + cost
                    ops += 1
                    if nb not in g_cur or ng < g_cur[nb]:
                        g_cur[nb] = ng
                        came[nb] = current
                        counter += 1
                        heapq.heappush(oset, (ng + self._h(nb, target), counter, nb))
                        in_cur.add(nb)
                        if nb != start and nb != end:
                            self._set_cell(*nb, 'open')
                        if nb in g_other:
                            total = ng + g_other[nb]
                            if total < best:
                                best = total
                                meet = nb
                break

            max_open = max(max_open, len(inf_f) + len(inf_b))

            min_f = of[0][0] if of else float('inf')
            min_b = ob[0][0] if ob else float('inf')
            if best <= min(min_f, min_b):
                self._finish_bidir(meet, cf, cb, gf, len(clf)+len(clb), max_open, t0, ops)
                return

            delay = max(1, 101 - self.speed.get())
            self.after(delay, step)

        step()

    def _set_stats(self, cost, visited, max_open, elapsed, ops):
        self.stats['cost'].set(cost)
        self.stats['visited'].set(str(visited))
        self.stats['max_open'].set(str(max_open))
        self.stats['time'].set(f'{elapsed:.2f} ms')
        self.stats['ops'].set(str(ops))
        self.running = False
        self.visualized = True
        self.btn_start.config(text='Start', bg='#4CAF50')

    def _draw_path(self, path):
        for p in path:
            if p != self.start and p != self.end:
                self._set_cell(*p, 'path')

    def _finish(self, path, g, visited, max_open, t0, ops):
        elapsed = (time.perf_counter() - t0) * 1000
        if path is None:
            self._set_stats('-', visited, max_open, elapsed, ops)
        else:
            self._draw_path(path)
            self._set_stats(f'{g[self.end]:.2f}', visited, max_open, elapsed, ops)

    def _build_bidir_path(self, meet, cf, cb):
        path = []
        n = meet
        while n:
            path.append(n)
            n = cf.get(n)
        path.reverse()
        n = cb.get(meet)
        while n:
            path.append(n)
            n = cb.get(n)
        return path

    def _path_cost(self, path):
        return sum(
            math.hypot(path[i][0]-path[i+1][0], path[i][1]-path[i+1][1])
            if not self.diag_cost1.get() else
            max(abs(path[i][0]-path[i+1][0]), abs(path[i][1]-path[i+1][1]))
            for i in range(len(path)-1))

    def _finish_bidir(self, meet, cf, cb, gf, visited, max_open, t0, ops):
        elapsed = (time.perf_counter() - t0) * 1000
        if meet is None:
            self._set_stats('-', visited, max_open, elapsed, ops)
        else:
            path = self._build_bidir_path(meet, cf, cb)
            self._draw_path(path)
            self._set_stats(f'{self._path_cost(path):.2f}',
                           visited, max_open, elapsed, ops)

    # * ── Compare All ────
    def _astar_instant(self, hname):
        # Chạy A* tức thì, tái sử dụng _neighbors, chỉ thay heuristic
        start, end = self.start, self.end
        g = {start: 0}
        came = {start: None}
        cnt = ops = 0
        oset = [(self._h(start, end, hname), cnt, start)]
        in_open = {start}
        closed = set()
        max_open = 1
        t0 = time.perf_counter()

        while oset:
            _, _, cur = heapq.heappop(oset)
            in_open.discard(cur)
            ops += 1
            if cur == end:
                elapsed = (time.perf_counter() - t0) * 1000
                return {'cost':f'{g[end]:.2f}',
                        'visited':len(closed),'max_open':max_open,
                        'time':f'{elapsed:.2f}','ops':ops}
            closed.add(cur)
            for nb, cost in self._neighbors(cur):
                if nb in closed:
                    continue
                ng = g[cur] + cost
                ops += 1
                if nb not in g or ng < g[nb]:
                    g[nb] = ng
                    came[nb] = cur
                    cnt += 1
                    heapq.heappush(oset, (ng + self._h(nb, end, hname), cnt, nb))
                    in_open.add(nb)
            max_open = max(max_open, len(in_open))

        elapsed = (time.perf_counter() - t0) * 1000
        return {'cost':'-',
                'visited':len(closed),'max_open':max_open,
                'time':f'{elapsed:.2f}','ops':ops}

    def _compare_all(self):
        if self.running:
            return
        heuristics = ['Euclidean','Manhattan','Octile','Chebyshev','Dijkstra (h=0)']
        results = []
        for h in heuristics:
            r = self._astar_instant(h)
            r['heuristic'] = h
            results.append(r)

        win = tk.Toplevel(self)
        win.title('Compare All Heuristics')
        win.resizable(False, False)

        cols = ['Heuristic','Path Cost','Visited Nodes',
                'Max Open Nodes','Search Time (ms)','Operations']
        keys = ['heuristic','cost','visited','max_open','time','ops']

        for j, col in enumerate(cols):
            tk.Label(win, text=col, font=('Segoe UI',9,'bold'), bg='#E0E0E0',
                     relief='ridge', padx=6, pady=4).grid(row=0, column=j, sticky='nsew')

        for i, r in enumerate(results):
            bg = '#F9FBE7' if r['cost'] != '-' else '#FFEBEE'
            for j, k in enumerate(keys):
                tk.Label(win, text=str(r[k]), font=('Segoe UI',9), bg=bg,
                         relief='ridge', padx=6, pady=3).grid(row=i+1, column=j, sticky='nsew')

        for j in range(len(cols)):
            win.columnconfigure(j, weight=1)

if __name__ == '__main__':
    App().mainloop()
