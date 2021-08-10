import threading


class Th(threading.Thread):
    def __init__(self, thr):
        threading.Thread.__init__(self)
        self.run = thr


@Th
def myth():
    print(1)


myth.start()
