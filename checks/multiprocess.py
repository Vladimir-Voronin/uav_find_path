import multiprocessing
import time

def foo(x, q):
    for i in range(x):
        time.sleep(1)
        q.put(i)

if __name__ == '__main__':
    queue = multiprocessing.Queue()
    procs = []
    for i in range(3):
        p = multiprocessing.Process(target=foo, args=(3, queue))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
    queue.put("Done")
    msg = 0
    while msg != "Done":
        msg = queue.get()
        print(msg)

