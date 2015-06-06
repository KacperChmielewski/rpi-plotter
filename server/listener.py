from queue import Queue
import socketserver
import socket as sock
import threading
import time
import signal
import sys
from hardware import Plotter, CommandError, NotCalibratedError

queue = Queue()
server, socket = None, None

class TCPPlotterListener(socketserver.BaseRequestHandler):
    def handle(self):
        global socket
        try:
            print("{}:{} connected!".format(self.client_address[0], self.client_address[1]))
            socket = self.request
            while True:
                data = socket.recv(8192)
                if data == b'\x01':
                    continue
                if not data:
                    break
                m = str(data, 'ascii')
                print("{} wrote: {}".format(self.client_address[0], m))

                if m == "!PANIC":
                    plotter.stopexecute()
                elif m == "!PAUSE":
                    plotter.setexecpause(True)
                elif m == "!UNPAUSE":
                    plotter.setexecpause(False)
                else:
                    queue.put(m)
        except Exception as e:
            print(e)
        finally:
            queue.queue.clear()
            socket.close()
            print(self.client_address[0] + " disconnected!")


def serve():
    host, port = "0.0.0.0", 9882
    global server
    server = socketserver.TCPServer((host, port), TCPPlotterListener)

    print("Listening on {}:{}".format(host, str(port)))
    server.serve_forever()


def signal_handler(*args):
    print('\nCtrl-C pressed, quitting...')
    if socket:
        try:
            socket.shutdown(sock.SHUT_RDWR)
        except sock.error:
            pass
    if plotter:
        plotter.shutdown()
    sys.exit(0)


if __name__ == "__main__":
    print("-= vPlotter Network Listener =-\nCtrl+C - terminate\n")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    plotter = Plotter()
    thread = threading.Thread(target=serve)
    thread.setDaemon(True)
    thread.start()
    while thread.isAlive:
        if queue.empty():
            time.sleep(0.1)
            continue

        command = queue.get()

        try:
            socket.sendall(bytes("EXEC|" + command + ';;', "utf-8"))
        except OSError:
            continue
        # TODO: report position
        msg = ""
        success = False

        begintime = time.time()
        try:
            for result in plotter.execute(command):
                if result:
                    msg += str(result) + '\n'
            success = True
        except NotCalibratedError as ex:
            msg = str(ex) + " Use CAL <x>,<y>"
        except CommandError as ex:
            msg = str(ex)
        endtime = time.time()

        if msg:
            msg = str(msg).strip()

        if success:
            info = "OK|{}|{}".format(command, "{:f} s".format(endtime - begintime))
        else:
            info = "ERR|{}".format(command)
            queue.queue.clear()

        if msg:
            info += "|" + msg

        print(info)
        try:
            socket.sendall(bytes(info + ';;', "utf-8"))
        except OSError:
            continue
    thread.join(10)
