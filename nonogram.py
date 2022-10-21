# -------------------------------------------------------------------------------------------------------------------- #
#                                                        IMPORTS                                                       #
# -------------------------------------------------------------------------------------------------------------------- #

import os, re
from itertools import zip_longest
from typing import Union

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
					if value.strip() and int(value) > 0:
						column.append(int(value))
			else:
				result.append([int(value) for value in separated_values if value.strip() and int(value) > 0])
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
				elif cell == CROSS:
					result += "\033[0;37;40m X " #X
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