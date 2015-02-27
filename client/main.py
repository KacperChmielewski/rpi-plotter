import threading
import tkinter as tk
from tkinter import messagebox
import socket


class Application(tk.Frame):
    socket = None

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack(expand=1, fill=tk.BOTH)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.createwidgets()
        self.create_connect_window()

    def createwidgets(self):
        self.create_command_frame()
        self.create_command_list()

    def create_command_frame(self):
        commandframe = tk.Frame(self)
        commandframe.columnconfigure(0, weight=1)
        commandframe.columnconfigure(1, minsize=5)
        self.commandentry = tk.Entry(commandframe)
        self.commandentry.bind('<Return>', self.send_command)
        commandlabel = tk.Label(commandframe, text="Send command")
        sendcommand_bt = tk.Button(commandframe, text='Send', command=self.send_command)

        sendcommand_bt.grid(column=2, row=1)
        commandlabel.grid(row=0, column=0, sticky='w', columnspan=3)
        self.commandentry.grid(column=0, row=1, sticky='we')
        commandframe.grid(row=1, padx=5, pady=5, sticky='we')

    def create_command_list(self):
        commandlist_frame = tk.Frame(self)
        commandlist_frame.columnconfigure(0, weight=1)
        self.commandlist = tk.Listbox(commandlist_frame, height=10)
        self.commandlist.bind('<Double-1>', self.enter_command)
        commandlist_scroll = tk.Scrollbar(commandlist_frame)
        commandlist_scroll.configure(command=self.commandlist.yview)
        self.commandlist.configure(yscrollcommand=commandlist_scroll.set)

        self.commandlist.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)
        commandlist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        commandlist_frame.grid(column=0, row=0, padx=5, pady=5, sticky='snwe')

    def create_connect_window(self):
        self.connectdialog = tk.Toplevel(self)
        self.connectdialog.transient(self)
        self.connectdialog.grab_set()
        self.connectdialog.wm_title("Connect to plotter")
        self.connectdialog.resizable(0, 0)
        l = tk.Label(self.connectdialog, text="Hostname:")
        l.grid(column=0, row=0, columnspan=3, sticky="w", padx=5, pady=5)
        self.hostname_entry = tk.Entry(self.connectdialog)
        self.hostname_entry.grid(column=0, row=1, padx=5, pady=5, columnspan=3)
        connectbt = tk.Button(self.connectdialog, text="Connect", command=self.connect, padx=5, pady=5)
        connectbt.grid(column=1, row=2)
        connectbt = tk.Button(self.connectdialog, text="Quit", command=self.quit, padx=5, pady=5)
        connectbt.grid(column=2, row=2)


    def connect(self):
        print("Connecting...")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            split_addr = self.hostname_entry.get().strip().split(':')
            if len(split_addr) > 1:
                split_addr[1] = int(split_addr[1])
            self.socket.connect(tuple(split_addr))
            threading.Thread(target=self.receive_from_server).start()
            self.socket.sendall(bytes(0))
        except Exception as ex:
            if self.socket:
                self.socket.close()
            messagebox.showerror(message=str(ex))
            return

        print("Connected!")
        self.connectdialog.destroy()

    def send_command(self, *args):
        command = self.commandentry.get().strip()
        if not command:
            return
        if not self.socket:
            self.create_connect_window()
            return

        command = command.upper()
        try:
            self.socket.sendall(bytes(command, "ascii"))
        except Exception as ex:
            self.socket.close()
            messagebox.showerror(message=str(ex))
            self.create_connect_window()
            return
        self.commandlist.insert(tk.END, command)
        self.commandentry.delete(0, tk.END)
        self.commandlist.yview(tk.END)

    def enter_command(self, *args):
        sel = self.commandlist.curselection()
        if len(sel) == 0:
            return
        self.commandentry.delete(0, tk.END)
        self.commandentry.insert(0, self.commandlist.get(sel))
        self.commandentry.focus()

    def receive_from_server(self):
        while True:
            try:
                received = str(self.socket.recv(1024), "utf-8")
                if received:
                    messagebox.showinfo(message='Server: ' + received)
            except Exception as ex:
                self.socket.close()
                messagebox.showerror(message=str(ex))
                self.create_connect_window()
                return

    def onquit(self):
        if self.socket:
            self.socket.close()
            root.destroy()


root = tk.Tk()
root.title("RPi Plotter Control Panel")
app = Application(master=root)
root.protocol("WM_DELETE_WINDOW", app.onquit)
app.mainloop()