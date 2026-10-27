"""Launch the PK model demo or one of the games from a simple menu."""

import subprocess
import sys
import webbrowser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy

from pk_model import Model, Protocol

PROJECT_DIR = Path(__file__).resolve().parent
GAMES = {
    "2": ("Tetris", "tetris.py"),
    "3": ("Sandtris", "sandtris.py"),
    "4": ("Snake", "snake.py"),
}


def run_model_demo():
    model_parameters = {
        "central_volume": 3000,
        "clearance": 300,
        "peripheral_volumes": [5000, 10000],
        "intercompartmental_clearances": [200, 150],
    }
    iv_model = Model(**model_parameters, name="IV")
    sc_model = Model(
        **model_parameters,
        route="sc",
        absorption_rate=0.8,
        name="SC",
    )
    protocol = Protocol().add_bolus(1000)
    times = numpy.linspace(0, 24, 241)
    iv_solution = iv_model.solve(protocol, times)
    sc_solution = sc_model.solve(protocol, times)

    figure, (concentration_axis, depot_axis) = plt.subplots(
        2, 1, figsize=(10, 8), sharex=True
    )
    plt.sca(concentration_axis)
    compartments = ["central", "peripheral_1", "peripheral_2"]
    iv_solution.plot(compartments=compartments)
    sc_solution.plot(compartments=compartments)
    concentration_axis.set_title("IV and subcutaneous concentration profiles")

    plt.sca(depot_axis)
    sc_solution.plot(quantity="amount", compartments=["depot"])
    depot_axis.set_title("Subcutaneous absorption depot")
    depot_axis.set_xlabel("Time [h]")

    figure.tight_layout()
    plot_path = PROJECT_DIR / "pk_model_demo.png"
    figure.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot saved to {plot_path}")
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", "Preview", str(plot_path)], check=True)
    elif not webbrowser.open(plot_path.as_uri(), new=2):
        raise RuntimeError(f"Could not open plot: {plot_path}")


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
