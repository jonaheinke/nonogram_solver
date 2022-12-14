"""
	If you just want to see the algorithm used, see lines 55 to 234.
"""

__all__ = ["NonogramSolver"]



# -------------------------------------------------------------------------------------------------------------------- #
#                                                        IMPORTS                                                       #
# -------------------------------------------------------------------------------------------------------------------- #

import os, time, argparse, profile, pstats
from multiprocessing import Pool, Queue
from typing import Union, Callable
from collections.abc import Iterator

os.environ["NUMPY_EXPERIMENTAL_ARRAY_FUNCTION"] = "0" #implement_array_function takes much time (see profiler): https://stackoverflow.com/questions/61983372/is-built-in-method-numpy-core-multiarray-umath-implement-array-function-a-per
import numpy as np

from nonogram import Nonogram, EMPTY, CROSS, BOX



# -------------------------------------------------------------------------------------------------------------------- #
#                                             RUN-LENGTH-ENCODING FUNCTIONS                                            #
# -------------------------------------------------------------------------------------------------------------------- #

def rle(array: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
	#from: https://stackoverflow.com/a/69693227
	n = len(array)
	if n == 0:
		values = np.empty(0, dtype = array.dtype)
		lengths = np.empty(0, dtype = np.ubyte)
	else:
		positions = np.concatenate([[-1], np.nonzero(array[1:] != array[:-1])[0], [n - 1]])
		lengths = positions[1:] - positions[:-1]
		values = array[positions[1:]]
	return values, lengths

def rle_box_lengths(array: np.ndarray) -> list[int]:
	return [l for v, l in zip(*rle(array)) if v == BOX]

def rle_between_crosses(array: np.ndarray) -> list[int]:
	result = []
	for value in zip(array + [None], [None] + array):
		if value == CROSS:
			result.append(0)
		elif i == 0 or array[i - 1] == CROSS:
			result.append(1)
		else:
			result[-1] += 1



# -------------------------------------------------------------------------------------------------------------------- #
#                                                 NONOGRAMMSOLVER CLASS                                                #
# -------------------------------------------------------------------------------------------------------------------- #

class NonogramSolver:
	"""This class solves a nonogram puzzle using a multiplicity of methods.
	
	Attributes:
		dimensions (tuple): The dimensions of the nonogram puzzle.
		board (np.ndarray^2): The nonogram puzzle (0 == empty, 1 == cross, 2 == box).
	"""
	MAX_DEPTH = 4

	def __init__(self, from_board_or_filename: Union[Nonogram, str, bytes, os.PathLike]):
		"""Reads the input file and initializes the nonogram puzzle."""
		self.__start_time = self.__end_time = time.perf_counter_ns()
		self.__waiting_message_shown = False
		if isinstance(from_board_or_filename, Nonogram):
			self.nonogram = from_board_or_filename
		else:
			self.nonogram = Nonogram(from_board_or_filename)
		#self.nonogram.assert_correctness()
	

	
	# ---------------------------------------------------- PROCESSING ---------------------------------------------------- #
	@staticmethod
	def __min_number_width(numbers: Union[np.ndarray, list, tuple]) -> int:
		"""Calculates the minimum required length of an array of numbers on a hypothetical puzzle board.\n
		Examples:
		- [6] -> 6
		- [1, 4] -> 6
		- [3, 1, 1] -> 7"""
		return 0 if len(numbers) == 0 else np.sum(numbers) + len(numbers) - 1
	
	@staticmethod
	def __check_line_solvability(numbers: list[int], line: np.ndarray) -> bool:
		if not numbers:
			return True
		if line.size == 0 or NonogramSolver.__min_number_width(numbers) > line.size:
			return False
		"""
		lengths = rle_box_lengths(line)
		if not lengths:
			return True
		i = 0
		for number in numbers:
			remaining_space = number
			while remaining_space > 0:
				if i == len(lengths):
					return True
				if lengths[i] <= number:
					remaining_space -= lengths[i] + 1
					i += 1
				else:
					break
		return False
		"""
		def idk(numbers: list[int], line: np.ndarray) -> bool:
			i = 0
			for number in numbers:
				position = NonogramSolver.__get_first_possible_position(number, line, i)
				if position == -1:
					return False
				i = position + number + 1
			return True
		
		#print("Vorw??rts: ", idk(numbers, line))
		#print("R??ckw??rts:", idk(reversed(numbers), line[::-1]))
		return idk(numbers, line) and idk(reversed(numbers), line[::-1])
		#try fitting from reverse is necessary because some of the following nonassigned boxgroups can prevent the fitting of the last number(s)
		#(1, 2), [ ??  ???????]
	
	@staticmethod
	def __check_board_solvability(nonogram: Nonogram) -> bool:
		#print("Row solvability:")
		#print([NonogramSolver.__check_line_solvability(numbers, line) for numbers, line in zip(nonogram.row_numbers, nonogram.board)])
		#print("Column solvability:")
		#print([NonogramSolver.__check_line_solvability(numbers, line) for numbers, line in zip(nonogram.column_numbers, nonogram.board.T)])
		return all(NonogramSolver.__check_line_solvability(numbers, line) for numbers, line in zip(nonogram.row_numbers, nonogram.board)) and all(NonogramSolver.__check_line_solvability(numbers, line) for numbers, line in zip(nonogram.column_numbers, nonogram.board.T))
	
	@staticmethod
	def __check_board_solved(nonogram: Nonogram) -> bool:
		if np.any(nonogram.board == EMPTY):
			return False
		return NonogramSolver.__check_board_solvability(nonogram)
	
	@staticmethod
	def __find_next_box(line: np.ndarray, line_start_at: int = 0) -> int:
		"""Finds the next box in a line."""
		try:
			position = np.where(line[line_start_at:] == BOX)[0][0] + line_start_at
		except IndexError:
			return len(line) + 1
		return position

	@staticmethod
	def __get_all_possible_positions(number: int, line: np.ndarray, line_start_at: int = 0) -> Iterator[int]:
		condition = lambda i: np.all(line[i:i+number] != CROSS) and not (i + number < len(line) and line[i+number] == BOX) and not (i > 0 and line[i-1] == BOX)
		indecies = range(line_start_at, min(len(line) - number, NonogramSolver.__find_next_box(line, line_start_at)) + 1)
		yield from filter(condition, indecies)

	@staticmethod
	def __get_first_possible_position(number: int, line: np.ndarray, line_start_at: int = 0) -> int:
		"""Returns the first possible position of a number inside a (possibly filled) line. Returns -1 if no position is available.\n
		Examples:
		- 1, '?? ?????' -> 1
		- 2, ' ?????  ??' -> 2"""
		return next(NonogramSolver.__get_all_possible_positions(number, line, line_start_at), -1)

	@staticmethod
	def __get_permutations(numbers: list[int], line: np.ndarray, numbers_start_at: int = 0, line_start_at: int = 0) -> Iterator[np.ndarray]:
		if numbers_start_at >= len(numbers):
			yield line
			return
		number = numbers[numbers_start_at]
		#try to position the block at every available position
		for i in NonogramSolver.__get_all_possible_positions(number, line, line_start_at):
			temp = line.copy()
			temp[i:i+number] = BOX
			if i > 0:
				temp[line_start_at:i] = CROSS
			if i + number < len(line) and temp[i+number] != BOX:
				temp[i+number] = CROSS	
			#if not NonogramSolver.__check_line_solvability(numbers, temp):
			#	continue
			yield from NonogramSolver.__get_permutations(numbers, temp, numbers_start_at + 1, i + number + 1)

	"""
	@staticmethod
	def __get_permutations(numbers: list[int], line: np.ndarray, numbers_start_at: int = 0, line_start_at: int = 0) -> Iterator[np.ndarray]:
		if numbers_start_at >= len(numbers):
			yield line
			return
		number = numbers[numbers_start_at]
		#try to position the block at every available position
		for i in range(line_start_at, len(line) - number + 1):
			#abort if a block got jumped over
			if np.any(line[line_start_at:i] == BOX):
				return #TODO: Is returning here correct?
			#check if the spot is available
			if np.all(line[i:i+number] != CROSS):
				#check if the spot is followed by a box
				if i + number < len(line) and line[i+number] == BOX:
					continue
				temp = line.copy()
				temp[i:i+number] = BOX

				if not NonogramSolver.__check_line_solvability(numbers, temp):
					continue
				if i > 0:
					#temp[start_at:i] = CROSS
					temp[i-1] = CROSS
				if i + number < len(line) and temp[i+number] != BOX:
					temp[i+number] = CROSS
				
				yield from NonogramSolver.__get_permutations(numbers, temp, numbers_start_at + 1, i + number)
	"""

	@staticmethod
	def __solve_line(numbers: list[int], line: np.ndarray) -> set[int]:
		"""Solves a single row or column of the nonogram puzzle."""
		permutations = list(NonogramSolver.__get_permutations(numbers, line))
		if not permutations:
			return set()
		transposed_stack = np.column_stack(permutations)
		changed_indeces = set()
		for i, cell_permutations in enumerate(transposed_stack):
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

		#if all boxes are placed, fill the rest with crosses
		if rle_box_lengths(line) == numbers:
			indeces = (line == EMPTY).nonzero()[0]
			line[line == EMPTY] = CROSS
			changed_indeces.update(indeces)
		return changed_indeces
	
	@staticmethod
	def __solve_permutation(nonogram: Nonogram, time_update_callback: Callable = lambda *_: None) -> bool:
		#add every row and column to the queue
		row_queue    = set(range(len(nonogram.row_numbers)))
		column_queue = set(range(len(nonogram.column_numbers)))
		while not nonogram.is_solved():
			time_update_callback()
			#if the queues are empty the puzzle is unsolvable with the permutation method
			if not row_queue and not column_queue:
				break
			#try to solve every row that got updated (and is because of that in the row_queue)
			for row in row_queue.copy():
				row_queue.remove(row)
				changed_indeces = NonogramSolver.__solve_line(nonogram.row_numbers[row], nonogram.board[row])
				for index in changed_indeces:
					if not list(next(NonogramSolver.__get_permutations(nonogram.column_numbers[index], nonogram.board[:, index]), [])):
						return False
				column_queue.update(changed_indeces)
			#try to solve every column that got updated (and is because of that in the column_queue)
			for column in column_queue.copy():
				column_queue.remove(column)
				#if not NonogramSolver.__check_line_solvability(nonogram.column_numbers[column], nonogram.board[:, column]):
				#	return False
				changed_indeces = NonogramSolver.__solve_line(nonogram.column_numbers[column], nonogram.board[:, column])
				for index in changed_indeces:
					if not list(next(NonogramSolver.__get_permutations(nonogram.row_numbers[index], nonogram.board[index]), [])):
						return False
				row_queue.update(changed_indeces)

	@staticmethod
	def __solve_disproof_cell(idx: int, nonogram: Nonogram, time_update_callback: Callable = lambda *_: None, depth: int = 1) -> bool:
		pass
	#terminate complete pool
	#pool.close()
	#pool.terminate()
	#pool.join()
	
	@staticmethod
	def __solve_disproof(nonogram: Nonogram, time_update_callback: Callable = lambda *_: None, depth: int = 1) -> bool:
		if depth == 0:
			return nonogram.is_solved()
		for (i, j), value in np.ndenumerate(nonogram.board):
			if value == EMPTY:
				#print(f"depth: {depth}, indeces: {i}-{j}".ljust(40))
				contradiction = [False, False]
				#try setting a box and a cross
				for k, target_value in enumerate((BOX, CROSS)):
					#copy nonogram board, so that the original isn't overwritten
					temp = nonogram.copy()
					#set assumption
					temp.board[i][j] = target_value
					#try to solve without further assumptions
					NonogramSolver.__solve_permutation(temp, time_update_callback)
					"""print("completed squares:", len((temp.board != EMPTY).nonzero()[0]), "     ")"""
					#if the puzzle could be solved without further assumptions, the initial assumption was correct
					if NonogramSolver.__check_board_solved(temp):
						#nonogram = temp
						nonogram.board = temp.board
						return True
					#otherwise if the puzzle is not solvable with the assumption, the assumption was wrong
					if not NonogramSolver.__check_board_solvability(temp):
						#found a contradiction
						contradiction[k] = True
						continue
					#otherwise try to solve with further assumptions recursively
					if NonogramSolver.__solve_disproof(temp, time_update_callback, depth - 1):
						#nonogram = temp
						nonogram.board = temp.board
						return True
				#if both assumptions were wrong, the puzzle is unsolvable at this point (in upper recursion depths it still might be solvable)
				if contradiction[0] and contradiction[1]:
					#print("both assumptions wrong".ljust(40))
					return False
				#otherwise the cell's value is forced
				if contradiction[0] or contradiction[1]:
					#print("forced value".ljust(40))
					nonogram.board[i][j] = CROSS if contradiction[0] else BOX
					if NonogramSolver.__solve_permutation(nonogram, time_update_callback):
						#after finding an assumption that works, it was solvable without further assumptions
						return True
					if NonogramSolver.__solve_disproof(nonogram, time_update_callback, depth):
						return True
				#else: no conclusive assumption could be made for this cell
				#print("no conclusive assumption".ljust(40))
		#print("default false".ljust(40))
		return False

	def solve(self, print_elapsed_time = False, depth: int = 1) -> bool:
		"""Solves the nonogram puzzle. Allows printing the elapsed time."""
		self.__start_time = time.perf_counter_ns()
		function_ = self.__update_elapsed_time if print_elapsed_time else lambda *_: None
		self.__solve_permutation(self.nonogram, function_)
		try:
			self.__solve_disproof(self.nonogram, function_, min(depth, NonogramSolver.MAX_DEPTH))
		except RecursionError:
			print()
			print("Maximum recursion depth reached."*5)
			return False
		if print_elapsed_time:
			self.__update_elapsed_time(True)
		return self.nonogram.is_solved()
	
	def __str__(self) -> str:
		return str(self.nonogram)
	


	# ------------------------------------------------------ OUTPUT ------------------------------------------------------ #
	def __print_time(self, time: float, newline = True) -> str:
		print(f"Time elapsed: {(time - self.__start_time) / 1e9:11.6f} seconds", end = "\r\n" if newline else "\r")

	def __update_elapsed_time(self, final_update = False):
		"""Updates the current elapsed time shown in the console."""
		#if print_elapsed_time:
		if final_update:
			self.__end_time = time.perf_counter_ns()
			self.print_time()
		else:
			#If more than five seconds elapsed, show a message.
			if not self.__waiting_message_shown and time.perf_counter_ns() - self.__start_time > 10e9:
				self.__waiting_message_shown = True
				print("Please be patient, solving nonograms is in fact an NP-complete problem. ????")
			self.__print_time(time.perf_counter_ns(), False)
	
	def print_time(self):
		"""Prints the elapsed time."""
		self.__print_time(self.__end_time)



# -------------------------------------------------------------------------------------------------------------------- #
#                                                         MAIN                                                         #
# -------------------------------------------------------------------------------------------------------------------- #

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Solves nonogram puzzles, even the really hard ones.")
	parser.add_argument("dataset", help = "CSV file")
	parser.add_argument("-t", "--time",  dest = "time", action = "store_true", help = "prints the elapsed time")
	parser.add_argument("-d", "--depth", dest = "depth", type = int, choices = range(NonogramSolver.MAX_DEPTH + 1), default = 1, help = "assumption depth")
	parser.add_argument("-p", "--profiler", dest = "profiler", action = "store_true", help = "writes performance profile to profile.txt")
	args = parser.parse_args()

	solved = False
	try:
		nonogram = NonogramSolver(args.dataset)
		if args.profiler:
			profile.run("solved = nonogram.solve(args.time, args.depth)", "profile.temp")
		else:
			solved = nonogram.solve(args.time, args.depth)
	except KeyboardInterrupt:
		print() #newline, otherwise elapsed time is overwritten
		solved = False

	if solved:
		print("Solved nonogram:")
	else:
		print("Unfinished nonogram:")
	print(nonogram)

	if args.profiler:
		with open("profile.txt", "w") as f:
			pstats.Stats("profile.temp", stream = f).sort_stats("time").print_stats()
			try:
				os.remove("profile.temp")
			except FileNotFoundError:
				pass