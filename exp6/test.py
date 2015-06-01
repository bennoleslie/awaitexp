"""An example server using async IO.

This is really just to demonstrate the 'io' coroutine. Directly using
recv() and send() without error checking as demonstrated here
shouldn't be done in real life code!

"""
from sched import scheduler, switch, sleep, io, background
import selectors
import socket
import resource
import time


BACKLOG = 100
SERVER_ADDR = ('localhost', 1234)
count = 0


@background
def add(x, y):
    time.sleep(0.4)
    return x + y


async def server():
    global count
    print("C1: Start server")

    # Setup a server socket.
    sock = socket.socket()
    sock.bind(SERVER_ADDR)
    sock.listen(BACKLOG)
    sock.setblocking(False)

    while True:
        await io(sock, selectors.EVENT_READ)
        conn, addr = sock.accept()
        print("Got connection: {} ({})".format(addr, count))
        scheduler.add_coro(echo(conn))
        count += 1


async def echo(conn):
    global count
    conn.setblocking(False)
    while True:
        # Note: this is not a good echo implementation!
        await io(conn, selectors.EVENT_READ)
        data = conn.recv(100)
        if not data:
            break
        x = await add(3, 5)  # Just here to test background functions!
        assert x == 8
        await io(conn, selectors.EVENT_WRITE)
        conn.send(data)
    conn.close()
    count -= 1

scheduler.add_coro(server())
scheduler.run()
