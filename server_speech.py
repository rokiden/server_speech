import json
import socket
import threading
from playsound import playsound
from gtts import gTTS
import os
import hashlib

separators = (',', ':')


class ServerSpeech:
    def __init__(self, port, cache_folder='tts_cache'):
        self.tcp_port = port
        self.verbose = False
        self.cache_folder = cache_folder
        try:
            os.mkdir(cache_folder)
        except Exception:
            pass
        self.lock = threading.Lock()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', self.tcp_port))
        self.sock.listen(10)

    def __del__(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def listen(self):
        print('listen :%d' % self.tcp_port)
        while True:
            client_sock, address = self.sock.accept()
            client_handler = threading.Thread(
                target=self.handle,
                args=(client_sock, address)
            )
            client_handler.start()

    def cmd(self, line):
        obj = json.loads(line)
        print(obj)
        h = hashlib.md5(obj['text'].encode('UTF-8')).hexdigest()
        filename = h + '.mp3'
        if not filename in os.listdir(self.cache_folder):
            print('generate file')
            tts = gTTS(obj['text'], lang=obj['lang'])
            tts.save(self.cache_folder + '\\' + filename)
        playsound(self.cache_folder + '\\' + filename)

    def handle(self, sock: socket.SocketType, addr):
        print('connected', addr)
        buf = ""
        while True:
            try:
                data = bytes(sock.recv(4096))
                data = data.decode('UTF-8')
                buf += data

                while True:
                    idx = buf.find('\n')
                    if idx < 0:
                        break
                    part = buf[:idx]
                    if part:
                        try:
                            self.cmd(part)
                        except Exception as e:
                            print('exc: ' + str(e))
                    buf = buf[idx + 1:]
            except ConnectionResetError:
                print('closed', addr)
                break


class ServerSpeechClient:
    def __init__(self, ip, port):
        self.tcp_ip = ip
        self.tcp_port = port
        self.verbose = False
        self.sock: socket.SocketType = None
        self.sock_init()

    def sock_init(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3)
            self.sock.connect((self.tcp_ip, self.tcp_port))
            print('connected', self.tcp_ip, self.tcp_port)
        except Exception as e:
            self.sock = None
            raise e

    def send(self, text, lang='en'):
        msg = json.dumps({'lang': lang, 'text': text}, separators=separators) + '\n'
        msg = msg.encode('UTF-8')

        if self.sock is None:
            self.sock_init()
        try:
            self.sock.send(msg)
        except ConnectionResetError:
            print('reconnect')
            self.sock_init()
            self.sock.send(msg)


if __name__ == '__main__':
    serv = ServerSpeech(1488)
    serv.listen()
