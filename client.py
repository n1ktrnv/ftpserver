import socket

from ftpserver import STATUS_SUCCESS, STATUS_EMPTY_RESPONSE

IP = 'localhost'
PORT = 8080
EXIT = 'exit'


def auth(sock):
    username = input('Введите имя: ')
    password = input('Введите пароль: ')
    sock.send((username + ' ' + password).encode())
    response = sock.recv(1024)
    if response == STATUS_SUCCESS:
        on_success(sock, username)
    else:
        on_fail()


def on_success(sock, username):
    while True:
        pwd = sock.recv(1024).decode()
        command = input(get_invite(pwd, username))
        if command == EXIT:
            break
        sock.send(command.encode())
        response = sock.recv(1024)
        if response != STATUS_EMPTY_RESPONSE:
            print(response.decode())


def get_invite(pwd, username):
    return f'{username}:{pwd}$ '


def on_fail():
    print('Ошибка: доступ запрещен')


def _main():
    sock = socket.socket()
    sock.connect((IP, PORT))
    auth(sock)
    sock.close()


if __name__ == '__main__':
    _main()