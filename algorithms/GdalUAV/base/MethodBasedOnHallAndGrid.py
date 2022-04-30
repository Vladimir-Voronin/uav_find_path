from abc import ABC

from qgis.core import *

from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.GdalUAV.processing.Converter import ObjectsConverter
from algorithms.GdalUAV.processing.grid.GridForRoadmap import GridForRoadmap
from algorithms.GdalUAV.processing.grid.CellOfTheGrid import CellOfTheGrid
from algorithms.GdalUAV.processing.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalUAV.processing.grid.Hall import Hall
from algorithms.GdalUAV.base.SearchMethodBase import SearchMethodBase
import math


class MethodBasedOnHallAndGrid(SearchMethodBase, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog, hall_width=150):
        super().__init__(findpathdata, debuglog)
        # constants
        self.const_square_meters = 400
        self.const_sight_of_points = 12
        self.step_of_the_grid = 100  # step of the grid
        self.numbers_of_geom = 0

        self.time_to_succeed = findpathdata.time_to_succeed
        self.hall = Hall(self.starting_point.x(), self.starting_point.y(), self.target_point.x(), self.target_point.y(),
                         hall_width)
        if self.source_list_of_geometry_obstacles is None:
            self.list_of_obstacles_geometry = self.hall.create_list_of_obstacles(self.obstacles, self.project)
        else:
            self.list_of_obstacles_geometry = self.hall.create_list_of_polygons_by_source_geometry(
                self.source_list_of_geometry_obstacles)

        self.left_x, self.right_x, self.bottom_y, self.top_y = None, None, None, None
        self.grid = self._create_grid()

    def _create_grid(self):
        self.left_x = min(self.hall.point1.x(), self.hall.point2.x(), self.hall.point3.x(), self.hall.point4.x())
        self.right_x = max(self.hall.point1.x(), self.hall.point2.x(), self.hall.point3.x(), self.hall.point4.x())
        self.bottom_y = min(self.hall.point1.y(), self.hall.point2.y(), self.hall.point3.y(), self.hall.point4.y())
        self.top_y = max(self.hall.point1.y(), self.hall.point2.y(), self.hall.point3.y(), self.hall.point4.y())

        number_of_rows = math.ceil((self.top_y - self.bottom_y) / self.step_of_the_grid)
        number_of_columns = math.ceil((self.right_x - self.left_x) / self.step_of_the_grid)

        grid = GridForRoadmap(number_of_rows, number_of_columns, self.step_of_the_grid, self.bottom_y, self.left_x)

        lx = self.left_x
        by = self.bottom_y
        coor_row = 0
        coor_column = 0
        for row in grid.cells:
            ty = by + self.step_of_the_grid
            if ty > self.top_y:
                ty = self.top_y
            rx = lx + self.step_of_the_grid
            if rx > self.right_x:
                rx = self.right_x
            for _ in row:
                cell = CellOfTheGrid(lx, by, rx, ty)
                grid.add_cell_by_coordinates(cell, coor_row, coor_column)
                lx += self.step_of_the_grid
                rx += self.step_of_the_grid
                coor_column += 1
                if rx > self.right_x:
                    rx = self.right_x
            by += self.step_of_the_grid
            lx = self.left_x
            coor_column = 0
            coor_row += 1
        grid.visualize(self.project)

        return grid

    def _get_shorter_path(self, feats_or_geometry, increase_points=0, depth=30):
        if type(feats_or_geometry[0]) == QgsFeature:
            # get shorter path
            min_path_geometry = [i.geometry() for i in feats_or_geometry]
        else:
            min_path_geometry = feats_or_geometry
        points = [i.asPolyline()[0] for i in min_path_geometry]
        # adding last point
        points.append(min_path_geometry[-1].asPolyline()[1])
        # increase points in path to get shorter path
        i = 0
        while i < len(points) - 1:
            for k in range(increase_points):
                coef_multi = (k + 1) / (increase_points + 1)
                x = points[i].x() + (points[i + 1 + k].x() - points[i].x()) * coef_multi
                y = points[i].y() + (points[i + 1 + k].y() - points[i].y()) * coef_multi
                point = QgsPointXY(x, y)
                points.insert(i + k + 1, point)
            i += increase_points + 1

        points_extended = []
        for point in points:
            point = QgsGeometry.fromPointXY(point)
            cell = self.grid.difine_point(point)
            point_extand = GeometryPointExpand(point, cell.n_row, cell.n_column)
            points_extended.append(point_extand)

        list_min_path_indexes = [0]
        update_index = 0
        i = 0
        current_index = 0
        list_min_path_indexes.append(current_index)
        while current_index < len(points_extended) - 1:
            next_index = current_index + 1
            for k in range(current_index + 2, min(current_index + 2 + depth, len(points_extended))):
                line = QgsGeometry.fromPolylineXY([points_extended[current_index].point.asPoint(),
                                                           points_extended[k].point.asPoint()])

                geometry_obstacles = self.grid.get_multipolygon_by_points(points_extended[current_index],
                                                                          points_extended[k])

                if geometry_obstacles.isNull() or geometry_obstacles.distance(line) > 0:
                    next_index = k
                else:
                    break
            current_index = next_index
            list_min_path_indexes.append(current_index)

        if len(points_extended) - 1 != list_min_path_indexes[-1]:
            list_min_path_indexes.append(len(points_extended) - 1)

        a = 0
        while a + 1 < len(list_min_path_indexes):
            if list_min_path_indexes[a] == list_min_path_indexes[a + 1]:
                list_min_path_indexes.remove(list_min_path_indexes[a])
                a -= 1
            a += 1

        shortes_min_path_points = [points_extended[i] for i in list_min_path_indexes]
        shortest_path_lines = []
        for i in range(len(shortes_min_path_points) - 1):
            line = QgsGeometry.fromPolylineXY([shortes_min_path_points[i].point.asPoint(),
                                               shortes_min_path_points[i + 1].point.asPoint()])
            shortest_path_lines.append(line)

        result_feats = ObjectsConverter.list_of_geometry_to_feats(shortest_path_lines)

        return result_feats

    def _set_geometry_to_grid(self):
        # assign geometry to the cell
        for row in self.grid.cells:
            for cell in row:
                a = cell.borders.intersection(self.hall.hall_polygon)
                if not cell.borders.intersection(self.hall.hall_polygon).isEmpty():
                    list_of_inter_geom = cell.set_geometry(self.list_of_obstacles_geometry)
                    self.numbers_of_geom += len(list_of_inter_geom)

    def get_area_precents(self):
        polygons_area = 0
        for i in self.list_of_obstacles_geometry:
            polygons_area += i.area()
        return polygons_area / self.hall.hall_polygon.area()