import time
import numpy as np



class NonogramSolver:
	"""This class solves a nonogram puzzle using a multiplicity of methods."""

	@staticmethod
	def __read_number_block_from_file(f) -> tuple[tuple[int, int], np.ndarray]:
		dimensions = tuple(int(dim) for dim in f.readline().strip().split(","))
		result = []
		for _ in range(dimensions[0]):
			result.extend(f.readline().strip().split(","))
		#return (dimensions, np.array(f.readline().strip().split(",")).reshape(dimensions))
		return (dimensions, np.array(result).reshape(dimensions))

	def __init__(self, filename: str):
		"""Reads the input file and initializes the nonogram puzzle."""
		self.__correctly_read = False
		self.__start_time = self.__end_time = time.perf_counter_ns()
		self.solved = False

		try:
			with open(filename, "r") as f:
				column_dimensions, self.column_numbers = self.__read_number_block_from_file(f)
				row_dimensions,    self.row_numbers    = self.__read_number_block_from_file(f)
		except OSError:
			print("File not found. Please enter a valid filename.")
			return

		self.dimensions = (row_dimensions[0], column_dimensions[1]) #rows times columns
		#print(f"Dimensions: {self.dimensions[0]}x{self.dimensions[1]}")
		self.row_queue    = set(range(self.dimensions[0]))
		self.column_queue = set(range(self.dimensions[1]))

		#self.dimensions = (30, 30)
		self.board = np.zeros(self.dimensions, dtype = np.bool_)
		self.board = np.random.randint(0, 2, self.dimensions, dtype = np.bool_) #randomize board
		self.__correctly_read = True
	
	def __assert(self):
		"""Prevents the program from running if the input file was not read correctly."""
		if not self.__correctly_read:
			print("The data was not correctly read. Please check for file validity and try again.")
			exit(1)
	
	def __update_elapsed_time(self, final_update = False):
		"""Updates the current elapsed time shown in the console."""
		#if print_elapsed_time:
		if final_update:
			self.__end_time = time.perf_counter_ns()
			print(f"Time elapsed: {(self.__end_time - self.__start_time) / 1e9:2.6f} seconds")
		else:
			print(f"Time elapsed: {(time.perf_counter_ns() - self.__start_time) / 1e9:2.6f} seconds", end = "\r")

	def solve(self, print_elapsed_time = False):
		"""Solves the nonogram puzzle. Allows printing the elapsed time."""
		self.__assert()
		#print("Start calculations")
		self.__start_time = time.perf_counter_ns()

		self.__update_elapsed_time()
		#print("Calculating via permutation method...")
		#TODO
		#self.__update_elapsed_time()
		#time.sleep(0.5)
		#print("Calculating via disproof method...")
		#self.__update_elapsed_time()
		#time.sleep(2)
		#TODO
		self.__update_elapsed_time(True)

	def print_board(self):
		"""Prints the nonogram puzzle."""
		print("\033[0;37;40m┌" + "──"*self.board.shape[1] + "┐") #top bar
		#https://stackabuse.com/how-to-print-colored-text-in-python/
		for row in self.board:
			print("│", end = "") #left bar
			for cell in row:
				if cell:
					print("\033[0;37;47m  ", end = "") #white square
				else:
					print("\033[0;37;40m  ", end = "") #black square
			print("\033[0;37;40m│") #color reset, right bar and newline
		print("└" + "──"*self.board.shape[1] + "┘") #bottom bar
	
	def print_time(self):
		"""Prints the elapsed time."""
		print(f"Time elapsed: {(self.__end_time - self.__start_time) / 1e9:.6f} seconds")



if __name__ == "__main__":
	nonogram = NonogramSolver("example_input.csv")
	nonogram.solve(True)
	print("Solved board:" if nonogram.solved else "Unsolved board:")
	nonogram.print_board()
	#print()
	#nonogram.print_time()