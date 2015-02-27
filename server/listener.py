import socketserver
from plotter import Plotter

plotter = None


class TCPPlotterListener(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            print("{}:{} connected!".format(self.client_address[0], self.client_address[1]))
            while True:
                self.data = self.request.recv(1024).strip()
                if not len(self.data):
                    continue
                print("{} wrote:".format(self.client_address[0]))
                command = str(self.data, 'ascii')
                print(command)
                msg = plotter.exec(command)
                if msg is not None:
                    msg = str(msg).strip()
                    if msg != "":
                        self.request.sendall(bytes(msg, "utf-8"))
        except Exception as ex:
            print(ex)
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
