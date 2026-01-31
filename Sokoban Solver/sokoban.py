"""
Sokoban Solver using SAT
--------------------------------------

Grid Encoding:
- 'P' = Player
- 'B' = Box
- 'G' = Goal
- '#' = Wall
- '.' = Empty space
"""

from pysat.formula import CNF
from pysat.solvers import Solver

# Directions for movement
DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}

class SokobanEncoder:
    def __init__(self, grid, T):
        
        self.grid = grid
        self.T = T
        self.N = len(grid)
        self.M = len(grid[0])

        self.goals = []
        self.boxes = []
        self.player_start = None
        self.walls = set()

        self._parse_grid()

        self.num_cells = self.N * self.M
        self.num_steps = self.T + 1

        # Base indices for variables
        # Player vars start at 1
        self.base_player = 1
        # Box vars start after all player vars
        self.base_box = self.base_player + (self.num_cells * self.num_steps)
        # Action vars start after all box vars
        self.base_action = self.base_box + (self.num_cells * self.num_steps)

        self.cnf = CNF()

    def _parse_grid(self):
        
        for r in range(self.N):
            for c in range(self.M):
                char = self.grid[r][c]
                if char == '#':
                    self.walls.add((r, c))
                elif char == 'P':
                    self.player_start = (r, c)
                elif char == 'B':
                    self.boxes.append((r, c))
                elif char == 'G':
                    self.goals.append((r, c))

    
    def var_player(self, x, y, t):

        return self.base_player + (t * self.num_cells) + (x * self.M) + y

    def var_box(self, b, x, y, t):

        return self.base_box + (t * self.num_cells) + (x * self.M) + y

    def var_action(self, t, i):

        return self.base_action + (t * 5) + i

    
    def is_valid(self, r, c):
        if r < 0 or r >= self.N: return False
        if c < 0 or c >= self.M: return False
        if (r, c) in self.walls: return False
        return True

    def get_combinations(self, pools):
        
        result = [[]]
        for pool in pools:
            new_result = []
            for x in result:
                for y in pool:
                    new_result.append(x + [y])
            result = new_result
        return result

    
    def encode(self):
        """
        Build CNF constraints for Sokoban.
        """
        # 1. Initial State
        for r in range(self.N):
            for c in range(self.M):
                p = self.var_player(r, c, 0)
                if (r, c) == self.player_start:
                    self.cnf.append([p])
                else:
                    self.cnf.append([-p])

                b = self.var_box(0, r, c, 0)
                if (r, c) in self.boxes:
                    self.cnf.append([b])
                else:
                    self.cnf.append([-b])

        # 2. Goal State
        for (r, c) in self.goals:
            self.cnf.append([self.var_box(0, r, c, self.T)])

        # 3. Transitions
        for t in range(self.T):
            
            # Action constraints: At least one action
            actions = []
            for i in range(5):
                actions.append(self.var_action(t, i))
            self.cnf.append(actions)
            
            # At most one action
            for i in range(5):
                for j in range(i + 1, 5):
                    self.cnf.append([-actions[i], -actions[j]])

            # Wait Action Effects
            wait_act = self.var_action(t, 4)
            for r in range(self.N):
                for c in range(self.M):
                    if (r, c) in self.walls: continue
                    curr_p = self.var_player(r, c, t)
                    next_p = self.var_player(r, c, t+1)
                    self.cnf.append([-wait_act, -curr_p, next_p])
                    self.cnf.append([-wait_act, curr_p, -next_p])

            # Move Action Effects
            for i in range(4):
                dr, dc = 0, 0
                if i == 0: dr, dc = -1, 0  # Up
                elif i == 1: dr, dc = 1, 0 # Down
                elif i == 2: dr, dc = 0, -1 # Left
                elif i == 3: dr, dc = 0, 1  # Right
                
                act = self.var_action(t, i)

                for r in range(self.N):
                    for c in range(self.M):
                        if (r, c) in self.walls:
                            self.cnf.append([-self.var_player(r, c, t)])
                            continue

                        curr_p = self.var_player(r, c, t)
                        nr, nc = r + dr, c + dc

                        if not self.is_valid(nr, nc):
                            self.cnf.append([-act, -curr_p])
                            continue

                        next_p = self.var_player(nr, nc, t+1)
                        box_at_target = self.var_box(0, nr, nc, t)

                        # Move into empty space
                        self.cnf.append([-act, -curr_p, box_at_target, next_p])

                        # Push box
                        pr, pc = nr + dr, nc + dc
                        if self.is_valid(pr, pc):
                            box_dest_curr = self.var_box(0, pr, pc, t)
                            box_dest_next = self.var_box(0, pr, pc, t+1)
                            box_target_next = self.var_box(0, nr, nc, t+1)

                            pre = [-act, -curr_p, -box_at_target]
                            self.cnf.append(pre + [next_p])
                            self.cnf.append(pre + [box_dest_next])
                            self.cnf.append(pre + [-box_target_next])
                            self.cnf.append(pre + [-box_dest_curr])
                        else:
                            self.cnf.append([-act, -curr_p, -box_at_target])

            # Frame Axioms (Inertia)
            for r in range(self.N):
                for c in range(self.M):
                    if (r, c) in self.walls:
                        self.cnf.append([-self.var_player(r, c, t+1)])
                        self.cnf.append([-self.var_box(0, r, c, t+1)])
                        continue

                    curr_b = self.var_box(0, r, c, t)
                    next_b = self.var_box(0, r, c, t+1)

                    # 1. Box Arrival
                    arrivals = []
                    for k in range(4):
                        dr, dc = 0, 0
                        if k == 0: dr, dc = -1, 0
                        elif k == 1: dr, dc = 1, 0
                        elif k == 2: dr, dc = 0, -1
                        elif k == 3: dr, dc = 0, 1
                        
                        sr, sc = r - dr, c - dc
                        pr, pc = r - 2*dr, c - 2*dc
                        
                        if self.is_valid(sr, sc) and self.is_valid(pr, pc):
                            arrivals.append([
                                self.var_action(t, k),
                                self.var_player(pr, pc, t),
                                self.var_box(0, sr, sc, t)
                            ])

                    base = [-next_b, curr_b]
                    if len(arrivals) > 0:
                        for combo in self.get_combinations(arrivals):
                            self.cnf.append(base + list(combo))
                    else:
                        self.cnf.append(base)

                    # 2. Box Departure
                    departures = []
                    for k in range(4):
                        dr, dc = 0, 0
                        if k == 0: dr, dc = -1, 0
                        elif k == 1: dr, dc = 1, 0
                        elif k == 2: dr, dc = 0, -1
                        elif k == 3: dr, dc = 0, 1
                        
                        pr, pc = r - dr, c - dc
                        if self.is_valid(pr, pc):
                            departures.append([
                                self.var_action(t, k),
                                self.var_player(pr, pc, t)
                            ])
                    
                    base = [-curr_b, next_b]
                    if len(departures) > 0:
                        for combo in self.get_combinations(departures):
                            self.cnf.append(base + list(combo))
                    else:
                        self.cnf.append(base)

                    # 3. Player Arrival
                    curr_p = self.var_player(r, c, t)
                    next_p = self.var_player(r, c, t+1)
                    
                    reasons = []
                    reasons.append([self.var_action(t, 4), curr_p]) # Wait
                    
                    for k in range(4):
                        dr, dc = 0, 0
                        if k == 0: dr, dc = -1, 0
                        elif k == 1: dr, dc = 1, 0
                        elif k == 2: dr, dc = 0, -1
                        elif k == 3: dr, dc = 0, 1
                        
                        pr, pc = r - dr, c - dc
                        if self.is_valid(pr, pc):
                            reasons.append([
                                self.var_action(t, k),
                                self.var_player(pr, pc, t)
                            ])
                    
                    base = [-next_p]
                    if len(reasons) > 0:
                        for combo in self.get_combinations(reasons):
                            self.cnf.append(base + list(combo))
                    else:
                        self.cnf.append(base)
        
        return self.cnf


def decode(model, encoder):
   
    moves = []
    model_set = set(model)
    
    for t in range(encoder.T):
        for i in range(5):
            act_var = encoder.var_action(t, i)
            if act_var in model_set:
                direction = ""
                if i == 0: direction = 'U'
                elif i == 1: direction = 'D'
                elif i == 2: direction = 'L'
                elif i == 3: direction = 'R'
                
                if direction != "":
                    moves.append(direction)
                break
    return moves


def solve_sokoban(grid, T):
    
    encoder = SokobanEncoder(grid, T)
    cnf = encoder.encode()

    with Solver(name='g3') as solver:
        solver.append_formula(cnf)
        if not solver.solve():
            return -1

        model = solver.get_model()
        if not model:
            return -1

        return decode(model, encoder)