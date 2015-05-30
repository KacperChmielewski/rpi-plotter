from hardware import Plotter, CommandError
import sys
import signal

plotter = None


def signal_handler(*args):
    print('\nCtrl+C pressed, quitting...')
    if plotter:
        plotter.setpower(False)
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("-= vPlotter Interactive Terminal =-\nPress Ctrl+C to terminate")
    plotter = Plotter(debug=True)
    print("Ready.")
    while True:
        try:
            command = input("> ")
            command = command.strip()
            if command == "":
                continue
            for msg in plotter.execute(command):
                if msg:
                    print(msg)
        except CommandError as ex:
            print("ERROR: " + str(ex), file=sys.stderr)
