import math


def get_distance(point_1, point_2):
    x_full_difference = point_2.x() - point_1.x()
    y_full_difference = point_2.y() - point_1.y()
    result = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
    return (result * result) ** 0.5