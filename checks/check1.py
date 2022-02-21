from memory_profiler import memory_usage

mem1 = memory_usage()[0]
print(mem1)
b = []
for i in range(2000000):
    b.append(i)
b.clear()
mem2 = memory_usage()[0]
print(mem2)