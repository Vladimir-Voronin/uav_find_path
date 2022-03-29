import math
import random
import time

from qgis._core import QgsGeometry, QgsPointXY, QgsApplication, QgsProject, QgsVectorLayer
import csv
from ModuleInstruments.Converter import Converter
from algorithms.GdalFPExtension.qgis.visualization.Visualizer import Visualizer


class PointsPare:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2


class Creater:
    @staticmethod
    def create_points(number_of_points, length, access, more_access, obstacle):
        left_x = 4426099.4
        right_x = 4429344.6
        bottom_y = 5954710.6
        top_y = 5957673.6

        result_list = []
        while len(result_list) != number_of_points:
            r1 = random.random()
            new_x = left_x + (right_x - left_x) * r1
            r2 = random.random()
            new_y = bottom_y + (top_y - bottom_y) * r2
            point = QgsGeometry.fromPointXY(QgsPointXY(new_x, new_y))
            dis = obstacle.distance(QgsGeometry.fromPointXY(QgsPointXY(new_x, new_y)))

            if not access <= obstacle.distance(QgsGeometry.fromPointXY(QgsPointXY(new_x, new_y))) <= more_access:
                continue
            else:
                while True:
                    angle = random.random() * 360
                    rad = math.radians(angle)

                    Xp = length * math.sin(rad)
                    Yp = length * math.cos(rad)

                    if left_x <= new_x + Xp <= right_x and bottom_y <= new_y + Yp <= top_y:
                        if not access <= obstacle.distance(
                                QgsGeometry.fromPointXY(QgsPointXY(new_x + Xp, new_y + Yp))) <= more_access:
                            continue
                        else:
                            result_list.append(PointsPare(new_x, new_y, new_x + Xp, new_y + Yp))
                            break
                    else:
                        continue

        return result_list


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
    source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)

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
        new_list = Creater.create_points(10, start_length, 10, 50, geometry)
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
