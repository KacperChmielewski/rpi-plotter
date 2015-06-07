# vPlotter for Raspberry Pi
Software for controlling self-made plotter based on Raspberry Pi.

The server software is written in Python and contains three front-ends:
- interactive terminal (can be runned directly on RPi or through SSH)
- SVG file parser (interprets .svg files with paths and executes path data)
- TCP/IP server & client (for remote controlling without need for SSH, features advanced features such as live preview)

The client software is written in Mono/C#. It can be used for sending commands or sending whole .svg files.
