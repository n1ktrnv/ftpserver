import socket

from ftpserver import STATUS_SUCCESS, STATUS_EMPTY_RESPONSE

IP = 'localhost'
PORT = 8080
EXIT = 'exit'
USERNAME = 'test'
PASSWORD = 'test'
TESTS = [
    {
        'command': 'makedir files',
        'result': None
    },
    {
        'command': 'makefile notes.txt',
        'result': None
    },
    {
        'command': 'ls',
        'result': 'files; notes.txt'
    },
    {
        'command': 'write notes.txt Hello, world!',
        'result': None
    },
    {
        'command': 'show notes.txt',
        'result': 'Hello, world!'
    },
    {
        'command': 'copy notes.txt files',
        'result': None
    },
    {
        'command': 'show files/notes.txt',
        'result': 'Hello, world!'
    },
    {
        'command': 'cd files',
        'result': None
    },
    {
        'command': 'pwd',
        'result': '/files'
    },
    {
        'command': 'move notes.txt ../notes2.txt',
        'result': None,
    },
    {
        'command': 'show ../notes2.txt',
        'result': 'Hello, world!',
    },
    {
        'command': 'exit'
    }
]


def auth(sock):
    username = USERNAME
    password = PASSWORD
    sock.send((username + ' ' + password).encode())
    response = sock.recv(1024)
    on_success(sock, username)


def on_success(sock, username):
    test_number = 1
    for test in TESTS:
        pwd = sock.recv(1024).decode()
        command = test['command']
        if command == EXIT:
            break
        sock.send(command.encode())
        response = sock.recv(1024)
        if response == STATUS_EMPTY_RESPONSE:
            response = None
        else:
            response = response.decode()
        print('Сервер:', response)
        print('Ожидалось:', test['result'])
        if response == test['result']:
            print(f'Тест{test_number} ({test["command"]}) успешно!')
        else:
            print(f'Тест{test_number} ({test["command"]}) провален!')
        print('------------')
        test_number += 1


def _main():
    sock = socket.socket()
    sock.connect((IP, PORT))
    auth(sock)
    sock.close()


if __name__ == '__main__':
    _main()