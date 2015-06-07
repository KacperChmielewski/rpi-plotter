from hardware import Plotter, CommandError
import sys
import signal
import argparse


def signal_handler(*args):
    print('\nCtrl+C pressed, quitting...')
    if plotter:
        plotter.setpower(False)
    sys.exit(0)


def main():
    print("-= vPlotter Interactive Terminal =-\nCtrl+C - terminate")
    signal.signal(signal.SIGINT, signal_handler)
    global plotter
    plotter = Plotter(debug=True)
    print("Ready.")
    while True:
        try:
            command = input("> ").strip()
            if command == "":
                continue
            for msg in plotter.execute(command):
                if msg:
                    print(msg)
        except CommandError as ex:
            print("ERROR: " + ex.__str__(False), file=sys.stderr)


if __name__ == "__main__":
    main()
