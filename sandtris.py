"""A falling-sand block game. Run with ``python3 sandtris.py``."""

import random
import tkinter as tk


CELL_SIZE = 24
BOARD_WIDTH = 12
BOARD_HEIGHT = 22
COLORS = (
    ("cyan", "#38bdf8"),
    ("yellow", "#facc15"),
    ("purple", "#c084fc"),
    ("green", "#4ade80"),
    ("pink", "#fb7185"),
    ("blue", "#60a5fa"),
    ("orange", "#fb923c"),
)
BOARD_COLOR = "#111827"
GRID_COLOR = "#263244"

SHAPES = (
    ((0, 1), (1, 1), (2, 1), (3, 1)),
    ((1, 0), (2, 0), (1, 1), (2, 1)),
    ((1, 0), (0, 1), (1, 1), (2, 1)),
    ((1, 0), (2, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((2, 0), (0, 1), (1, 1), (2, 1)),
)


def settle_sand(board, rng=random):
    """Move each grain down, or diagonally around an obstacle."""
    moved = False
    for y in range(len(board) - 2, -1, -1):
        x_positions = range(len(board[y]))
        if rng.randrange(2):
            x_positions = reversed(x_positions)
        for x in x_positions:
            color = board[y][x]
            if color is None:
                continue

            if board[y + 1][x] is None:
                board[y + 1][x] = color
                board[y][x] = None
                moved = True
                continue

            diagonals = [-1, 1]
            if rng.randrange(2):
                diagonals.reverse()
            for dx in diagonals:
                next_x = x + dx
                if (
                    0 <= next_x < len(board[y])
                    and board[y + 1][next_x] is None
                ):
                    board[y + 1][next_x] = color
                    board[y][x] = None
                    moved = True
                    break
    return moved


def clear_target_rows(board, target_color):
    """Clear only completely filled rows made entirely of the target color."""
    width = len(board[0])
    remaining = [
        row
        for row in board
        if not all(color == target_color for color in row)
    ]
    cleared = len(board) - len(remaining)
    board[:] = [[None] * width for _ in range(cleared)] + remaining
    return cleared


class Sandtris:
    def __init__(self, root):
        self.root = root
        self.root.title("Sandtris")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=BOARD_WIDTH * CELL_SIZE,
            height=BOARD_HEIGHT * CELL_SIZE,
            background=BOARD_COLOR,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, rowspan=5, padx=12, pady=12)

        self.score_label = tk.Label(root, text="Score: 0", font=("Helvetica", 16))
        self.score_label.grid(row=0, column=1, padx=12, sticky="w")
        self.lines_label = tk.Label(root, text="Lines: 0", font=("Helvetica", 12))
        self.lines_label.grid(row=1, column=1, padx=12, sticky="nw")
        self.target_label = tk.Label(root, font=("Helvetica", 12, "bold"))
        self.target_label.grid(row=2, column=1, padx=12, sticky="nw")
        tk.Label(
            root,
            text=(
                "← →  Move\n↑      Rotate\n↓      Soft drop\n"
                "Space  Hard drop\nP      Pause\nR      Restart"
            ),
            justify="left",
            font=("Helvetica", 11),
        ).grid(row=3, column=1, padx=12, sticky="nw")

        self.root.bind("<Left>", lambda _event: self.move(-1, 0))
        self.root.bind("<Right>", lambda _event: self.move(1, 0))
        self.root.bind("<Down>", lambda _event: self.soft_drop())
        self.root.bind("<Up>", lambda _event: self.rotate())
        self.root.bind("<space>", lambda _event: self.hard_drop())
        self.root.bind("p", lambda _event: self.toggle_pause())
        self.root.bind("P", lambda _event: self.toggle_pause())
        self.root.bind("r", lambda _event: self.restart())
        self.root.bind("R", lambda _event: self.restart())

        self.restart()

    def restart(self):
        if hasattr(self, "timer_id"):
            self.root.after_cancel(self.timer_id)
        self.board = [[None] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.paused = False
        self.game_over = False
        self.target = random.choice(COLORS)
        self.active = self.new_piece()
        self.update_labels()
        self.draw()
        self.schedule_tick()

    @staticmethod
    def new_piece():
        cells = random.choice(SHAPES)
        color = random.choice(COLORS)
        return {
            "cells": list(cells),
            "color": color,
            "x": BOARD_WIDTH // 2 - 2,
            "y": 0,
        }

    def fits(self, cells, x, y):
        for dx, dy in cells:
            board_x, board_y = x + dx, y + dy
            if board_x < 0 or board_x >= BOARD_WIDTH or board_y >= BOARD_HEIGHT:
                return False
            if board_y >= 0 and self.board[board_y][board_x] is not None:
                return False
        return True

    def move(self, dx, dy):
        if self.paused or self.game_over:
            return
        new_x = self.active["x"] + dx
        new_y = self.active["y"] + dy
        if self.fits(self.active["cells"], new_x, new_y):
            self.active["x"] = new_x
            self.active["y"] = new_y
            self.draw()

    def rotate(self):
        if self.paused or self.game_over:
            return
        rotated = [(3 - y, x) for x, y in self.active["cells"]]
        for offset in (0, -1, 1, -2, 2):
            x = self.active["x"] + offset
            if self.fits(rotated, x, self.active["y"]):
                self.active["cells"] = rotated
                self.active["x"] = x
                self.draw()
                return

    def soft_drop(self):
        if self.paused or self.game_over:
            return
        if self.fits(self.active["cells"], self.active["x"], self.active["y"] + 1):
            self.active["y"] += 1
            self.score += 1
            self.update_labels()
            self.draw()
        else:
            self.lock_piece()
            self.draw()

    def hard_drop(self):
        if self.paused or self.game_over:
            return
        distance = 0
        while self.fits(
            self.active["cells"], self.active["x"], self.active["y"] + 1
        ):
            self.active["y"] += 1
            distance += 1
        self.score += distance * 2
        self.lock_piece()
        self.draw()

    def tick(self):
        if self.game_over:
            return
        if not self.paused:
            settle_sand(self.board)
            if self.fits(
                self.active["cells"], self.active["x"], self.active["y"] + 1
            ):
                self.active["y"] += 1
            else:
                self.lock_piece()
            self.draw()
        self.schedule_tick()

    def schedule_tick(self):
        speed = max(80, 500 - (self.lines // 5) * 35)
        self.timer_id = self.root.after(speed, self.tick)

    def lock_piece(self):
        for dx, dy in self.active["cells"]:
            x = self.active["x"] + dx
            y = self.active["y"] + dy
            if y < 0:
                self.game_over = True
                return
            self.board[y][x] = self.active["color"]

        cleared = clear_target_rows(self.board, self.target)
        if cleared:
            self.lines += cleared
            self.score += cleared * 100
            available_targets = [color for color in COLORS if color != self.target]
            self.target = random.choice(available_targets)
        self.update_labels()
        self.active = self.new_piece()
        if not self.fits(
            self.active["cells"], self.active["x"], self.active["y"]
        ):
            self.game_over = True

    def update_labels(self):
        self.score_label.config(text=f"Score: {self.score}")
        self.lines_label.config(text=f"Lines: {self.lines}")
        self.target_label.config(
            text=f"Clear a {self.target[0]} row",
            fg=self.target[1],
        )

    def toggle_pause(self):
        if not self.game_over:
            self.paused = not self.paused
            self.draw()

    def draw(self):
        self.canvas.delete("all")
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self.draw_cell(x, y, color[1])

        if not self.game_over:
            for dx, dy in self.active["cells"]:
                self.draw_cell(
                    self.active["x"] + dx,
                    self.active["y"] + dy,
                    self.active["color"][1],
                )

        for x in range(BOARD_WIDTH + 1):
            self.canvas.create_line(
                x * CELL_SIZE,
                0,
                x * CELL_SIZE,
                BOARD_HEIGHT * CELL_SIZE,
                fill=GRID_COLOR,
            )
        for y in range(BOARD_HEIGHT + 1):
            self.canvas.create_line(
                0,
                y * CELL_SIZE,
                BOARD_WIDTH * CELL_SIZE,
                y * CELL_SIZE,
                fill=GRID_COLOR,
            )

        if self.game_over or self.paused:
            message = "Game over — press R to restart" if self.game_over else "Paused"
            self.canvas.create_text(
                BOARD_WIDTH * CELL_SIZE // 2,
                BOARD_HEIGHT * CELL_SIZE // 2,
                text=message,
                fill="white",
                font=("Helvetica", 16, "bold"),
            )

    def draw_cell(self, x, y, color):
        left, top = x * CELL_SIZE, y * CELL_SIZE
        self.canvas.create_oval(
            left + 2,
            top + 2,
            left + CELL_SIZE - 2,
            top + CELL_SIZE - 2,
            fill=color,
            outline="",
        )


def main():
    root = tk.Tk()
    Sandtris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
