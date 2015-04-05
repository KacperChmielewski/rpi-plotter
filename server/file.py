from hardware import Plotter, CommandError
import sys


class CommandFileParser:
    def __init__(self, plotter, filename=None):
        self.plotter = plotter
        if filename and len(filename) > 0:
            self.execute(filename)

    def execute(self, filename):
        if not self.plotter:
            raise Exception("No plotter instance passed!")
        f = open(filename, 'r')
        cmds = f.read().split('\n')
        f.close()
        counter = 1
        for cmd in cmds:
            print(cmd)
            try:
                msg = self.plotter.execute(cmd)
                if msg is not None:
                    print(msg)
            except CommandError as ex:
                print("{} - {}, line {}.".format(cmd, str(ex), counter), file=sys.stderr)
                return
            counter += 1


if __name__ == "__main__":
    print("Executing commands from print.plo...\n")
    parser = CommandFileParser(Plotter(), 'print.plo')
