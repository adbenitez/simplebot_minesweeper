"""Game logic"""

import random
import time
from typing import Generator

import minesweeper

MINE = "M"
BOOM = "B"
FLAG = "X"
HIDDEN = "_"

CELLS = {
    MINE: "💣",
    BOOM: "💥",
    FLAG: "🚩",
    HIDDEN: "🔲",
    "0": "⬜",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
}
COLS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
ROWS = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮"]


class Board:
    def __init__(self, board: str = None) -> None:
        if board:
            lines = board.split("\n")
            self.date = float(lines.pop(0))
            board = lines.pop(0)
            self._board = [[board[i * 9 + j] for j in range(9)] for i in range(9)]
        else:
            self.date = time.time()
            my_generator = minesweeper.Generator(9, 9, mine_id=MINE)
            self._board = my_generator.generate_raw(random.randint(10, 20))
            for i, row in enumerate(self._board):
                for j, n in enumerate(row):
                    if n != MINE:
                        self._board[i][j] = HIDDEN

    def get_score(self, date: float) -> float:
        mines = 0
        for row in self._board:
            for cell in row:
                if cell == MINE:
                    mines += 1
        return round(mines / (date - self.date) * 10 ** 4, 2) or 1

    def export(self) -> str:
        board = str(self.date) + "\n"
        board += "".join("".join(row) for row in self._board)
        return board

    def __str__(self) -> str:
        text = "|".join(COLS) + "\n"
        for i, row in enumerate(self._board):
            for n in row:
                text += CELLS[n if n.isdigit() else HIDDEN]
                text += "|"
            text += ROWS[i] + "\n"
        return text

    def reveal(self, status: int) -> str:
        text = "|".join(COLS) + "\n"
        m = FLAG if status == 1 else MINE
        for i, row in enumerate(self._board):
            for n in row:
                text += CELLS[m if n == MINE else n]
                text += "|"
            text += ROWS[i] + "\n"
        return text

    @staticmethod
    def on_board(i: int, j: int) -> bool:
        if 0 <= i <= 8 and 0 <= j <= 8:
            return True
        return False

    def move(self, coords: str) -> None:
        sorted_coord = sorted(coords.lower())
        i = "abcdefghi".find(sorted_coord[1])
        j = "123456789".find(sorted_coord[0])

        if not self.on_board(i, j) or self._board[i][j] not in (HIDDEN, MINE):
            raise ValueError("Invalid move")

        self.show(i, j)

    def show(self, i: int, j: int) -> None:
        if self._board[i][j] == MINE:
            self._board[i][j] = BOOM
            return
        check = [(i, j)]
        while check:
            i, j = check.pop()
            cm = self.count_mines(i, j)
            self._board[i][j] = str(cm)
            if cm == 0:
                for row, col in self.get_dirs(i, j):
                    if self._board[row][col] == HIDDEN:
                        check.append((row, col))

    def count_mines(self, i: int, j: int) -> int:
        total = 0
        for row, col in self.get_dirs(i, j):
            if self._board[row][col] == MINE:
                total += 1
        return total

    def get_dirs(self, i: int, j: int) -> Generator:
        for row in range(-1, 2):
            for col in range(-1, 2):
                if (row, col) != (0, 0):
                    if self.on_board(row + i, col + j):
                        yield (row + i, col + j)

    def result(self):
        game_over = True
        for row in self._board:
            if BOOM in row:
                return -1
            if HIDDEN in row:
                game_over = False
        return 1 if game_over else 0
