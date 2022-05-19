import math
import random
import time

from qgis._core import QgsGeometry, QgsPointXY, QgsApplication, QgsProject, QgsVectorLayer
import csv
from algorithms.GdalUAV.transformation.coordinates.CoordinateTransform import CoordinateTransform
from algorithms.GdalUAV.qgis.visualization.Visualizer import Visualizer


class PointsPare:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2


class PointsCreater:
    @staticmethod
    def create_points(number_of_points, length, access_min, access_max, obstacle, left_x, bottom_y, right_x, top_y):
        result_list = []
        while len(result_list) != number_of_points:
            r1 = random.random()
            new_x = left_x + (right_x - left_x) * r1
            r2 = random.random()
            new_y = bottom_y + (top_y - bottom_y) * r2
            if not access_min <= obstacle.distance(QgsGeometry.fromPointXY(QgsPointXY(new_x, new_y))) <= access_max:
                continue
            else:
                while True:
                    angle = random.random() * 360
                    rad = math.radians(angle)

                    Xp = length * math.sin(rad)
                    Yp = length * math.cos(rad)

                    if left_x <= new_x + Xp <= right_x and bottom_y <= new_y + Yp <= top_y:
                        if not access_min <= obstacle.distance(
                                QgsGeometry.fromPointXY(QgsPointXY(new_x + Xp, new_y + Yp))) <= access_max:
                            continue
                        else:
                            result_list.append(PointsPare(new_x, new_y, new_x + Xp, new_y + Yp))
                            break
                    else:
                        continue

        return result_list

    @staticmethod
    def create_points_for_station(number_of_points, length, access_min, access_max, obstacle, left_x, bottom_y, right_x,
                                  top_y, station_x, station_y):
        result_list = []
        while len(result_list) != number_of_points:
            new_x = station_x
            new_y = station_y
            while True:
                angle = random.random() * 360
                rad = math.radians(angle)

                Xp = length * math.sin(rad)
                Yp = length * math.cos(rad)

                if left_x <= new_x + Xp <= right_x and bottom_y <= new_y + Yp <= top_y:
                    if not access_min <= obstacle.distance(
                            QgsGeometry.fromPointXY(QgsPointXY(new_x + Xp, new_y + Yp))) <= access_max:
                        continue
                    else:
                        result_list.append(PointsPare(new_x, new_y, new_x + Xp, new_y + Yp))
                        break
                else:
                    continue

        return result_list

    @staticmethod
    def get_max_research_distance(left_x, bottom_y, right_x, top_y):
        x_full_difference = right_x - left_x
        y_full_difference = top_y - bottom_y
        result = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        result = (result * result) ** 0.5
        result /= 1.7
        integer_div = result // 100
        return 100 * integer_div

    @staticmethod
    def get_max_distance_from_station(left_x, bottom_y, right_x, top_y, station_x, station_y):
        result = 0
        first = [left_x, bottom_y]
        second = [right_x, bottom_y]
        third = [right_x, top_y]
        forth = [left_x, top_y]
        for point in [first, second, third, forth]:
            x_full_difference = station_x - point[0]
            y_full_difference = station_y - point[1]
            result_bef = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
            result_bef = (result_bef * result_bef) ** 0.5
            result = result_bef if result_bef > result else result
        result /= 1.7
        return result


if __name__ == "__main__":
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    my_time = time.perf_counter()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point1 = QgsGeometry.fromPointXY(QgsPointXY(4426633.9, 5957487.3))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(4426401.5, 5957303.1))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

    # create geometry obstacle
    obstacles = QgsVectorLayer(path)
    source_list_of_geometry_obstacles = CoordinateTransform.get_list_of_poligons_in_3395(obstacles, proj)

    list_of_geom = []
    for polygon in source_list_of_geometry_obstacles:
        list_of_geom.append(polygon)

    number_of_polyg = len(list_of_geom)
    print(number_of_polyg)

    geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])
    for polygon in list_of_geom:
        if polygon is not None:
            geometry.addPartGeometry(polygon)
    geometry.deletePart(0)

    # add point pares
    pointspares_list = []

    start_length = 100
    for i in range(20):
        new_list = PointsCreater.create_points(10, start_length, 10, 50, geometry)
        start_length += 100
        for i in new_list:
            pointspares_list.append(i)

    # visualise lines
    geometry_lines = []
    for pointspare in pointspares_list:
        line = QgsGeometry.fromPolylineXY([QgsPointXY(pointspare.x1, pointspare.y1),
                                           QgsPointXY(pointspare.x2, pointspare.y2)])
        geometry_lines.append(line)

    Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                geometry_lines)

    # append csv file with new points
    with open(r"C:\Users\Neptune\Desktop\points_auto.csv", 'w', newline='') as csvfile:
        fieldnames = ['first_point', 'second_point']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

        for pare in pointspares_list:
            writer.writerow({'first_point': f'{pare.x1}, {pare.y1}', 'second_point': f'{pare.x2}, {pare.y2}'})
