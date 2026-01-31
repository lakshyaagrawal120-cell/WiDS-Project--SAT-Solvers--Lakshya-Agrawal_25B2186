# WiDS-Project--SAT-Solvers--Lakshya-Agrawal_25B2186

Sudoku Solver using SAT (PySAT)
==============================

This program solves a 9x9 Sudoku puzzle using a SAT solver from the PySAT
library.

The Sudoku grid is given as a 2D list where 0 means an empty cell and
numbers 1 to 9 are already filled values.

Each possible (row, column, digit) combination is represented as a
Boolean variable. The Sudoku rules are converted into SAT clauses:
- Every cell must contain one digit from 1 to 9
- A cell cannot contain more than one digit
- Each digit appears only once in every row
- Each digit appears only once in every column
- Each digit appears only once in each 3x3 subgrid

The given numbers in the input grid are added as fixed constraints.

All clauses are added to a CNF formula and solved using a SAT solver.
If the problem is satisfiable, the solver’s output is decoded to build
the solved Sudoku grid.

If no solution exists, the function returns an empty list.
