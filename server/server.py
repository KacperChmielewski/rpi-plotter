from queue import Queue
import socketserver
import socket as sock
import datetime
import threading
import signal
import logging
import sys

from plotter import *

server, socket = None, None
prop = None
queue = Queue()
starttime = None
logger = None
plotter = None


class TCPPlotterListener(socketserver.BaseRequestHandler):
    filereceive = False
    file = None

    def handle(self):
        global socket
        try:
            logger.info("{}:{} connected!".format(self.client_address[0], self.client_address[1]))
            socket = self.request
            while True:
                data = socket.recv(1024)
                if data == b'\x01':
                    continue
                if not data:
                    break
                m = str(data, 'ascii')
                logger.info("{} wrote: {}".format(self.client_address[0], m))

                if m == "!PANIC":
                    plotter.stopexecute()
                elif m == "!PAUSE":
                    plotter.setexecpause(True)
                elif m == "!UNPAUSE":
                    plotter.setexecpause(False)
                elif m == "!STATE":
                    self.sendstate()
                elif m == "!INFO":
                    self.sendinfo()
                elif m.startswith("FILE|"):
                    self.filereceive = True
                    self.file = m.lstrip("FILE|")
                elif m.endswith("|END") and self.filereceive:
                    self.file += m.rstrip("|END")
                    self.filereceive = False
                    queue.put(("FILE", self.file))
                elif self.filereceive:
                    self.file += m
                else:
                    queue.put(m.split('|'))
        except Exception as e:
            logger.error(str(e))
        finally:
            queue.queue.clear()
            socket.close()
            logger.info(self.client_address[0] + " disconnected!")

    def sendstate(self):
        info = "<b>Coordinate:</b> {0[0]:.2f}, {0[1]:.2f}\n" \
               "<b>Strings length:</b>\n\tLeft: {1[0]:.2f}\n\tRight: {1[1]:.2f}".format(plotter.getcoord(), hw.length)
        logger.debug(info)
        try:
            self.request.sendall(bytes("MSG|" + info + ';;', "utf-8"))
        except OSError:
            pass

    def sendinfo(self):
        import platform
        global starttime
        info = "Platform: " + platform.platform()
        uptime = datetime.datetime.now() - starttime
        info += "\nUptime: " + str(uptime)
        logger.debug(info)
        try:
            self.request.sendall(bytes("MSG|" + info + ';;', "utf-8"))
        except OSError:
            pass


def signal_handler(*args):
    print('\nCtrl-C pressed, quitting...')
    if socket:
        try:
            socket.shutdown(sock.SHUT_RDWR)
        except sock.error:
            pass
    sys.exit(0)


def serve():
    host, port = prop.host, int(prop.port)
    global server
    try:
        server = socketserver.TCPServer((host, port), TCPPlotterListener)

        logger.info("Listening on {}:{}".format(host, str(port)))
        server.serve_forever()
    except OSError as ex:
        logger.error(str(ex) + " - {}:{}".format(host, str(port)))


def process():
    global starttime
    starttime = datetime.datetime.now()
    thread = threading.Thread(target=serve)
    thread.setDaemon(True)
    thread.start()
    while thread.isAlive:
        if queue.empty():
            time.sleep(0.1)
            continue

        info, msg = '', ''
        index, command = queue.get()
        if index == "FILE":
            success = False

            def send_progress(current, total):
                progmsg = "FILE|PROGRESS|{}|{}".format(current, total)
                logger.debug(progmsg)
                socket.sendall(bytes(progmsg + ';;', "utf-8"))

            try:
                for result in plotter.execute(command, progress_cb=send_progress):
                    if result:
                        logger.info(str(result))
                success = True
            except OSError:
                continue
            except CommandError as ex:
                logger.error(str(ex))
                msg = str(ex)

            if success:
                info = "FILE|DONE"
            else:
                info = "FILE|FAIL"
        else:
            try:
                execmsg = "EXEC|" + index
                logger.debug(execmsg)
                socket.sendall(bytes(execmsg + ';;', "utf-8"))
            except OSError:
                continue
            # TODO: report position
            success = False

            begintime = time.time()
            try:
                for result in plotter.execute(command):
                    if result:
                        msg += str(result) + '\n'
                        logger.info(str(result))
                success = True
            except NotCalibratedError as ex:
                logger.error(str(ex))
                msg = str(ex) + " Use CAL <x>,<y>"
            except CommandError as ex:
                logger.error(str(ex))
                msg = str(ex)
            endtime = time.time()

            if msg:
                msg = str(msg).strip()

            if success:
                info = "OK|{}|{}".format(index, "{:f} s".format(endtime - begintime))
            else:
                info = "ERR|{}".format(index)
                queue.queue.clear()

        if msg:
            info += "|" + msg

        logger.debug(info)
        try:
            socket.sendall(bytes(info + ';;', "utf-8"))
        except OSError:
            continue


def main():
    parser = argparse.ArgumentParser(description="TCP/IP server for remote controlling vPlotter", add_help=False)
    parser.add_argument("--host", default="0.0.0.0", help='server address')
    parser.add_argument("--port", default=9882, help='server port')
    global plotter
    plotter = Plotter(parentparser=parser)
    global prop
    prop = parser.parse_known_args()[0]

    print("-= vPlotter Server =-\nCtrl+C - terminate\n")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    global logger
    logger = logging.getLogger("vPlotter.server")
    if not plotter.args.no_logging:
        fh = logging.FileHandler("server.log")
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s: %(message)s"))
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

    # logger.addHandler(logging.StreamHandler())
    process()

if __name__ == "__main__":
    try:
        main()
    finally:
        if plotter:
            plotter.shutdown()
