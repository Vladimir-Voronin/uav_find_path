import math
import sys
from abc import ABC
from qgis.core import *
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.GdalFPExtension.grid.CellOfTheGrid import CellOfTheGrid
from algorithms.GdalFPExtension.grid.GridForRoadmap import GridForRoadmap
import time


class AlgorithmsBasedOnFullObstaclesGeometryGrid(SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        super().__init__(findpathdata, debuglog)
        self.list_of_obstacles_geometry = findpathdata.source_list_of_geometry_obstacles
        self.step_of_the_grid = 100  # step of the grid
        self.left_x, self.right_x, self.bottom_y, self.top_y = None, None, None, None
        self.grid = self._create_grid()

    def _create_grid(self):
        print("check")

        multi_polygon_geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])

        for polygon in self.source_list_of_geometry_obstacles:
            multi_polygon_geometry.addPartGeometry(polygon)

        point_checker = QgsGeometry.fromPointXY(QgsPointXY(4428893.88140036724507809, 5954132.36808735784143209))
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4428893.88140036724507809, 5954132.36808735784143209)).asPoint()
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4428885.63262609764933586, 5954137.61756516434252262)).asPoint()
        multi_polygon_geometry.deletePart(0)
        checker = QgsGeometry.fromPolylineXY([point1, point2])
        my_time = time.perf_counter()
        for i in range(10):
            if multi_polygon_geometry.distance(checker):
                pass
        my_time = time.perf_counter() - my_time
        print(my_time)

        print("here")
        left_x = sys.float_info.max
        right_x = sys.float_info.min
        bottom_y = sys.float_info.max
        top_y = sys.float_info.min
        # This loop works enough fast
        for obstacle in self.source_list_of_geometry_obstacles:
            for polygon in obstacle.asPolygon():
                for point in polygon:
                    if point.x() < left_x:
                        left_x = point.x()
                    if point.x() > right_x:
                        right_x = point.x()
                    if point.y() < bottom_y:
                        bottom_y = point.y()
                    if point.y() > top_y:
                        top_y = point.y()
        if left_x == sys.float_info.max or right_x == sys.float_info.min or bottom_y == sys.float_info.max or \
                top_y == sys.float_info.min:
            if len(self.source_list_of_geometry_obstacles) == 0:
                return GridForRoadmap(0, 0)
            else:
                raise Exception("Problem with geometry of obstacles layer")

        self.left_x, self.right_x, self.bottom_y, self.top_y = left_x, right_x, bottom_y, top_y

        number_of_rows = math.ceil((self.top_y - self.bottom_y) / self.step_of_the_grid)
        number_of_columns = math.ceil((self.right_x - self.left_x) / self.step_of_the_grid)
        grid = GridForRoadmap(number_of_rows, number_of_columns)
        print("rows: ", number_of_columns)
        print("columns: ", number_of_columns)
        bx = self.left_x
        ty = self.top_y
        coor_row = 0
        coor_column = 0
        for row in grid.cells:
            ry = ty - self.step_of_the_grid
            if ry < self.bottom_y:
                ry = self.bottom_y
            rx = bx + self.step_of_the_grid
            if rx > self.right_x:
                rx = self.right_x
            for _ in row:
                cell = CellOfTheGrid(bx, ty, rx, ry)
                grid.add_cell_by_coordinates(cell, coor_row, coor_column)
                bx += self.step_of_the_grid
                rx += self.step_of_the_grid
                coor_column += 1
                if rx > self.right_x:
                    rx = self.right_x
            ty -= self.step_of_the_grid
            coor_column = 0
            coor_row += 1

        return grid

    def _set_geometry_to_grid(self):
        # assign geometry to the cell
        for row in self.grid.cells:
            for cell in row:
                cell.set_geometry(self.list_of_obstacles_geometry)

    def _get_shorter_path(self, feats, increase_points=0):
        pass