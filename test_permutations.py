import numpy as np

from nonogram_solver import NonogramSolver
from nonogram import EMPTY, CROSS, BOX



line = np.array([EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, BOX, EMPTY, EMPTY, CROSS, BOX])
print(line)
perm = list(NonogramSolver.get_permutations([2, 1], line))
print()
print("Result:")
print(perm)