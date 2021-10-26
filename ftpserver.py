import socket
from pathlib import Path
from enum import Enum

from filemanager import FileManager
from users_storage import JSONUsersStorage
from logger import TXTLogger


STATUS_SUCCESS = b'1'
STATUS_EMPTY_RESPONSE = b'0'
ADMIN_USERNAME = 'admin'


class Commands(Enum):
    MAKE_DIR = 'makedir'
    MAKE_FILE = 'makefile'
    CD = 'cd'
    WRITE_FILE = 'write'
    SHOW_FILE = 'show'
    DEL = 'del'
    COPY = 'copy'
    MOVE = 'move'
    FREE = 'free'
    EXIT = 'exit'


class FTPServer:
    def __init__(self, file_manager, users, logger, port=8080,
                 location='storage', size=None):
        self._users = users
        self._file_manager = file_manager
        self._logger = logger
        self._location = Path(location).resolve()
        self._root = Path.cwd().resolve()
        if not self._location.is_dir():
            self._location.mkdir(parents=True)
        self._size = size
        self._socket = socket.socket()
        self._socket.bind(('', port))
        self._socket.listen()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def users(self):
        return self._users

    @property
    def location(self):
        return self._location

    def start(self):
        while True:
            self.accept()

    def accept(self):
        conn, addr = self._socket.accept()
        self.log(f'Клиент {addr} подключен')
        FTPServerHandler(conn, addr, self, self._file_manager,
                         self._size).handle()

    def log(self, message, back_path=None):
        self._logger.log(message)


    def close(self):
        self._socket.close()


class FTPServerHandler:

    def __init__(self, conn, addr, server, file_manager, size):
        self._socket = conn
        self._ip = addr[0]
        self._port = addr[1]
        self._server = server
        self._file_manager = file_manager
        self._size = size

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def handle(self):
        self.auth()

    def auth(self):
        username, password = self.recv_text().split()
        if self._server.users.exists(username):
            if password == self._server.users.get_password(username):
                self.on_success(username)
            else:
                self.on_fail()
        else:
            self._server.users.add(username, password)
            self.on_success(username)

    def on_success(self, username):
        self._server.log(f'Пользователь {username} авторизован')
        self._socket.send(STATUS_SUCCESS)
        if username == ADMIN_USERNAME:
            user_dir = self._server.location
        else:
            user_dir = Path(self._server.location, username)
        file_manager = self._file_manager(user_dir, self._size)
        while True:
            self.send_text(file_manager.pwd())
            request = self.recv_text()
            if not request:
                break
            response = self.process_request(file_manager, request, username)
            if response:
                self.send_text(response)
            else:
                self._socket.send(STATUS_EMPTY_RESPONSE)

    def process_request(self, file_manager, request, username):
        try:
            command, args = request.split(maxsplit=1)
        except ValueError:
            command, args = request, ''
        if command == 'pwd':
            return file_manager.pwd()
        elif command == 'ls':
            return file_manager.ls()
        elif command == 'makedir':
            path = args.split()[0]
            self._server.log(f'Пользователь {username} создал папку {path}')
            return file_manager.make_dir(path)
        elif command == 'makefile':
            path = args.split()[0]
            self._server.log(f'Пользователь {username} создал файл {path}')
            return file_manager.make_file(path)
        elif command == 'cd':
            path = args.split()[0]
            return file_manager.cd(path)
        elif command == 'write':
            path, text = args.split(maxsplit=1)
            self._server.log(
                f'Пользователь {username} записал текст в файл {path}')
            return file_manager.write(path, text)
        elif command == 'show':
            path = args.split()[0]
            return file_manager.read(path)
        elif command == 'del':
            path = args.split()[0]
            self._server.log(f'Пользователь {username} удалил файл {path}')
            return file_manager.delete(path)
        elif command == 'copy':
            src_path = args.split()[0]
            dst_path = args.split()[1]
            self._server.log(f'Пользователь {username} скопировал файл '
                             f'{src_path} в {dst_path}')
            return file_manager.copy(src_path, dst_path)
        elif command == 'move':
            src_path = args.split()[0]
            dst_path = args.split()[1]
            self._server.log(f'Пользователь {username} переместил файл '
                             f'{src_path} в {dst_path}')
            return file_manager.move(src_path, dst_path)
        elif command == 'free':
            return file_manager.free()
        else:
            return 'Неверная команда'

    def on_fail(self):
        self.send_null()

    def send_null(self):
        self._socket.send(b'')

    def recv_text(self, bufsize=1024, encoding='utf-8'):
        return self._socket.recv(bufsize).decode(encoding)

    def send_text(self, data, encoding='utf-8'):
        self._socket.send(data.encode(encoding))

    def close(self):
        self._socket.close()


def _main():
    users = JSONUsersStorage('users.json')
    logger = TXTLogger('logs.txt')
    with FTPServer(FileManager, users, logger) as server:
        server.start()


if __name__ == '__main__':
    _main()
