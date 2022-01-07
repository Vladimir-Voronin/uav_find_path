import math
import matplotlib.pyplot as plt
import numpy as np


class Checkhall:
    def __init__(self, start_x, start_y, target_x, target_y):
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y

    def get_hall(self):
        # объект будет хранить 4 точки, в конце возвратим прямоугольник
        hall = [[0, 0], [0, 0], [0, 0], [0, 0]]
        # Коэфицент расширение коридора в длину
        coef_length = 0.15
        # Фиксированная ширина коридора (деленная на 2)
        hall_width = 0.5

        # Далее:
        # Изначальный вектор - a
        # точка 1 расширенного вектора - x3, y3
        # точка 2 расширенного вектора - x4, y4
        # расширенный вектор - ev
        # длина вектора - 'name'_len

        x3 = self.start_x - (self.target_x - self.start_x) * coef_length
        y3 = self.start_y - (self.target_y - self.start_y) * coef_length
        x4 = self.target_x + (self.target_x - self.start_x) * coef_length
        y4 = self.target_y + (self.target_y - self.start_y) * coef_length

        ev = [x4 - x3, y4 - y3]
        ev_len = math.sqrt((x4 - x3) ** 2 + (y4 - y3) ** 2)
        # Высчитываем коэф уменьшения
        coef_decr = ev_len / hall_width

        ev_decr = [0, 0]
        ev_decr[0], ev_decr[1] = ev[0] / coef_decr, ev[1] / coef_decr

        cos_ev = ev[0] / ev_len
        sin_ev = ev[1] / ev_len
        Xp = hall_width * sin_ev
        Yp = hall_width * cos_ev

        # Точки расположены в порядке создания прямоугольника, ЭТО НЕ ТОЧКИ ЭТО ПРИРАЩЕНИЯ
        hall[0][0] = x3 + Xp
        hall[0][1] = y3 - Yp

        hall[1][0] = x3 - Xp
        hall[1][1] = y3 + Yp

        hall[2][0] = x4 - Xp
        hall[2][1] = y4 + Yp

        hall[3][0] = x4 + Xp
        hall[3][1] = y4 - Yp


if __name__ == "__main__":
    a = Checkhall(1, 2, 4, 3)
    result = a.get_hall()
    xs = []
    ys = []
    line, = plt.plot(xs, ys)
    plt.show()
    xs.append(1)
    xs.append(2)
    plt.draw()
