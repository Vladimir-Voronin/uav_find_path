import numpy as np
import math
from qgis.core import *


class AngleDistanceTransform:
    @staticmethod
    def transform_from_geometry_lines(list_of_geometry):
        info_list = []
        vertical = [0, 1]
        for i in range(len(list_of_geometry)):
            current_line = list_of_geometry[i].asPolyline()
            source = current_line[0]
            target = current_line[1]
            st = [target.x() - source.x(), target.y() - source.y()]
            angle = np.degrees(np.math.atan2(np.linalg.det([st, vertical]), np.dot(st, vertical)))
            distance = math.sqrt(st[0] ** 2 + st[1] ** 2)
            string = f"Distance: {distance}, angle: {angle}"
            print(string)
            info_list.append(string)
        return info_list

    @staticmethod
    def transform_from_qgsfeature_lines(list_if_feature):
        info_list = []
        vertical = [0, 1]
        for i in range(len(list_if_feature)):
            current_line = list_if_feature[i].geometry().asPolyline()
            source = current_line[0]
            target = current_line[1]
            st = [target.x() - source.x(), target.y() - source.y()]
            angle = np.degrees(np.math.atan2(np.linalg.det([st, vertical]), np.dot(st, vertical)))
            if angle < 0:
                angle = 360 + angle
            distance = math.sqrt(st[0] ** 2 + st[1] ** 2)
            string = f"Distance: {distance}, angle: {angle}"
            print(string)
            info_list.append(string)
        return info_list


if __name__ == "__main__":
    x = 10
    y = 20
    lines = []
    for i in range(5):
        point = QgsPointXY(x, y)
        point2 = QgsPointXY(x + 10, y + 10)
        line = QgsGeometry.fromPolylineXY([point, point2])
        lines.append(line)
        x += 10
        y += 10

    tr = AngleDistanceTransform.transform_from_geometry_lines(lines)
