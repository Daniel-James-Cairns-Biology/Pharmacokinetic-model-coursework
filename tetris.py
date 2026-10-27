"""A small keyboard-controlled Tetris game using only Python's standard library."""

import random
import tkinter as tk


CELL_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BOARD_COLOR = "#111827"
GRID_COLOR = "#263244"

SHAPES = (
    ("I", ((0, 1), (1, 1), (2, 1), (3, 1)), "#38bdf8"),
    ("O", ((1, 0), (2, 0), (1, 1), (2, 1)), "#facc15"),
    ("T", ((1, 0), (0, 1), (1, 1), (2, 1)), "#c084fc"),
    ("S", ((1, 0), (2, 0), (0, 1), (1, 1)), "#4ade80"),
    ("Z", ((0, 0), (1, 0), (1, 1), (2, 1)), "#fb7185"),
    ("J", ((0, 0), (0, 1), (1, 1), (2, 1)), "#60a5fa"),
    ("L", ((2, 0), (0, 1), (1, 1), (2, 1)), "#fb923c"),
)


class Tetris:
    def __init__(self, root):
        self.root = root
        self.root.title("Tetris")
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
        self.level_label = tk.Label(root, text="Lines: 0", font=("Helvetica", 12))
        self.level_label.grid(row=1, column=1, padx=12, sticky="nw")
        tk.Label(
            root,
            text=(
                "← →  Move\n↑      Rotate\n↓      Soft drop\n"
                "Space  Hard drop\nP      Pause\nR      Restart"
            ),
            justify="left",
            font=("Helvetica", 11),
        ).grid(row=2, column=1, padx=12, sticky="nw")

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
        self.active = self.new_piece()
        self.draw()
        self.schedule_tick()

    @staticmethod
    def new_piece():
        name, cells, color = random.choice(SHAPES)
        return {
            "name": name,
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
            if self.fits(rotated, self.active["x"] + offset, self.active["y"]):
                self.active["cells"] = rotated
                self.active["x"] += offset
                self.draw()
                return

    def soft_drop(self):
        if self.paused or self.game_over:
            return
        previous_y = self.active["y"]
        self.move(0, 1)
        if self.active["y"] > previous_y:
            self.score += 1
            self.score_label.config(text=f"Score: {self.score}")
        else:
            self.lock_piece()

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

    def tick(self):
        if not self.paused and not self.game_over:
            if self.fits(
                self.active["cells"], self.active["x"], self.active["y"] + 1
            ):
                self.active["y"] += 1
            else:
                self.lock_piece()
            self.draw()
        self.schedule_tick()

    def schedule_tick(self):
        speed = max(90, 600 - (self.lines // 10) * 50)
        self.timer_id = self.root.after(speed, self.tick)

    def lock_piece(self):
        for dx, dy in self.active["cells"]:
            x = self.active["x"] + dx
            y = self.active["y"] + dy
            if y < 0:
                self.game_over = True
                return
            self.board[y][x] = self.active["color"]

        full_rows = [
            row for row in self.board if all(cell is not None for cell in row)
        ]
        self.board = [
            row for row in self.board if not all(cell is not None for cell in row)
        ]
        self.board = [[None] * BOARD_WIDTH for _ in full_rows] + self.board
        cleared = len(full_rows)
        self.lines += cleared
        self.score += (0, 100, 300, 500, 800)[cleared] * (
            self.lines // 10 + 1
        )
        self.score_label.config(text=f"Score: {self.score}")
        self.level_label.config(text=f"Lines: {self.lines}")
        self.active = self.new_piece()
        if not self.fits(
            self.active["cells"], self.active["x"], self.active["y"]
        ):
            self.game_over = True

    def toggle_pause(self):
        if not self.game_over:
            self.paused = not self.paused
            self.draw()

    def draw(self):
        self.canvas.delete("all")
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self.draw_cell(x, y, color)

        if not self.game_over:
            for dx, dy in self.active["cells"]:
                self.draw_cell(
                    self.active["x"] + dx,
                    self.active["y"] + dy,
                    self.active["color"],
                )

        for x in range(BOARD_WIDTH + 1):
            self.canvas.create_line(
                x * CELL_SIZE, 0, x * CELL_SIZE, BOARD_HEIGHT * CELL_SIZE,
                fill=GRID_COLOR,
            )
        for y in range(BOARD_HEIGHT + 1):
            self.canvas.create_line(
                0, y * CELL_SIZE, BOARD_WIDTH * CELL_SIZE, y * CELL_SIZE,
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
        self.canvas.create_rectangle(
            left + 1,
            top + 1,
            left + CELL_SIZE - 1,
            top + CELL_SIZE - 1,
            fill=color,
            outline="",
        )


def main():
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
