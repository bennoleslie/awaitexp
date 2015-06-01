from sched import scheduler, switch, sleep, io
import selectors
import socket
import resource

NUM_TESTERS = 50
SERVER_ADDR = ('localhost', 1234)
FMT = b"TEST%05d"
LEN = 9

async def echoclient(cid):
    sock = socket.socket()
    sock.setblocking(False)
    try:
        sock.connect(SERVER_ADDR)
    except BlockingIOError as e:
        pass

    for _ in range(10):
        await io(sock, selectors.EVENT_WRITE)
        testdata = FMT % cid
        sock.send(testdata)

        await io(sock, selectors.EVENT_READ)
        data = sock.recv(LEN)
        assert testdata == data, "Bad data: {} != {}".format(testdata, data)
        await sleep(0.2)

    sock.close()

for cid in range(NUM_TESTERS):
    scheduler.add_coro(echoclient(cid))

scheduler.run()
