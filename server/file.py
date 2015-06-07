from plotter import *
import sys


class CommandFileParser:
    def __init__(self, plotter, fp):
        self.plotter = plotter
        if fp:
            self.execute(fp)

    def execute(self, fp):
        if not self.plotter:
            raise Exception("No plotter instance passed!")
        cmds = fp.read().split('\n')
        fp.close()
        counter = 1
        for cmd in cmds:
            if self.plotter.getdebug():
                print(cmd)
            try:
                for msg in self.plotter.execute(cmd):
                    if msg:
                        print(msg)
            except CommandError as ex:
                print("ERROR: {}, line {}.".format(ex.__str__(False), counter), file=sys.stderr)
                return
            counter += 1
