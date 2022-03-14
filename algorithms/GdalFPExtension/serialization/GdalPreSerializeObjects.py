from qgis.core import *


class QgsPointXYSerialize:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_pointXY(self):
        return QgsPointXY(self.x, self.y)


class QgsPolygonSerialize:
    def __init__(self, list_of_points: [QgsPointXYSerialize]):
        self.list_of_points = list_of_points

    def get_polygon(self):
        real_points = []
        for i in self.list_of_points:
            real_points.append(i.get_pointXY())
        return QgsGeometry.fromPolygonXY([real_points])
