import sys
import signal

from plotter import *

isprocessing = False

def signal_handler(*args):
    if isprocessing:
        plotter.stopexecute()
        return

    print('\nCtrl+C pressed, quitting...')
    if plotter:
        plotter.shutdown()
    sys.exit(0)


def execute_command(command):
    if command == "":
        return
    try:
        for msg in plotter.execute(command):
            if msg:
                print(msg)
    except ExecutionError as ex:
        print("\n" + str(ex))
    except CommandError as ex:
        print("ERROR: " + str(ex), file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    mutual_term = parser.add_mutually_exclusive_group()
    mutual_term.add_argument('-c', help="execute single command", metavar="<command>", dest='command', type=str)
    mutual_term.add_argument('-f', help="execute commands from file", metavar="<file>", dest='file',
                             type=argparse.FileType())

    global plotter
    plotter = Plotter(parser)

    print("-= vPlotter Interactive Terminal =-\nCtrl+C - terminate")
    signal.signal(signal.SIGINT, signal_handler)
    termargs = parser.parse_known_args()[0]
    if termargs.command:
        print(termargs.command)
        try:
            execute_command(termargs.command)
        finally:
            plotter.shutdown()
        return
    elif termargs.file:
        import file

        try:
            file.CommandFileParser(plotter, termargs.file)
        finally:
            plotter.shutdown()
        return
    print("Ready.")
    global isprocessing
    isprocessing = False
    while True:
        command = input("> ").strip()
        isprocessing = True
        execute_command(command)
        isprocessing = False

if __name__ == "__main__":
    main()
