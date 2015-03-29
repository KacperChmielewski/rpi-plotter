from plotter import Plotter
from time import sleep

if True:

    plotter = Plotter()
   
    commandsFile = open('print.plo', 'r')
    commandsRaw = commandsFile.read()
    commandsFile.close()

    commandRawRows = commandsRaw.split("\n")
    for commandRawRow in commandRawRows:
       sleep(1)
       print(commandRawRow)
       command = commandRawRow
       msg = plotter.exec(command)
       if msg is not None:
           print(msg)
