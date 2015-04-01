from hardware import Plotter

if __name__ == "__main__":
    print("vPlotter Interactive Terminal\n")

    plotter = Plotter()
    print("Ready")
    while True:
        command = input("> ")
        if command.strip() == "":
            continue
        msg = plotter.exec(command)
        if msg is not None:
            print(msg)