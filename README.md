# vPlotter for Raspberry Pi
This is the software for controlling self-made plotter based on Raspberry Pi.

The server software is written in Python and contains three front-ends:
- interactive terminal (can be runned directly on RPi or through SSH)
- command file parser (interprets .plo files with commands for plotter)
- TCP/IP server (for remote controlling)

The client software is written in Mono/C# and is used only with TCP/IP server. It can be used for sending commands, sending .plo files or drawing a figures (soon). 
