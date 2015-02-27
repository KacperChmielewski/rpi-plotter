import socketserver
import time
from plotter import Plotter, BadCommandError, NotCalibratedError

plotter = None


class TCPPlotterListener(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            print("{}:{} connected!".format(self.client_address[0], self.client_address[1]))
            while True:
                self.data = self.request.recv(1024)
                if not self.data:
                    break
                print("{} wrote:".format(self.client_address[0]))
                command = str(self.data, 'ascii')
                print(command)
                msg = None
                success = False

                begintime = time.time()
                try:
                    msg = plotter.exec(command)
                    success = True
                except BadCommandError:
                    msg = "Bad command"
                except NotCalibratedError:
                    msg = "Not calibrated! Use C [x] [y]"
                endtime = time.time()

                if msg is not None:
                    msg = str(msg).strip()

                if success:
                    info = "OK|{}|{}".format(command, "{:f} s".format(endtime - begintime))
                else:
                    info = "ERR|{}".format(command)

                if msg:
                    info += "|" + msg

                print("Return: " + info)
                self.request.sendall(bytes(info, "utf-8"))
        except Exception as ex:
            print(ex)
        self.request.close()
        print(self.client_address[0] + " disconnected!")

if __name__ == "__main__":
    plotter = Plotter()
    HOST, PORT = "0.0.0.0", 9882
    server = socketserver.TCPServer((HOST, PORT), TCPPlotterListener)

    print("Listening on {}:{}".format(HOST, str(PORT)))
    print("Ctrl-C - quit")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCtrl-C pressed, quitting...")
