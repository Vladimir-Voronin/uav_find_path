from memory_profiler import profile, memory_usage
import tracemalloc


class Test:
    def __init__(self):
        self.my_list = []

    def run(self):
        # starting the monitoring
        tracemalloc.start()
        for i in range(10000):
            self.my_list.append([i, i, i])
            print(tracemalloc.get_traced_memory())
            # stopping the library
        tracemalloc.stop()


a = Test()
a.run()
