import time
from memory_profiler import memory_usage


class DebugLog:
    def __init__(self):
        # save info
        self.__info = ""

        # Time
        # key=name_of_block, value=block time start
        self.__dictinary_start_time = {}
        # key=name_of_block, value endblock time - block time start.
        # Use to take time of particular block
        self.__dictinary_execute_time = {}

        # Memory
        # key=name_of_block, value=block memory start
        self.__dictinary_start_memory = {}
        # key=name_of_block, value endblock memory - block memory start.
        # Use to take memory of particular block
        self.__dictinary_execute_memory = {}

    def info(self, message: str):
        self.__info += '\n'
        self.__info += message

    def start_time_block(self, name: str):
        if name in self.__dictinary_start_time or name in self.__dictinary_execute_time:
            raise Exception("This time measure name of the block already used")
        self.__dictinary_start_time[name] = time.perf_counter()

    def end_time_block(self, name: str, to_info_at_ones=True):
        if name not in self.__dictinary_start_time:
            raise Exception("This time measure block hasn't been started")
        if name in self.__dictinary_execute_time:
            raise Exception("This time measure block already ended")

        self.__dictinary_execute_time[name] = time.perf_counter() - self.__dictinary_start_time[name]
        if to_info_at_ones:
            self.info(f'Block "{name}" worked for {self.__dictinary_execute_time[name]} s.')

    def start_memory_block(self, name: str):
        if name in self.__dictinary_start_memory or name in self.__dictinary_execute_memory:
            raise Exception("This name of the memory measure block already used")
        self.__dictinary_start_memory[name] = memory_usage()

    def end_memory_block(self, name: str, to_info_at_ones=True):
        if name not in self.__dictinary_start_memory:
            raise Exception("This memory measure block hasn't been started")
        if name in self.__dictinary_execute_memory:
            raise Exception("This memory measure block already ended")

        self.__dictinary_execute_memory[name] = memory_usage() - self.__dictinary_start_memory[name]
        if to_info_at_ones:
            self.info(f'Block "{name}" worked for {self.__dictinary_execute_memory[name]} MiB')

    # Measure time and memory together, start block
    def start_block(self, name: str):
        self.start_time_block(name)
        self.start_memory_block(name)

    # Measure time and memory together, end block
    def end_block(self, name: str, to_info_at_ones=True):
        self.end_time_block(name, to_info_at_ones)
        self.end_memory_block(name, to_info_at_ones)
