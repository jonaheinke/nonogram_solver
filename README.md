# Nonogram Solver

[![license](https://img.shields.io/github/license/jonaheinke/nonogram_solver)](LICENSE)
[![last commit](https://img.shields.io/github/last-commit/jonaheinke/nonogram_solver)](https://github.com/jonaheinke/nonogram_solver/commit)
[![open issues](https://img.shields.io/github/issues/jonaheinke/nonogram_solver)](https://github.com/jonaheinke/nonogram_solver/issues)
[![code size](https://img.shields.io/github/languages/code-size/jonaheinke/nonogram_solver)](#)
[![example count](https://img.shields.io/github/directory-file-count/jonaheinke/nonogram_solver/example_files?label=example%20nonograms&type=file&extension=csv)](example_files/)
[![used libraries](https://img.shields.io/badge/used%20libraries-numpy-013243)](#)

This Python project is a **puzzle solver** for the popular japanese **Nonograms**. They are also known as Hanjie, Paint by Numbers, Picross, Griddlers and Pic-a-Pix. I recommend reading the corresponding [Wikipedia article on Nonograms](https://en.wikipedia.org/wiki/Nonogram). It explains very well how to solve them by hand.

This program is superior to other nonogram solvers because it can solve way more nonograms. In perticular those, in which you have to make an assumption and prove or disprove it. No other nonogram solver to my knowledge can solve those.

There are plenty of examples in the `example_files` folder, hand-solved solutions and their transcriptions. Some of them are marked `hard` which cannot be solved with traditional methods.

## Current stage of development

It can currently solve any nonogram without assumptions. But that is not really useful, because you can solve those by hand.
I don't know why but it can't solve nonograms with assumptions for the life of it.

## Usage

### Commandline

```bash
$ git clone https://github.com/jonaheinke/nonogram_solver.git
$ pip install numpy
$ python nonogram_solver.py example_files/example2.csv
```

### File input

You should write the row and column numbers into a [CSV file](https://en.wikipedia.org/wiki/Comma-separated_values) delimited by `","`, `";"` or `"|"`.

First you write the column numbers.

It is followed by a seperator line which contains at least one character that is not a number, space, tab or allowed delimiter.

Last you write the row numbers.

You can leave unused cells out or empty or use spaces so the number clusters look more like a complete matrix.

If it is not clear by now, look at the examples in the `example_files` folder.

Call the program with the path to the [CSV file](https://en.wikipedia.org/wiki/Comma-separated_values) described under Commandline Usage.

## Used strategies

### Permutation method

### Disproof method

\
*Copyright (c) 2022 Jona Heinke under MIT License, see [LICENSE](LICENSE) for more information.*