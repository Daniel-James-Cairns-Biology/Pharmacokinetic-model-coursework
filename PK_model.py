import numpy

from pk_model import Model, Protocol


def main():
    model = Model(central_volume=3000, clearance=300)
    protocol = Protocol().add_bolus(1000)
    times = numpy.linspace(0, 24, 241)
    solution = model.solve(protocol, times)

    print("Central amount at 0, 8, and 24 hours [ng]:")
    print(solution.amount("central")[[0, 80, 240]])


if __name__ == "__main__":
    main()
