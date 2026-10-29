"""Launch the PK model demo or one of the games from a simple menu."""

import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pk_model import Model, Protocol

PROJECT_DIR = Path(__file__).resolve().parent
GAMES = {
    "2": ("Tetris", "tetris.py"),
    "3": ("Sandtris", "sandtris.py"),
    "4": ("Brickbreaker", "brickbreaker.py"),
    "5": ("Snake", "snake.py"),
    "6": ("Therapist", "therapist.py"),
}

init_vect = [1, 3000, 300, 1, 1000, 100, 1000, 24, 0.8]
def run_model_demo():
    """Interactive command line based implementation of the PK model"""
    print("PK model simulation")
    try:
        print("Choose drug administration route")
        init_temp = []
        choice = (
            input(f"[1] Intravenous (IV), [2] Subcutaneous (SC) [default: {init_vect[0]}]: ")
            or init_vect[0]
        )
        init_temp = [0]*9 if choice == "2" or 2 else [0]*8
        init_temp[0] = 2 if choice == "2" or 2 else 1
        model_type = "SC" if choice == "2" or 2 else "IV"
        print(f"{model_type} used.")

        v_c = float(
            input(f"Input central compartment volume (ml) [default: {init_vect[1]}]: ")
            or init_vect[1]
        )
        init_temp[1]=v_c

        cl = float(
            input(f"Input clearance rate (ml/h) [default: {init_vect[2]}]: ")
            or init_vect[2]
        )
        init_temp[2] = cl
        if model_type == "SC":
            k_a = float(
                input(f"Enter absorption rate (1/h): [default: {init_vect[8]}]: ")
                or init_vect[8]
        )
            init_temp[8] = k_a
        else:
            k_a = None
        num_periph = int(
            input(f"Number of peripheral compartments (0, 1, or 2) [default: {init_vect[3]}]: ")
            or init_vect[3]
        )
        init_temp[3] = num_periph
        v_p = []
        q_p = []

        for i in range(num_periph):
            v_i = float(
                input(f"Peripheral {i+1} Volume V_{i+1} (mL) [default: {init_vect[4]}]: ")
                or init_vect[4]
            )
            q_i = float(
                input(f"Peripheral {i+1} Clearance Q_{i+1} (mL/h) [default: {init_vect[5]}]: ")
                or init_vect[5]
            )
            v_p.append(v_i)
            q_p.append(q_i)

        if num_periph == 0:
            init_temp[4] = init_vect[4]
            init_temp[5] = init_vect[5]
        else:
            init_temp[4] = v_p[num_periph-1]
            init_temp[5] = q_p[num_periph-1]

        dose = float(
            input(f"Enter bolus dose (ng)[default: {init_vect[6]}]: ")
            or init_vect[6]
        )
        init_temp[6] = dose

        duration = float(
            input(f"Enter simulation duration (hrs) [default: {init_vect[7]}]: ")
            or init_vect[7]
        )
        init_temp[7] = duration

        change_defaults = input("Save conditions as default? [y/n]") or "y"
        if change_defaults == "y" or "Y":
            print("Conditions saved.")
            print(init_temp)
            init_vect[0:len(init_temp)] = init_temp

        protocol = Protocol().add_bolus(dose)
        print(init_vect)

        model = Model(
            central_volume=v_c,
            clearance=cl,
            peripheral_volumes=v_p,
            intercompartmental_clearances=q_p,
            route=model_type,
            absorption_rate=k_a,
        )
        times = np.linspace(0, duration, int(duration * 10) + 1)
        solution = model.solve(protocol, times)
        print("Plotting...")
        solution.plot()
        figure, (concentration_axis, depot_axis) = plt.subplots(
            2, 1, figsize=(10, 8), sharex=True
        )
        plt.sca(concentration_axis)
        compartments = ["central"] + [f"peripheral_{i+1}" for i in range(num_periph)]
        solution.plot(compartments=compartments)

        concentration_axis.set_title("IV and SC concentration profiles")

        if model_type == "SC" or k_a is not None:
            plt.sca(depot_axis)
            solution.plot(quantity="amount", compartments=["depot"])
            depot_axis.set_title("Subcutaneous Absorption Depot")
            depot_axis.set_xlabel("Time [h]")

        figure.tight_layout()
        plot_path = PROJECT_DIR / "pk_model_demo.png"
        figure.savefig(plot_path, dpi=150, bbox_inches="tight")
        print(f"Plot saved to {plot_path}")
        plt.show()
        plt.close()
    except Exception:
        print("Something went wrong, do you want to talk to someone about it?")
        print("Sending you to therapy...")
        run_game("therapist.py")


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
            "1. Pharmacokinetic Model Demo\n"
            "2. Tetris\n"
            "3. Sandtris\n"
            "4. Brickbreaker \n"
            "5. Snake (requires Pygame)\n"
            "6. Therapist\n"
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
            print("Choose 1, 2, 3, 4, 5, 6, or q.")


if __name__ == "__main__":
    main()
