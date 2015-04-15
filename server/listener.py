from queue import Queue
import socketserver
import threading
import time
import signal
import sys
from hardware import Plotter, CommandError, NotCalibratedError

queue = Queue()


class TCPPlotterListener(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            print("{}:{} connected!".format(self.client_address[0], self.client_address[1]))
            while True:
                data = self.request.recv(1536)
                if data == b'\x00':
                    continue
                if not data:
                    break
                m = str(data, 'ascii')
                print("{} wrote: {}".format(self.client_address[0], m))
                queue.put((m, self.request))
        except Exception as e:
            print(e)
        finally:
            self.request.close()
            print(self.client_address[0] + " disconnected!")


def serve():
    host, port = "0.0.0.0", 9882
    server = socketserver.TCPServer((host, port), TCPPlotterListener)

    print("Listening on {}:{}".format(host, str(port)))
    print("Ctrl-C - quit")
    server.serve_forever()


def signal_handler(*args):
    print('\nCtrl-C pressed, quitting...!')
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    plotter = Plotter()
    thread = threading.Thread(target=serve)
    thread.daemon = True
    thread.start()
    while thread.isAlive:
        while queue.empty():
            time.sleep(0.1)
        comm_socket = queue.get()
        command = comm_socket[0]
        socket = comm_socket[1]

        socket.sendall(bytes("EXEC|" + command, "utf-8"))

        msg = ""
        success = False

        begintime = time.time()
        try:
            for result in plotter.execute(command):
                if result:
                    msg += str(result) + '\n'
            success = True
        except NotCalibratedError as ex:
            msg = str(ex) + " Use CAL <x> <y>"
        except CommandError as ex:
            msg = str(ex)
        endtime = time.time()

        if msg:
            msg = str(msg).strip()

        if success:
            info = "OK|{}|{}".format(command, "{:f} s".format(endtime - begintime))
        else:
            info = "ERR|{}".format(command)
            queue = Queue()

        if msg:
            info += "|" + msg

        print(info)
        socket.sendall(bytes(info, "utf-8"))
    thread.join(10)
