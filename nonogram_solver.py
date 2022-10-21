"""
	If you just want to see the algorithm used, see lines 175 to 298.
"""



# -------------------------------------------------------------------------------------------------------------------- #
#                                                        IMPORTS                                                       #
# -------------------------------------------------------------------------------------------------------------------- #

import os, time, argparse
from typing import Union, Callable, Generator

import numpy as np

from nonogram import Nonogram, EMPTY, CROSS, BOX
	


# -------------------------------------------------------------------------------------------------------------------- #
#                                                 NONOGRAMMSOLVER CLASS                                                #
# -------------------------------------------------------------------------------------------------------------------- #

class NonogramSolver:
	"""This class solves a nonogram puzzle using a multiplicity of methods.
	
	Attributes:
		dimensions (tuple): The dimensions of the nonogram puzzle.
		board (np.ndarray): The nonogram puzzle (0 = empty, 1 == cross, 2 == box).
	"""

	def __init__(self, from_board_or_filename: Union[Nonogram, str, bytes, os.PathLike]):
		"""Reads the input file and initializes the nonogram puzzle."""
		self.__start_time = self.__end_time = time.perf_counter_ns()
		self.__waiting_message_shown = False
		if isinstance(from_board_or_filename, Nonogram):
			self.nonogram = from_board_or_filename
		else:
			self.nonogram = Nonogram(from_board_or_filename)
		self.nonogram.assert_correctness()
	

	
	# ---------------------------------------------------- PROCESSING ---------------------------------------------------- #
	@staticmethod
	def __min_number_width(numbers: Union[np.ndarray, list, tuple]) -> int:
		"""Calculates the minimum required width of an array of numbers on a hypothetical puzzle board.\n
		Examples:
		- [6] -> 6
		- [1, 4] -> 6
		- [3, 1, 1] -> 7"""
		return 0 if len(numbers) == 0 else np.sum(numbers) + len(numbers) - 1
	
	@staticmethod
	def rle(array: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
		#from: https://stackoverflow.com/a/69693227
		n = len(array)
		if n == 0:
			values = np.empty(0, dtype = array.dtype)
			lengths = np.empty(0, dtype = np.int_)
		else:
			positions = np.concatenate([[-1], np.nonzero(array[1:] != array[:-1])[0], [n - 1]])
			lengths = positions[1:] - positions[:-1]
			values = array[positions[1:]]
		return values, lengths
	
	@staticmethod
	def __check_line_validity(numbers: list[int], line: np.ndarray) -> bool:
		#Checks if the numbers fit between the start and end index in the line.
		if NonogramSolver.__min_number_width(numbers) > line.size:
			return False
		lengths = [l for v, l in zip(*NonogramSolver.rle(line)) if v == BOX]

	
	@staticmethod
	def __check_line_solvability(numbers: list[int], line: np.ndarray) -> bool:
		raise NotImplementedError
	
	@staticmethod
	def __check_line_completeness(numbers: list[int], line: np.ndarray) -> bool:
		return np.all(line != EMPTY) and NonogramSolver.__check_line_validity(numbers, line)
	
	@staticmethod
	def __get_permutations(numbers: list[int], line: np.ndarray, start_at: int = 0) -> Generator[np.ndarray, None, None]:
		if not numbers:
			yield line
			return
		number = numbers[0]
		"""
		print("execute __get_permutations")
		print("\tcurrent number:", number)
		print("\tline:", line)"""
		#try to position the block at every available position
		for i in range(start_at, len(line) - number + 1):
			#abort if a block got jumped over
			if np.any(line[start_at:i] == BOX):
				return
			#check if the spot is available
			if np.all(line[i:i+number] != CROSS):
				#check if the spot is followed by a box
				if i + number < len(line) and line[i+number] == BOX:
					continue
				temp = line.copy()
				temp[i:i+number] = BOX
				if i > 0:
					#temp[start_at:i] = CROSS
					temp[i-1] = CROSS
				if i + number < len(line) and temp[i+number] != BOX:
					temp[i+number] = CROSS
				
				yield from NonogramSolver.__get_permutations(numbers[1:], temp, i + number)
	
	@staticmethod
	def get_permutations(*args):
		#TODO: implement sanity checks
		return NonogramSolver.__get_permutations(*args)

	@staticmethod
	def __solve_line(numbers: list[int], line: np.ndarray) -> set[int]:
		"""Solves a single row or column of the nonogram puzzle."""
		#TODO FIXME: this adds the index i for every cell to the set, so the logic doesn't quite check out
		permutations = list(NonogramSolver.__get_permutations(numbers, line))
		if not permutations:
			return set()
		transposed_stack = np.column_stack(permutations)
		changed_indeces = set()
		for i, cell_permutations in enumerate(transposed_stack):
			"""
			cells_are_boxes = np.equal(cell_permutations == BOX)
			if np.all(cells_are_boxes): #np.all(cell_permutations, BOX)
				line[i] = BOX
			elif np.any(cells_are_boxes): #np.any(cell_permutations == BOX)
				line[i] = EMPTY
			else:
				line[i] = CROSS
			"""
			#TODO: integrate this function
			#cell in all permutations:
			#- all empty -> cross
			#- all box -> box
			#- all cross -> cross
			#- has some box -> empty
			#- has some cross but no box -> cross

			#only modify/check empty cells
			if line[i] == EMPTY:
				if np.all(cell_permutations == BOX):
					line[i] = BOX
					changed_indeces.add(i)
				elif not np.any(cell_permutations == BOX):
					line[i] = CROSS
					changed_indeces.add(i)

		return changed_indeces
	
	@staticmethod
	def __solve_permutation(nonogram: Nonogram, time_update_callback: Callable = lambda *_: None) -> bool:
		#add every row and column to the queue
		row_queue    = set(range(len(nonogram.row_numbers)))
		column_queue = set(range(len(nonogram.column_numbers)))
		while not nonogram.is_solved():
			#print("row_queue:", row_queue)
			#print("column_queue:", column_queue)
			#if the queues are empty the puzzle is unsolvable with the permutation method
			if not row_queue and not column_queue:
				print("Well, this is awkward. The puzzle is not solvable.")
				break
			#try to solve every row that got updated (and is because of that in the row_queue)
			for row in row_queue.copy():
				time_update_callback() #self.__update_elapsed_time()
				row_queue.remove(row)
				changed_indeces = NonogramSolver.__solve_line(nonogram.row_numbers[row], nonogram.board[row])
				column_queue.update(changed_indeces)
				#print("added", changed_indeces, "to column_queue")
			#try to solve every column that got updated (and is because of that in the column_queue)
			for column in column_queue.copy():
				time_update_callback() #self.__update_elapsed_time()
				column_queue.remove(column)
				changed_indeces = NonogramSolver.__solve_line(nonogram.column_numbers[column], nonogram.board[:, column])
				row_queue.update(changed_indeces)
				#print("added", changed_indeces, "to row_queue")
			#time.sleep(1.0)
	
	@staticmethod
	def __solve_disproof(nonogram: Nonogram, time_update_callback: Callable = lambda *_: None, depth: int = 1) -> bool:
		#for every cell:
		#	if it is empty, mark it is a box and try solving
		for i, j in np.ndenumerate(nonogram.board):
			time_update_callback()
			if nonogram.board[i][j] == EMPTY:
				temp = nonogram.copy()
				temp.board[i][j] = BOX
				NonogramSolver.__solve_permutation(temp, time_update_callback)
				if temp.is_solved():
					nonogram = temp
					return True
				elif depth > 1:
					solved = NonogramSolver.__solve_disproof(temp, time_update_callback, depth - 1)
					nonogram = temp
					return solved
		return False

	def solve(self, print_elapsed_time = False) -> bool:
		"""Solves the nonogram puzzle. Allows printing the elapsed time."""
		self.__start_time = time.perf_counter_ns()
		self.__update_elapsed_time()
		self.__solve_permutation(self.nonogram, self.__update_elapsed_time)
		self.__update_elapsed_time()
		#self.__solve_disproof(self.nonogram, self.__update_elapsed_time, 1)
		self.__update_elapsed_time(True)
		return self.nonogram.is_solved()
		if not self.nonogram.is_solved():
			print("Calculating via disproof method...")
			board: Nonogram = self.nonogram.copy()
			board.assert_correctness()
			for indeces, value in np.ndenumerate(board):
				self.__update_elapsed_time()
				if value == EMPTY:
					for v in (BOX, CROSS):
						board[indeces[0]][indeces[1]] = v
						self.__solve_permutation(board, self.__update_elapsed_time)
						if board.is_solved():
							self.nonogram = board
							break
					else:
						continue
					break
			else:
				pass #unsolvable puzzle, not even trying out every empty cell comes to a solution
		self.__update_elapsed_time(True)
	
	def __str__(self) -> str:
		return str(self.nonogram)
	


	# ------------------------------------------------------ OUTPUT ------------------------------------------------------ #
	def __update_elapsed_time(self, final_update = False):
		"""Updates the current elapsed time shown in the console."""
		#if print_elapsed_time:
		if final_update:
			self.__end_time = time.perf_counter_ns()
			print(f"Time elapsed: {(self.__end_time - self.__start_time) / 1e9:10.6f} seconds")
		else:
			#If more than five seconds elapsed, show a message.
			if not self.__waiting_message_shown and time.perf_counter_ns() - self.__start_time > 5e9:
				self.__waiting_message_shown = True
				print("Please be patient, solving nonograms is in fact an NP-complete problem. 😄")
			print(f"Time elapsed: {(time.perf_counter_ns() - self.__start_time) / 1e9:10.6f} seconds", end = "\r")
	
	def print_time(self):
		"""Prints the elapsed time."""
		print(f"Time elapsed: {(self.__end_time - self.__start_time) / 1e9:.6f} seconds")



# -------------------------------------------------------------------------------------------------------------------- #
#                                                         MAIN                                                         #
# -------------------------------------------------------------------------------------------------------------------- #
"""
line = np.array([EMPTY] * 8)
print(line)
perm = list(NonogramSolver.get_permutations([2, 4], line))
print()
print("Result:")
print(perm)

exit()
"""
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Process datasets with optional video overlay.")
	parser.add_argument("dataset", help = "CSV file")
	parser.add_argument("-t", "--time", dest = "time", action = "store_true", help = "prints the elapsed time")
	args = parser.parse_args()

	try:
		nonogram = NonogramSolver(args.dataset)
		nonogram.solve(True)
	except KeyboardInterrupt:
		print() #newline, otherwise elapsed time is overwritten
		print("Unfinished nonogram:")
	else:
		print("Solved nonogram:")
	print(nonogram)