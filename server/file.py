from hardware import Plotter, BadCommandError, NotCalibratedError


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
                msg = self.plotter.exec(cmd)
                if msg is not None:
                    print(msg)
            except BadCommandError:
                print(cmd + " - bad command, line " + counter + ".")
                return
            except NotCalibratedError:
                print(cmd + " - plotter is not calibrated, line " + counter + ".")
                return
            counter += 1

if __name__ == "__main__":
    print("Executing commands from print.plo...\n")
    parser = CommandFileParser(Plotter(), 'print.plo')
