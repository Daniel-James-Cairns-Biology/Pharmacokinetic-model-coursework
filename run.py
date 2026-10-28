"""Launch the PK model demo or one of the games from a simple menu."""

import subprocess
import sys
import webbrowser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pk_model import Model, Protocol

PROJECT_DIR = Path(__file__).resolve().parent
GAMES = {
    "2": ("Tetris", "tetris.py"),
    "3": ("Sandtris", "sandtris.py"),
    "4": ("Snake", "snake.py"),
}


def run_model_demo():
    """Interactive command line based implementation of the PK model"""
    print("PK model simulation")
    try: 
        print("Choose drug administration route")
        choice = input("[1] Intravenous (IV), [2] Subcutaneous (SC) [default: 1]: " or 1)
        model_type = "sc" if choice == "2" else "iv"
        print(f"{model_type} used.")

        v_c = float(input("Input central compartment volume (ml) [default: 3000]: ") or 3000)
        cl = float(input("Input clearance rate (ml/h) [default: 300]: ") or 300)
        if model_type == "sc": 
            k_a = float(input("Enter absorption rate (1/h): [default: 0.8]: ") or 0.8)
        else: 
            k_a = None
        num_periph = int(input("Number of peripheral compartments (0, 1, or 2) [default: 1]: ") or 1)
        
        v_p = []
        q_p = []
        
        for i in range(num_periph):
            v_i = float(input(f"Peripheral {i+1} Volume V_{i+1} (mL) [1000]: ") or 1000)
            q_i = float(input(f"Peripheral {i+1} Clearance Q_{i+1} (mL/h) [100]: ") or 100)
            v_p.append(v_i)
            q_p.append(q_i)
        dose = float(input("Enter bolus dose (ng) [default: 1000]: ") or 1000)
        duration = float(input("Enter simulation duration (hrs) [default: 24]: ") or 24)
        protocol = Protocol().add_bolus(dose)

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

        concentration_axis.set_title("IV and subcutaneous concentration profiles")
    
        if model_type == "sc" or k_a is not None:
            plt.sca(depot_axis)
            solution.plot(quantity="amount", compartments=["depot"])
            depot_axis.set_title("Subcutaneous absorption depot")
            depot_axis.set_xlabel("Time [h]")
    
        figure.tight_layout()
        plot_path = PROJECT_DIR / "pk_model_demo.png"
        figure.savefig(plot_path, dpi=150, bbox_inches="tight")
        print(f"Plot saved to {plot_path}")
        plt.show()
        plt.close()
    except Exception as e: 
        print("Something went wrong, play snake instead!")
        run_game("snake.py")
    

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
