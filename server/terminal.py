from hardware import Plotter, CommandError
import sys

if __name__ == "__main__":
    print("-= vPlotter Interactive Terminal =-\n")

    plotter = Plotter()
    print("Ready.")
    while True:
        try:
            command = input("> ").strip()
            if command == "":
                continue
            msg = plotter.execute(command)
            if msg is not None:
                print(msg)
        except CommandError as ex:
            print("Error: " + str(ex).lower(), file=sys.stderr)
        except KeyboardInterrupt:
            print("\nCtrl+C pressed, quitting...")
            exit()