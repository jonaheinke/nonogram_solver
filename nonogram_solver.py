"""
	If you just want to see the algorithm used, see lines 176 to 278.
"""



# -------------------------------------------------------------------------------------------------------------------- #
#                                                        IMPORTS                                                       #
# -------------------------------------------------------------------------------------------------------------------- #

import os, time, re, argparse
from itertools import zip_longest
from typing import Generator, Union, Callable
import numpy as np



ALPHABET_SIZE = 3
EMPTY, CROSS, BOX = range(ALPHABET_SIZE)



# -------------------------------------------------------------------------------------------------------------------- #
#                                                      BOARD CLASS                                                     #
# -------------------------------------------------------------------------------------------------------------------- #

class Nonogram:
	"""
	
	Attributes:
		board (np.ndarray): The nonogram puzzle (0 == empty, 1 == cross, 2 == box).
		row_numbers
		column_numbers
	"""
	def __read_matrix(self, lines: list[str], column_major: bool) -> list[list[int]]:
		result = []
		for line in lines:
			line = line.strip()
			separated_values = re.split(r"[\|,;]", line) #list(filter(lambda x: x.strip() != "", line.split(",")))
			if column_major:
				#if there are more items than currently detected, add some more lists
				if len(separated_values) > len(result):
					result.extend([] for _ in range(len(separated_values) - len(result)))
				#add the values to the lists
				for value, column in zip(separated_values, result):
					if value and int(value) > 0:
						column.append(int(value))
			else:
				result.append([int(value) for value in separated_values if value and int(value) > 0])
		return result

	def __init__(self, file: Union[str, bytes, os.PathLike, None], dimensions: Union[tuple[int, int], None] = None):
		self.board: np.ndarray[np.ndarray[int]]
		self.__correctly_read = False
		if file is None:
			self.board = np.zeros(dimensions, np.ubyte)
		else:
			try:
				with open(file, "r") as f:
					#column_dimensions, self.column_numbers = self.__read_number_block_from_file(f)
					#row_dimensions,    self.row_numbers    = self.__read_number_block_from_file(f)
					lines = f.readlines()
					#find the separator line
					index = next(i for i, line in enumerate(lines) if re.search(r"[^\d\s\t\|,;]", line))
					if index == 0:
						raise IndexError
					self.column_numbers = self.__read_matrix(lines[:index], True)
					self.row_numbers = self.__read_matrix(lines[index + 1:], False)
			except OSError:
				print("File not found. Please enter a valid filename.")
				return
			except StopIteration:
				print("Separator could not be found. Please check the file for validity.")
				return
			except IndexError:
				print("At least one table is empty. Please add it to the file.")
				return
			except ValueError:
				print("Unknown characters found. Please check the file for validity.")
				return
		self.board = np.zeros((len(self.row_numbers), len(self.column_numbers)), np.ubyte)
		#self.board = np.random.randint(0, 2, (10, 10), dtype = np.ubyte) #randomize board
		#print("Test output:")
		#print(self.column_numbers)
		#print(self.row_numbers)
		self.__correctly_read = self.board_valitity()
	
	def __repr__(self) -> str:
		return "Nonogram Puzzle (%dx%d)".format(*self.board.shape)
	
	def __str__(self) -> str:
		result = ""
		longest_row_length = max(len(row) for row in self.row_numbers)
		left_spacing = longest_row_length * 3
		for row in zip_longest(*self.column_numbers, fillvalue = " " * 3):
			result += " " * (left_spacing + 1) + "".join(str(n).center(3) for n in row) + "\n"
		result += " " * left_spacing + "┌" + "───"*self.board.shape[1] + "┐\n" #top bar
		#https://stackabuse.com/how-to-print-colored-text-in-python/
		for row_numbers_row, board_row in zip(self.row_numbers, self.board):
			if row_numbers_row == []:
				row_numbers_row = [0]
			result += "".join(str(n).center(3) for n in row_numbers_row).rjust(left_spacing) + "│" #left bar
			for cell in board_row:
				if cell == BOX:
					result += "\033[0;37;47m   " #white square
				else:
					result += "\033[0;37;40m   " #black square
			result += "\033[0;37;40m│\n" #color reset, right bar and newline
		result += " " * left_spacing + "└" + "───"*self.board.shape[1] + "┘\n" #bottom bar
		return result
	
	def __eq__(self, __o: object) -> bool:
		return isinstance(__o, Nonogram) and (self.board == __o.board).all() and self.row_numbers == __o.row_numbers and self.column_numbers == __o.column_numbers
	
	def copy(self):
		return Nonogram(None, (self.board.shape))

	@classmethod
	def from_board():
		pass

	def import_board(self, board):
		pass

	def assert_correctness(self):
		"""Prevents the program from running if the input file was not read correctly."""
		if not self.__correctly_read:
			print("The data was not correctly read. Please check for file validity and try again.")
			exit(1)
	
	def board_valitity(self) -> bool:
		"""Checks if the board is valid."""
		if (len(self.row_numbers), len(self.column_numbers)) != self.board.shape:
			print("Board size error")
			return False
		if not np.all(self.board < ALPHABET_SIZE):
			print("Board filled with invalid values")
			return False
		return True
	
	def is_solved(self) -> bool:
		return np.all(self.board != EMPTY)
	
	def get_row(self, n: int) -> np.ndarray: #TODO: check type
		return self.board[n]
	
	def get_column(self, n: int) -> np.ndarray: #TODO: check type
		return self.board[:, n]
		


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
	def __fits_between_indeces(numbers: list[int], line: np.ndarray) -> bool:
		"""Checks if the numbers fit between the start and end index in the line."""
		if NonogramSolver.__min_number_width(numbers) > line.size:
			return False
	
	@staticmethod
	def rle(line: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
		#from: https://stackoverflow.com/a/69693227
		n = len(line)
		if n == 0:
			values = np.empty(0, dtype = line.dtype)
			lengths = np.empty(0, dtype = np.int_)
		else:
			positions = np.concatenate([[-1], np.nonzero(line[1:] != line[:-1])[0], [n - 1]])
			lengths = positions[1:] - positions[:-1]
			values = line[positions[1:]]
		return values, lengths
	
	@staticmethod
	def __check_line_validity(numbers: list[int], line: np.ndarray) -> bool:
		raise NotImplementedError
	
	@staticmethod
	def __get_permutations(numbers: list[int], line: np.ndarray) -> Generator[np.ndarray, None, None]:
		if not numbers:
			yield line
			return
		number = numbers[0]
		for i in range(len(line) - number):
			if np.all(line[i:i+number] != CROSS):
				temp = line.copy()
				temp[i:i+number] = BOX
				if i > 0:
					temp[i - 1] = CROSS
				if i + number < len(line):
					temp[i + number] = CROSS
				yield from NonogramSolver.__get_permutations(numbers[1:], line[i+number:])

	@staticmethod
	def __solve_line(numbers: list[int], line: np.ndarray) -> set[int]:
		"""Solves a single row or column of the nonogram puzzle."""
		#TODO FIXME: this adds the index i for every cell to the set, so the logic doesn't quite check out
		changed_indeces = set()
		permutations = np.array(list(NonogramSolver.__get_permutations(numbers, line)), dtype = np.ubyte, order = "F")
		for i, cell_permutations in enumerate(permutations):
			cells_are_boxes = np.equal(cell_permutations == BOX)
			if np.all(cells_are_boxes): #np.all(cell_permutations, BOX)
				line[i] = BOX
			elif np.any(cells_are_boxes): #np.any(cell_permutations == BOX)
				line[i] = EMPTY
			else:
				line[i] = CROSS
			changed_indeces.add(i)
		#TODO: integrate this function
		#cell in all permutations:
		#- all empty -> cross
		#- all box -> box
		#- all cross -> cross
		#- has some box -> empty
		#- has some cross but no box -> cross
		return changed_indeces
	
	@staticmethod
	def __solve_permutation(nonogram: Nonogram, time_update_callback: Callable = lambda *_: None):
		#add every row and column to the queue
		row_queue    = set(range(len(nonogram.row_numbers)))
		column_queue = set(range(len(nonogram.column_numbers)))
		while not nonogram.is_solved():
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
			#try to solve every column that got updated (and is because of that in the column_queue)
			for column in column_queue.copy():
				time_update_callback() #self.__update_elapsed_time()
				column_queue.remove(column)
				changed_indeces = NonogramSolver.__solve_line(nonogram.column_numbers[column], nonogram.board[:, column])
				row_queue.update(changed_indeces)

	def solve(self, print_elapsed_time = False):
		"""Solves the nonogram puzzle. Allows printing the elapsed time."""
		#print("Calculating via permutation method...")
		self.__start_time = time.perf_counter_ns()
		for _ in range(4):
			time.sleep(1)
			self.__update_elapsed_time()
		self.__solve_permutation(self.nonogram, self.__update_elapsed_time)
		self.__update_elapsed_time(True)
		return
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

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Process datasets with optional video overlay.")
	parser.add_argument("dataset", help = "CSV file")
	parser.add_argument("-t", "--time", dest = "time", action = "store_true", help = "prints the elapsed time")
	args = parser.parse_args()

	nonogram = NonogramSolver(args.dataset)
	nonogram.solve(True)
	print("Solved nonogram:")
	print(nonogram)