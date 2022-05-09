import random


def select_sort(my_list):
    len_ = len(my_list)
    minimum = None
    for i in range(len_):
        minimum = i
        for k in range(i + 1, len_):
            if my_list[k] < my_list[minimum]:
                minimum = k
        my_list[i], my_list[minimum] = my_list[minimum], my_list[i]
    return my_list


def insert_sort(my_list):
    len_ = len(my_list)
    for i in range(len_ - 1):
        for k in range(i, -1, -1):
            if my_list[k + 1] < my_list[k]:
                my_list[k + 1], my_list[k] = my_list[k], my_list[k + 1]
            else:
                break
    return my_list


check_list = []

for i in range(10000):
    check_list.append(random.randint(0, 100000))
print(insert_sort(check_list))
