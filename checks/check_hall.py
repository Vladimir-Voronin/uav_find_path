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
        coef_length = 1.15
        # Фиксированная ширина коридора (деленная на 2)
        hall_width = 200

        # Далее:
        # Изначальный вектор - a
        # точка 1 расширенного вектора - x3, y3
        # точка 2 расширенного вектора - x4, y4
        # расширенный вектор - ev
        # длина вектора - 'name'_len
        line_length = ((self.target_x - self.start_x) ** 2 +
                       (self.target_y - self.start_y) ** 2) ** 0.5

        x3 = self.start_x + (self.target_x - self.start_x) * coef_length
        y3 = self.start_y + (self.target_y - self.start_y) * coef_length
        x4 = self.start_x - (self.target_x - self.start_x) * coef_length
        y4 = self.start_y - (self.target_y - self.start_y) * coef_length

        ev = [x4 - x3, y4 - y3]
        a_len = math.sqrt((self.target_x - self.start_x) ** 2 +
                          (self.target_y - self.start_y) ** 2)
        ev_len = math.sqrt((x4 - x3) ** 2 + (y4 - y3) ** 2)
        # Высчитываем коэф уменьшения
        coef_decr = ev_len / hall_width

        ev_decr = [0, 0]
        ev_decr[0], ev_decr[1] = ev[0] / coef_decr, ev[1] / coef_decr

        point_turn_x_1 = x3 + ev_decr[0]
        point_turn_y_1 = y3 + ev_decr[1]
        point_turn_x_2 = x4 - ev_decr[0]
        point_turn_y_2 = y4 - ev_decr[1]

        cos_ev = ev[0] / ev_len
        cos_ev = math.degrees(math.acos(cos_ev))
        angle_turn_1 = cos_ev + 90 if cos_ev + 90 < 360 else cos_ev + 90 - 360
        angle_turn_2 = cos_ev + 270 if cos_ev + 270 < 360 else cos_ev + 270 - 360

        # Точки расположены в порядке создания прямоугольника, ЭТО НЕ ТОЧКИ ЭТО ПРИРАЩЕНИЯ
        hall[0][0] = point_turn_x_1 * math.cos(angle_turn_1) + point_turn_y_1 * math.sin(angle_turn_1)
        hall[0][1] = point_turn_x_1 * math.sin(angle_turn_1) + point_turn_y_1 * math.cos(angle_turn_1)

        hall[1][0] = point_turn_x_1 * math.cos(angle_turn_2) + point_turn_y_1 * math.sin(angle_turn_2)
        hall[1][1] = point_turn_x_1 * math.sin(angle_turn_2) + point_turn_y_1 * math.cos(angle_turn_2)

        hall[2][0] = point_turn_x_2 * math.cos(angle_turn_2) + point_turn_y_2 * math.sin(angle_turn_2)
        hall[2][1] = point_turn_x_2 * math.sin(angle_turn_2) + point_turn_y_2 * math.cos(angle_turn_2)

        hall[3][0] = point_turn_x_2 * math.cos(angle_turn_1) + point_turn_y_2 * math.sin(angle_turn_1)
        hall[3][1] = point_turn_x_2 * math.sin(angle_turn_1) + point_turn_y_2 * math.cos(angle_turn_1)


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
