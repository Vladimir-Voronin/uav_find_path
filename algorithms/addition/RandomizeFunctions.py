from algorithms.addition import Hall
import random
from qgis.core import *
import math


class RandomizeFunctions:
    @staticmethod
    def get_points_around(source_point, distance, polygons):
        # source coordinates
        x_source = source_point.x()
        y_source = source_point.y()
        # angle
        f = 0
        shift = math.pi / 6
        points_around = []
        while f < 2 * math.pi:
            x = x_source + distance * math.cos(f)
            y = y_source + distance * math.sin(f)
            point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
            if polygons.distance(point) > 0.0:
                points_around.append(point)
            f += shift
        return points_around

    @staticmethod
    def get_random_points(hall, amount_of_points, polygons):
        list_of_points = []

        for i in range(amount_of_points):
            point = RandomizeFunctions.get_random_point(hall, polygons)
            list_of_points.append(point)

        return list_of_points

    @staticmethod
    def get_random_point(hall, polygons):
        x, y = RandomizeFunctions.get_random_point_coordinates_from_hall(hall)
        point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
        if polygons.distance(point) > 0.0:
            return point
        else:
            return RandomizeFunctions.get_random_point(hall, polygons)

    @staticmethod
    def get_random_point_coordinates_from_hall(hall):
        rand_0_1 = random.random()
        get_x_on_vector = hall.start_extended_point_x + (
                hall.target_extended_point_x - hall.start_extended_point_x) * rand_0_1
        get_y_on_vector = hall.start_extended_point_y + (
                hall.target_extended_point_y - hall.start_extended_point_y) * rand_0_1
        left_or_right = random.randint(0, 1)
        rand_shift = random.random()
        # Здесь мы получили нужный сдвиг, но формулы ниже не правильные! 08.01.2022
        if left_or_right == 0:
            x_point = get_x_on_vector + rand_shift * hall.Xp
            y_point = get_y_on_vector - rand_shift * hall.Yp
        else:
            x_point = get_x_on_vector - rand_shift * hall.Xp
            y_point = get_y_on_vector + rand_shift * hall.Yp

        return x_point, y_point
