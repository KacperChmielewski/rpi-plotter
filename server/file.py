from plotter import *
import sys
import re


class CommandFileParser:
    def __init__(self, plotter, fp):
        self.plotter = plotter
        if fp:
            self.execute(fp)

    def execute(self, fp):
        if not self.plotter:
            raise Exception("No plotter instance passed!")

        cmds = fp.read()
        fp.close()
        cmds = re.sub(r'(\s+)|(^#.*)', ' ', cmds, flags=re.MULTILINE).strip()
        for msg in self.plotter.execute(cmds):
            if msg:
                yield msg
