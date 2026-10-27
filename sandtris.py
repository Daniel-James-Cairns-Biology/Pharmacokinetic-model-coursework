"""A falling-sand block game. Run with ``python3 sandtris.py``."""

import random
import tkinter as tk

CELL_SIZE = 5
PARTICLES_PER_BLOCK = 5
PHYSICS_STEPS_PER_TICK = 3
TICK_MILLISECONDS = 75
BLOCK_WIDTH = 12
BLOCK_HEIGHT = 22
BOARD_WIDTH = BLOCK_WIDTH * PARTICLES_PER_BLOCK
BOARD_HEIGHT = BLOCK_HEIGHT * PARTICLES_PER_BLOCK
COLORS = (
    ("cyan", "#38bdf8"),
    ("yellow", "#facc15"),
    ("purple", "#c084fc"),
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


def lighten_color(color, amount=0.55):
    """Blend a hex color toward white for a glass-like reflective edge."""
    channels = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
    lighter = [
        round(channel + (255 - channel) * amount) for channel in channels
    ]
    return "#" + "".join(f"{channel:02x}" for channel in lighter)


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
                if 0 <= next_x < len(board[y]) and board[y + 1][next_x] is None:
                    board[y + 1][next_x] = color
                    board[y][x] = None
                    moved = True
                    break
    return moved


def clear_spanning_paths(board):
    """Clear each same-color cluster connected from the left edge to the right."""
    height, width = len(board), len(board[0])
    visited = set()
    paths_cleared = 0

    for start_y in range(height):
        color = board[start_y][0]
        if color is None or (0, start_y) in visited:
            continue

        component = []
        stack = [(0, start_y)]
        touches_right = False
        visited.add((0, start_y))

        while stack:
            x, y = stack.pop()
            component.append((x, y))
            if x == width - 1:
                touches_right = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    next_x, next_y = x + dx, y + dy
                    point = (next_x, next_y)
                    if (
                        0 <= next_x < width
                        and 0 <= next_y < height
                        and point not in visited
                        and board[next_y][next_x] == color
                    ):
                        visited.add(point)
                        stack.append(point)

        if touches_right:
            paths_cleared += 1
            for x, y in component:
                board[y][x] = None

    return paths_cleared


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
        self.particles_label = tk.Label(
            root, text="Particles: 0", font=("Helvetica", 12)
        )
        self.particles_label.grid(row=2, column=1, padx=12, sticky="nw")
        self.target_label = tk.Label(root, font=("Helvetica", 12, "bold"))
        self.target_label.grid(row=3, column=1, padx=12, sticky="nw")
        tk.Label(
            root,
            text=(
                "← →  Move\n↑      Rotate\n↓      Soft drop\n"
                "Space  Hard drop\nP      Pause\nR      Restart"
            ),
            justify="left",
            font=("Helvetica", 11),
        ).grid(row=4, column=1, padx=12, sticky="nw")

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
        self.particle_count = 0
        self.paused = False
        self.game_over = False
        self.fall_counter = 0
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
            "x": BLOCK_WIDTH // 2 - 2,
            "y": 0,
        }

    def fits(self, cells, x, y):
        for dx, dy in cells:
            left = (x + dx) * PARTICLES_PER_BLOCK
            top = (y + dy) * PARTICLES_PER_BLOCK
            if (
                left < 0
                or left + PARTICLES_PER_BLOCK > BOARD_WIDTH
                or top + PARTICLES_PER_BLOCK > BOARD_HEIGHT
            ):
                return False
            for particle_y in range(top, top + PARTICLES_PER_BLOCK):
                for particle_x in range(left, left + PARTICLES_PER_BLOCK):
                    if self.board[particle_y][particle_x] is not None:
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
        while self.fits(self.active["cells"], self.active["x"], self.active["y"] + 1):
            self.active["y"] += 1
            distance += 1
        self.score += distance * 2
        self.lock_piece()
        self.draw()

    def tick(self):
        if self.game_over:
            return
        if not self.paused:
            for _ in range(PHYSICS_STEPS_PER_TICK):
                settle_sand(self.board)
            self.clear_completed_paths()
            self.fall_counter += 1
            drop_every = max(2, 6 - self.lines // 10)
            if self.fall_counter >= drop_every:
                self.fall_counter = 0
                if self.fits(
                    self.active["cells"], self.active["x"], self.active["y"] + 1
                ):
                    self.active["y"] += 1
                else:
                    self.lock_piece()
            self.draw()
        self.schedule_tick()

    def schedule_tick(self):
        speed = max(45, TICK_MILLISECONDS - (self.lines // 5) * 5)
        self.timer_id = self.root.after(speed, self.tick)

    def lock_piece(self):
        for dx, dy in self.active["cells"]:
            left = (self.active["x"] + dx) * PARTICLES_PER_BLOCK
            top = (self.active["y"] + dy) * PARTICLES_PER_BLOCK
            if top < 0:
                self.game_over = True
                return
            for y in range(top, top + PARTICLES_PER_BLOCK):
                for x in range(left, left + PARTICLES_PER_BLOCK):
                    self.board[y][x] = self.active["color"]

        self.clear_completed_paths()
        self.update_labels()
        self.active = self.new_piece()
        if not self.fits(self.active["cells"], self.active["x"], self.active["y"]):
            self.game_over = True

    def clear_completed_paths(self):
        cleared_paths = clear_spanning_paths(self.board)
        if cleared_paths:
            self.lines += cleared_paths
            self.score += cleared_paths * BOARD_WIDTH * 10
            self.update_labels()

    def update_labels(self):
        self.score_label.config(text=f"Score: {self.score}")
        self.lines_label.config(text=f"Paths cleared: {self.lines}")
        self.particle_count = sum(
            color is not None for row in self.board for color in row
        )
        self.particles_label.config(text=f"Sand grains: {self.particle_count}")
        self.target_label.config(
            text="Any colour: connect left to right",
            fg="white",
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
                    self.draw_particle(x, y, color[1])

        if not self.game_over:
            for dx, dy in self.active["cells"]:
                left = (self.active["x"] + dx) * PARTICLES_PER_BLOCK
                top = (self.active["y"] + dy) * PARTICLES_PER_BLOCK
                for y in range(top, top + PARTICLES_PER_BLOCK):
                    for x in range(left, left + PARTICLES_PER_BLOCK):
                        self.draw_particle(x, y, self.active["color"][1])

        for x in range(BOARD_WIDTH + 1):
            self.canvas.create_line(
                x * CELL_SIZE,
                0,
                x * CELL_SIZE,
                BOARD_HEIGHT * CELL_SIZE,
                fill=GRID_COLOR if x % PARTICLES_PER_BLOCK == 0 else BOARD_COLOR,
            )
        for y in range(BOARD_HEIGHT + 1):
            self.canvas.create_line(
                0,
                y * CELL_SIZE,
                BOARD_WIDTH * CELL_SIZE,
                y * CELL_SIZE,
                fill=GRID_COLOR if y % PARTICLES_PER_BLOCK == 0 else BOARD_COLOR,
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

    def draw_particle(self, x, y, color):
        left, top = x * CELL_SIZE, y * CELL_SIZE
        inset = 0.45
        self.canvas.create_oval(
            left + inset,
            top + inset,
            left + CELL_SIZE - inset,
            top + CELL_SIZE - inset,
            fill=color,
            outline=lighten_color(color),
            width=1,
        )
        if (x + y) % 3 == 0:
            self.canvas.create_oval(
                left + 1.1,
                top + 1.0,
                left + 2.2,
                top + 2.1,
                fill="#ffffff",
                outline="",
            )


def main():
    root = tk.Tk()
    Sandtris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
