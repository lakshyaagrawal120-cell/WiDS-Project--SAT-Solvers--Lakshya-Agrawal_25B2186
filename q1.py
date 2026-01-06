"""
sudoku_solver.py

Implement the function `solve_sudoku(grid: List[List[int]]) -> List[List[int]]` using a SAT solver from PySAT.
"""

from pysat.formula import CNF
from pysat.solvers import Solver
from typing import List

def solve_sudoku(grid: List[List[int]]) -> List[List[int]]:
    """Solves a Sudoku puzzle using a SAT solver. Input is a 2D grid with 0s for blanks."""

    def get_var(row, col, digit):
        return (row * 9 + col) * 9 + digit

    cnf = CNF()
    size = 9

    for row in range(size):
        for col in range(size):
            clause = []
            for digit in range(1, 10):
                clause.append(get_var(row, col, digit))
            cnf.append(clause)

            for d1 in range(1, 10):
                for d2 in range(d1 + 1, 10):
                    cnf.append([
                        -get_var(row, col, d1),
                        -get_var(row, col, d2)
                    ])

    for row in range(size):
        for digit in range(1, 10):
            for col1 in range(size):
                for col2 in range(col1 + 1, size):
                    cnf.append([
                        -get_var(row, col1, digit),
                        -get_var(row, col2, digit)
                    ])

    for col in range(size):
        for digit in range(1, 10):
            for row1 in range(size):
                for row2 in range(row1 + 1, size):
                    cnf.append([
                        -get_var(row1, col, digit),
                        -get_var(row2, col, digit)
                    ])

    for start_row in range(0, 9, 3):
        for start_col in range(0, 9, 3):
            for digit in range(1, 10):
                cells = []
                for i in range(3):
                    for j in range(3):
                        cells.append((start_row + i, start_col + j))

                for i in range(len(cells)):
                    for j in range(i + 1, len(cells)):
                        r1, c1 = cells[i]
                        r2, c2 = cells[j]
                        cnf.append([
                            -get_var(r1, c1, digit),
                            -get_var(r2, c2, digit)
                        ])

    for row in range(size):
        for col in range(size):
            value = grid[row][col]
            if value != 0:
                cnf.append([get_var(row, col, value)])

    with Solver(name="g3", bootstrap_with=cnf.clauses) as solver:
        if not solver.solve():
            return []
        model = solver.get_model()

    solved_grid = [[0 for _ in range(size)] for _ in range(size)]

    for variable in model:
        if variable > 0:
            index = variable - 1
            digit = (index % 9) + 1
            col = (index // 9) % 9
            row = index // 81
            solved_grid[row][col] = digit

    return solved_grid
