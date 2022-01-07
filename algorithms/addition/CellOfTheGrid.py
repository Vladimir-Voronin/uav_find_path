from qgis.core import *


class CellOfTheGrid:
    def __init__(self, lx, ly, rx, ry):
        point1 = QgsPointXY(lx, ly)
        point2 = QgsPointXY(rx, ly)
        point3 = QgsPointXY(rx, ry)
        point4 = QgsPointXY(lx, ry)
        self.borders = QgsGeometry.fromPolygonXY([[point1, point2, point3, point4]])
        self.myGrid = None
        self.n_row = None
        self.n_column = None
        self.geometry = None
        self.number_of_polyg = None

    def set_geometry(self, polygons):
        list_of_geom = []
        for polygon in polygons:
            if self.borders.distance(polygon) == 0.0:
                list_of_geom.append(polygon)

        self.number_of_polyg = len(list_of_geom)

        self.geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])
        for polygon in list_of_geom:
            if polygon is not None:
                self.geometry.addPartGeometry(polygon)
        self.geometry.deletePart(0)


