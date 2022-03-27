from qgis.core import *


class CellOfTheGrid:
    def __init__(self, lx, by, rx, ty):
        self.point_lx_by = QgsPointXY(lx, by)
        self.point_rx_by = QgsPointXY(rx, by)
        self.point_rx_ty = QgsPointXY(rx, ty)
        self.point_lx_ty = QgsPointXY(lx, ty)
        self.borders = QgsGeometry.fromPolygonXY(
            [[self.point_lx_by, self.point_rx_by, self.point_rx_ty, self.point_lx_ty]])
        self.myGrid = None
        self.n_row = None
        self.n_column = None
        self.geometry = None
        self.number_of_polyg = 0

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
        return list_of_geom
