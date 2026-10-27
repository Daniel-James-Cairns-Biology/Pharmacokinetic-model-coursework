"""Launch the PK model demo or one of the games from a simple menu."""

import subprocess
import sys
from pathlib import Path

import numpy

from pk_model import Model, Protocol

PROJECT_DIR = Path(__file__).resolve().parent
GAMES = {
    "2": ("Tetris", "tetris.py"),
    "3": ("Sandtris", "sandtris.py"),
    "4": ("Snake", "snake.py"),
}


def run_model_demo():
    model = Model(central_volume=3000, clearance=300)
    protocol = Protocol().add_bolus(1000)
    solution = model.solve(protocol, numpy.linspace(0, 24, 241))
    solution.plot()


def run_game(script):
    return subprocess.run(
        [sys.executable, str(PROJECT_DIR / script)],
        cwd=PROJECT_DIR,
        check=False,
    ).returncode


def main():
    while True:
        print(
            "\nChoose what to run:\n"
            "1. Pharmacokinetic model demo\n"
            "2. Tetris\n"
            "3. Sandtris\n"
            "4. Snake (requires Pygame)\n"
            "q. Quit"
        )
        choice = input("> ").strip().lower()

        if choice == "q":
            return
        if choice == "1":
            run_model_demo()
        elif choice in GAMES:
            name, script = GAMES[choice]
            print(f"Starting {name}...")
            return_code = run_game(script)
            if return_code:
                print(f"{name} exited with status {return_code}.")
        else:
            print("Choose 1, 2, 3, 4, or q.")


if __name__ == "__main__":
    main()
