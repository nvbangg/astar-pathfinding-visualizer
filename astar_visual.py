import math
import heapq
import itertools
import time
import tkinter as tk
from tkinter import ttk

class Node:
    __slots__ = ['x', 'y', 'walkable', 'g', 'f', 'h', 'opened', 'closed', 'parent',
                 'by', 'opened_end', 'closed_end', 'g_end', 'f_end', 'h_end', 'parent_end']
    def __init__(self, x, y, walkable=True):
        self.x = x
        self.y = y
        self.walkable = walkable
        self.reset()
        
    def reset(self):
        self.g = 0
        self.f = 0
        self.h = 0
        self.opened = False
        self.closed = False
        self.parent = None
        
        self.by = 0
        self.opened_end = False
        self.closed_end = False
        self.g_end = 0
        self.f_end = 0
        self.h_end = 0
        self.parent_end = None

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.nodes = [[Node(x, y) for x in range(width)] for y in range(height)]
        
    def get_node_at(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.nodes[y][x]
        return None
        
    def is_walkable_at(self, x, y):
        node = self.get_node_at(x, y)
        return node.walkable if node else False
        
    def set_walkable_at(self, x, y, walkable):
        node = self.get_node_at(x, y)
        if node:
            node.walkable = walkable
            
    def get_neighbors(self, node, allow_diagonal, dont_cross_corners):
        x, y = node.x, node.y
        neighbors = []
        
        up = self.is_walkable_at(x, y - 1)
        down = self.is_walkable_at(x, y + 1)
        left = self.is_walkable_at(x - 1, y)
        right = self.is_walkable_at(x + 1, y)
        
        if up: neighbors.append(self.nodes[y - 1][x])
        if right: neighbors.append(self.nodes[y][x + 1])
        if down: neighbors.append(self.nodes[y + 1][x])
        if left: neighbors.append(self.nodes[y][x - 1])
        
        if allow_diagonal:
            d0 = (up or right) if not dont_cross_corners else (up and right)
            d1 = (right or down) if not dont_cross_corners else (right and down)
            d2 = (down or left) if not dont_cross_corners else (down and left)
            d3 = (left or up) if not dont_cross_corners else (left and up)
            
            if d0 and self.is_walkable_at(x + 1, y - 1): neighbors.append(self.nodes[y - 1][x + 1])
            if d1 and self.is_walkable_at(x + 1, y + 1): neighbors.append(self.nodes[y + 1][x + 1])
            if d2 and self.is_walkable_at(x - 1, y + 1): neighbors.append(self.nodes[y + 1][x - 1])
            if d3 and self.is_walkable_at(x - 1, y - 1): neighbors.append(self.nodes[y - 1][x - 1])
                
        return neighbors
        
    def reset(self):
        for row in self.nodes:
            for node in row:
                node.reset()

class Heuristics:
    @staticmethod
    def manhattan(dx, dy):
        return dx + dy
    @staticmethod
    def euclidean(dx, dy):
        return math.sqrt(dx * dx + dy * dy)
    @staticmethod
    def octile(dx, dy):
        F = math.sqrt(2) - 1
        return max(dx, dy) + F * min(dx, dy)
    @staticmethod
    def chebyshev(dx, dy):
        return max(dx, dy)
    @staticmethod
    def dijkstra(dx, dy):
        return 0

def backtrace(node):
    path = []
    while node:
        path.append((node.x, node.y))
        node = node.parent
    path.reverse()
    return path

def bi_backtrace(node_a, node_b):
    path_a = []
    node = node_a
    while node:
        path_a.append((node.x, node.y))
        node = node.parent
    path_a.reverse()
    
    path_b = []
    node = node_b
    while node:
        path_b.append((node.x, node.y))
        node = node.parent_end
        
    return path_a + path_b

def astar(grid, start_x, start_y, end_x, end_y, options):
    counter = itertools.count()
    allow_diagonal = options.get('allow_diagonal', True)
    dont_cross_corners = options.get('dont_cross_corners', False)
    weight = options.get('weight', 1)
    heuristic_name = options.get('heuristic', 'manhattan')
    heuristic = getattr(Heuristics, heuristic_name)
    
    start_node = grid.get_node_at(start_x, start_y)
    end_node = grid.get_node_at(end_x, end_y)
    
    open_list = []
    heapq.heappush(open_list, (0, next(counter), start_node))
    start_node.opened = True
    yield {'op': 'opened', 'x': start_x, 'y': start_y, 'by': 1}
    
    SQRT2 = math.sqrt(2)
    operations_count = 0
    
    while open_list:
        _, _, node = heapq.heappop(open_list)
        if node.closed: continue
        node.closed = True
        yield {'op': 'closed', 'x': node.x, 'y': node.y, 'by': 1}
        operations_count += 1
        
        if node == end_node:
            yield {'op': 'path', 'path': backtrace(end_node), 'ops': operations_count}
            return
            
        neighbors = grid.get_neighbors(node, allow_diagonal, dont_cross_corners)
        for neighbor in neighbors:
            if neighbor.closed: continue
            
            x, y = neighbor.x, neighbor.y
            ng = node.g + (1 if x == node.x or y == node.y else SQRT2)
            
            if not neighbor.opened or ng < neighbor.g:
                neighbor.g = ng
                neighbor.h = neighbor.h or weight * heuristic(abs(x - end_x), abs(y - end_y))
                neighbor.f = neighbor.g + neighbor.h
                neighbor.parent = node
                
                if not neighbor.opened:
                    heapq.heappush(open_list, (neighbor.f, next(counter), neighbor))
                    neighbor.opened = True
                    yield {'op': 'opened', 'x': x, 'y': y, 'by': 1}
                else:
                    heapq.heappush(open_list, (neighbor.f, next(counter), neighbor))

    yield {'op': 'path', 'path': [], 'ops': operations_count}

def bi_astar(grid, start_x, start_y, end_x, end_y, options):
    counter = itertools.count()
    allow_diagonal = options.get('allow_diagonal', True)
    dont_cross_corners = options.get('dont_cross_corners', False)
    weight = options.get('weight', 1)
    heuristic_name = options.get('heuristic', 'manhattan')
    heuristic = getattr(Heuristics, heuristic_name)
    
    start_node = grid.get_node_at(start_x, start_y)
    end_node = grid.get_node_at(end_x, end_y)
    
    start_open_list = []
    end_open_list = []
    
    heapq.heappush(start_open_list, (0, next(counter), start_node))
    start_node.opened = True
    yield {'op': 'opened', 'x': start_x, 'y': start_y, 'by': 1}
    
    heapq.heappush(end_open_list, (0, next(counter), end_node))
    end_node.opened_end = True
    yield {'op': 'opened', 'x': end_x, 'y': end_y, 'by': 2}
    
    SQRT2 = math.sqrt(2)
    operations_count = 0
    
    while start_open_list and end_open_list:
        # Expand start
        _, _, node = heapq.heappop(start_open_list)
        if not node.closed:
            node.closed = True
            yield {'op': 'closed', 'x': node.x, 'y': node.y, 'by': 1}
            operations_count += 1
            
            neighbors = grid.get_neighbors(node, allow_diagonal, dont_cross_corners)
            for neighbor in neighbors:
                if neighbor.closed: continue
                
                x, y = neighbor.x, neighbor.y
                
                if neighbor.opened_end:
                    yield {'op': 'path', 'path': bi_backtrace(node, neighbor), 'ops': operations_count}
                    return
                    
                ng = node.g + (1 if x == node.x or y == node.y else SQRT2)
                
                if not neighbor.opened or ng < neighbor.g:
                    neighbor.g = ng
                    neighbor.h = neighbor.h or weight * heuristic(abs(x - end_x), abs(y - end_y))
                    neighbor.f = neighbor.g + neighbor.h
                    neighbor.parent = node
                    
                    if not neighbor.opened:
                        heapq.heappush(start_open_list, (neighbor.f, next(counter), neighbor))
                        neighbor.opened = True
                        yield {'op': 'opened', 'x': x, 'y': y, 'by': 1}
                    else:
                        heapq.heappush(start_open_list, (neighbor.f, next(counter), neighbor))

        # Expand end
        _, _, node_e = heapq.heappop(end_open_list)
        if not node_e.closed_end:
            node_e.closed_end = True
            yield {'op': 'closed', 'x': node_e.x, 'y': node_e.y, 'by': 2}
            operations_count += 1
            
            neighbors_e = grid.get_neighbors(node_e, allow_diagonal, dont_cross_corners)
            for neighbor in neighbors_e:
                if neighbor.closed_end: continue
                
                x, y = neighbor.x, neighbor.y
                
                if neighbor.opened:
                    yield {'op': 'path', 'path': bi_backtrace(neighbor, node_e), 'ops': operations_count}
                    return
                    
                ng = node_e.g_end + (1 if x == node_e.x or y == node_e.y else SQRT2)
                
                if not neighbor.opened_end or ng < neighbor.g_end:
                    neighbor.g_end = ng
                    neighbor.h_end = neighbor.h_end or weight * heuristic(abs(x - start_x), abs(y - start_y))
                    neighbor.f_end = neighbor.g_end + neighbor.h_end
                    neighbor.parent_end = node_e
                    
                    if not neighbor.opened_end:
                        heapq.heappush(end_open_list, (neighbor.f_end, next(counter), neighbor))
                        neighbor.opened_end = True
                        yield {'op': 'opened', 'x': x, 'y': y, 'by': 2}
                    else:
                        heapq.heappush(end_open_list, (neighbor.f_end, next(counter), neighbor))
                        
    yield {'op': 'path', 'path': [], 'ops': operations_count}

class PathFindingVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("A* Algorithm Visualizer")
        self.root.configure(bg="#222")
        
        self.cols = 64
        self.rows = 36
        self.node_size = 20
        self.grid = Grid(self.cols, self.rows)
        
        self.start_x = (self.cols // 2) - 5
        self.start_y = self.rows // 2
        self.end_x = (self.cols // 2) + 5
        self.end_y = self.rows // 2
        
        self.colors = {
            'empty': '#ffffff',
            'wall': '#333333',
            'start': '#00ff00',
            'end': '#ff0000',
            'opened': '#98fb98',
            'closed': '#afeeee',
            'path': '#ffff00',
            'grid': '#e0e0e0'
        }
        
        self.rects = {}
        self.state = 'ready'
        self.search_generator = None
        self.drag_state = None
        self.start_time = 0
        
        self.setup_ui()
        self.draw_initial_grid()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.left_frame = tk.Frame(self.root, bg='#222')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = tk.Frame(self.root, width=320, bg='#333', padx=15, pady=15)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(self.left_frame, width=self.cols * self.node_size, height=self.rows * self.node_size, bg='white', highlightthickness=0)
        self.canvas.pack(padx=20, pady=20)
        
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_press)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_release)
        
        tk.Label(self.right_frame, text="Select Algorithm", font=('Arial', 14, 'bold'), bg='#333', fg='white').pack(pady=(0, 10))
        
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.X, pady=5)
        
        self.tab_astar = tk.Frame(self.notebook, bg='#e0e0e0', padx=10, pady=10)
        self.notebook.add(self.tab_astar, text="A* / Dijkstra")
        
        tk.Label(self.tab_astar, text="Heuristic", font=('Arial', 10, 'bold'), bg='#e0e0e0').pack(anchor='w', pady=(5,5))
        self.heuristic_var = tk.StringVar(value='manhattan')
        heuristics = [('Manhattan', 'manhattan'), ('Euclidean', 'euclidean'), 
                      ('Octile', 'octile'), ('Chebyshev', 'chebyshev'), ('Dijkstra (H=0)', 'dijkstra')]
        for text, val in heuristics:
            tk.Radiobutton(self.tab_astar, text=text, variable=self.heuristic_var, value=val, bg='#e0e0e0').pack(anchor='w')
            
        tk.Label(self.tab_astar, text="Options", font=('Arial', 10, 'bold'), bg='#e0e0e0').pack(anchor='w', pady=(15,5))
        
        self.allow_diagonal_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.tab_astar, text="Allow Diagonal", variable=self.allow_diagonal_var, bg='#e0e0e0').pack(anchor='w')
        
        self.bi_directional_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.tab_astar, text="Bi-directional", variable=self.bi_directional_var, bg='#e0e0e0').pack(anchor='w')
        
        self.dont_cross_corners_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.tab_astar, text="Don't Cross Corners", variable=self.dont_cross_corners_var, bg='#e0e0e0').pack(anchor='w')
        
        frame_weight = tk.Frame(self.tab_astar, bg='#e0e0e0')
        frame_weight.pack(anchor='w', pady=10)
        tk.Label(frame_weight, text="Weight: ", bg='#e0e0e0').pack(side=tk.LEFT)
        self.weight_spin = tk.Spinbox(frame_weight, from_=1, to=100, width=5)
        self.weight_spin.pack(side=tk.LEFT)
        
        tk.Label(self.right_frame, text="Visual Speed (ops/sec)", font=('Arial', 10, 'bold'), bg='#333', fg='white').pack(anchor='w', pady=(25,5))
        self.speed_slider = tk.Scale(self.right_frame, from_=10, to=2000, orient=tk.HORIZONTAL, bg='#333', fg='white', highlightthickness=0, length=250)
        self.speed_slider.set(300)
        self.speed_slider.pack(anchor='w')
        
        self.btn_start = tk.Button(self.right_frame, text="Start Search", command=self.action_start, bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'), relief=tk.FLAT, pady=5)
        self.btn_start.pack(fill=tk.X, pady=(25,10))
        
        self.btn_pause = tk.Button(self.right_frame, text="Pause Search", command=self.action_pause, state=tk.DISABLED, bg='#ff9800', fg='white', font=('Arial', 10, 'bold'), relief=tk.FLAT, pady=5)
        self.btn_pause.pack(fill=tk.X, pady=5)
        
        self.btn_clear = tk.Button(self.right_frame, text="Clear Walls", command=self.action_clear_walls, bg='#2196F3', fg='white', font=('Arial', 10, 'bold'), relief=tk.FLAT, pady=5)
        self.btn_clear.pack(fill=tk.X, pady=5)
        
        self.btn_clear_path = tk.Button(self.right_frame, text="Clear Path", command=self.action_clear_path, bg='#f44336', fg='white', font=('Arial', 10, 'bold'), relief=tk.FLAT, pady=5)
        self.btn_clear_path.pack(fill=tk.X, pady=5)
        
        self.lbl_stats = tk.Label(self.right_frame, text="", bg='#333', fg='#4CAF50', justify=tk.LEFT, font=('Arial', 11, 'bold'))
        self.lbl_stats.pack(anchor='w', pady=(20,0))
        
    def draw_initial_grid(self):
        self.canvas.delete("all")
        for y in range(self.rows):
            for x in range(self.cols):
                x1 = x * self.node_size
                y1 = y * self.node_size
                x2 = x1 + self.node_size
                y2 = y1 + self.node_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.colors['empty'], outline=self.colors['grid'])
                self.rects[(x, y)] = rect
        self.update_node_color(self.start_x, self.start_y)
        self.update_node_color(self.end_x, self.end_y)
                
    def get_color_for(self, x, y):
        if x == self.start_x and y == self.start_y: return self.colors['start']
        if x == self.end_x and y == self.end_y: return self.colors['end']
        node = self.grid.get_node_at(x, y)
        if not node.walkable: return self.colors['wall']
        if node.closed or node.closed_end: return self.colors['closed']
        if node.opened or node.opened_end: return self.colors['opened']
        return self.colors['empty']

    def update_node_color(self, x, y, force_color=None):
        if (x, y) in self.rects:
            color = force_color if force_color else self.get_color_for(x, y)
            self.canvas.itemconfig(self.rects[(x, y)], fill=color)

    def on_mouse_press(self, event):
        if self.state in ('searching', 'starting'): return
        x = event.x // self.node_size
        y = event.y // self.node_size
        if not (0 <= x < self.cols and 0 <= y < self.rows): return
        
        if self.state == 'finished':
            self.action_clear_path()
            
        if x == self.start_x and y == self.start_y:
            self.drag_state = 'start'
        elif x == self.end_x and y == self.end_y:
            self.drag_state = 'end'
        elif self.grid.is_walkable_at(x, y):
            self.drag_state = 'wall'
            self.grid.set_walkable_at(x, y, False)
            self.update_node_color(x, y)
        else:
            self.drag_state = 'erase'
            self.grid.set_walkable_at(x, y, True)
            self.update_node_color(x, y)
            
    def on_mouse_drag(self, event):
        if not self.drag_state or self.state in ('searching', 'starting'): return
        x = event.x // self.node_size
        y = event.y // self.node_size
        if not (0 <= x < self.cols and 0 <= y < self.rows): return
        
        if self.drag_state == 'start':
            if (x != self.end_x or y != self.end_y) and self.grid.is_walkable_at(x, y):
                old_x, old_y = self.start_x, self.start_y
                self.start_x, self.start_y = x, y
                self.update_node_color(old_x, old_y)
                self.update_node_color(x, y)
        elif self.drag_state == 'end':
            if (x != self.start_x or y != self.start_y) and self.grid.is_walkable_at(x, y):
                old_x, old_y = self.end_x, self.end_y
                self.end_x, self.end_y = x, y
                self.update_node_color(old_x, old_y)
                self.update_node_color(x, y)
        elif self.drag_state == 'wall':
            if not (x == self.start_x and y == self.start_y) and not (x == self.end_x and y == self.end_y):
                self.grid.set_walkable_at(x, y, False)
                self.update_node_color(x, y)
        elif self.drag_state == 'erase':
            if not (x == self.start_x and y == self.start_y) and not (x == self.end_x and y == self.end_y):
                self.grid.set_walkable_at(x, y, True)
                self.update_node_color(x, y)

    def on_mouse_release(self, event):
        self.drag_state = None

    def get_options(self):
        try:
            w = int(self.weight_spin.get())
        except:
            w = 1
        return {
            'heuristic': self.heuristic_var.get(),
            'allow_diagonal': self.allow_diagonal_var.get(),
            'bi_directional': self.bi_directional_var.get(),
            'dont_cross_corners': self.dont_cross_corners_var.get(),
            'weight': max(1, w)
        }

    def action_start(self):
        if self.state == 'searching': return
        self.action_clear_path()
        self.state = 'searching'
        self.btn_start.config(text="Restart Search", command=self.action_start)
        self.btn_pause.config(state=tk.NORMAL, text="Pause Search")
        self.lbl_stats.config(text="")
        
        opts = self.get_options()
        self.grid.reset()
        
        self.start_time = time.time()
        
        if opts['bi_directional']:
            self.search_generator = bi_astar(self.grid, self.start_x, self.start_y, self.end_x, self.end_y, opts)
        else:
            self.search_generator = astar(self.grid, self.start_x, self.start_y, self.end_x, self.end_y, opts)
            
        self.loop()

    def action_pause(self):
        if self.state == 'searching':
            self.state = 'paused'
            self.btn_pause.config(text="Resume Search")
        elif self.state == 'paused':
            self.state = 'searching'
            self.btn_pause.config(text="Pause Search")
            self.loop()

    def action_clear_walls(self):
        self.action_clear_path()
        for y in range(self.rows):
            for x in range(self.cols):
                self.grid.set_walkable_at(x, y, True)
                self.update_node_color(x, y)

    def action_clear_path(self):
        self.state = 'ready'
        self.search_generator = None
        self.grid.reset()
        for y in range(self.rows):
            for x in range(self.cols):
                self.update_node_color(x, y)
        self.btn_start.config(text="Start Search", command=self.action_start)
        self.btn_pause.config(state=tk.DISABLED, text="Pause Search")
        self.lbl_stats.config(text="")

    def loop(self):
        if self.state != 'searching': return
        
        ops_per_sec = self.speed_slider.get()
        steps_per_frame = max(1, int(ops_per_sec / 60))
        interval_ms = max(1, int(1000 / ops_per_sec)) if ops_per_sec < 60 else 16
        
        try:
            for _ in range(steps_per_frame):
                step = next(self.search_generator)
                
                if step['op'] == 'path':
                    self.state = 'finished'
                    path = step['path']
                    time_spent = time.time() - self.start_time
                    
                    for (x, y) in path:
                        if (x, y) != (self.start_x, self.start_y) and (x, y) != (self.end_x, self.end_y):
                            self.update_node_color(x, y, self.colors['path'])
                            
                    self.lbl_stats.config(text=f"Time Spent: {time_spent*1000:.2f} ms\nPath Length: {len(path)-1 if path else 0}\nOperations: {step['ops']}")
                    self.btn_pause.config(state=tk.DISABLED, text="Pause Search")
                    return
                else:
                    x, y = step['x'], step['y']
                    if (x, y) != (self.start_x, self.start_y) and (x, y) != (self.end_x, self.end_y):
                        self.update_node_color(x, y)
                        
            self.root.after(interval_ms, self.loop)
        except StopIteration:
            self.state = 'finished'
            self.btn_pause.config(state=tk.DISABLED, text="Pause Search")

if __name__ == "__main__":
    root = tk.Tk()
    app = PathFindingVisualizer(root)
    root.mainloop()
