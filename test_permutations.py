import numpy as np

from nonogram_solver import NonogramSolver
from nonogram import EMPTY, CROSS, BOX


"""
line = np.array([EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, BOX, EMPTY, EMPTY, CROSS, BOX])
print(line)
perm = list(NonogramSolver.get_permutations([2, 1], line))
print()
print("Result:")
print(perm)
"""


def find_next_box(line: np.ndarray, line_start_at: int = 0) -> int:
	"""Finds the next box in a line."""
	try:
		position = np.where(line[line_start_at:] == BOX)[0][0] + line_start_at
	except IndexError:
		return len(line) + 1
	return position

def get_all_possible_positions(number: int, line: np.ndarray, line_start_at: int = 0):
	condition = lambda i: np.all(line[i:i+number] != CROSS) and not (i + number < len(line) and line[i+number] == BOX) and not (i > 0 and line[i-1] == BOX)
	indecies = range(line_start_at, min(len(line) - number, find_next_box(line, line_start_at)) + 1)
	yield from filter(condition, indecies)



line = np.array([EMPTY, EMPTY, EMPTY, CROSS, BOX, CROSS, EMPTY, EMPTY, EMPTY, EMPTY])
print(line)
print("Result:")
#print(NonogramSolver._NonogramSolver__check_line_solvability([1, 3], line))
print(list(NonogramSolver._NonogramSolver__get_all_possible_positions(3, line, 2)))