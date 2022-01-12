from qgis.core import *
from algorithms.addition.Visualizer import Visualizer
from algorithms.addition.GridForRoadmap import GridForRoadmap
from algorithms.addition.CellOfTheGrid import CellOfTheGrid
from algorithms.addition.GeometryPointExpand import GeometryPointExpand
from algorithms.addition.Hall import Hall
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
import math


class AlgoritmsBasedOnHallAndGrid(SearchAlgorithm):
    def __init__(self, starting_point, target_point, obstacles, project):
        super().__init__(starting_point, target_point, obstacles, project)
        # constants
        self.const_square_meters = 400
        self.const_sight_of_points = 12
        self.step = 100  # step of the grid

        self.hall = Hall(self.starting_point.x(), self.starting_point.y(), self.target_point.x(), self.target_point.y())

        self.list_of_polygons = self.hall.create_list_of_polygons(obstacles, project)

        self.grid = self._create_grid()

    def _create_grid(self):
        self.left_x = min(self.hall.point1.x(), self.hall.point2.x(), self.hall.point3.x(), self.hall.point4.x())
        self.right_x = max(self.hall.point1.x(), self.hall.point2.x(), self.hall.point3.x(), self.hall.point4.x())
        self.bottom_y = min(self.hall.point1.y(), self.hall.point2.y(), self.hall.point3.y(), self.hall.point4.y())
        self.top_y = max(self.hall.point1.y(), self.hall.point2.y(), self.hall.point3.y(), self.hall.point4.y())

        number_of_rows = math.ceil((self.top_y - self.bottom_y) / self.step)
        number_of_columns = math.ceil((self.right_x - self.left_x) / self.step)
        grid = GridForRoadmap(number_of_rows, number_of_columns)
        print("rows: ", number_of_columns)
        print("columns: ", number_of_columns)
        lx = self.left_x
        ly = self.top_y
        a = 0
        coor_row = 0
        coor_column = 0
        for row in grid.cells:
            ry = ly - self.step
            if ry < self.bottom_y:
                ry = self.bottom_y
            rx = lx + self.step
            if rx > self.right_x:
                rx = self.right_x
            for _ in row:
                cell = CellOfTheGrid(lx, ly, rx, ry)
                grid.add_cell_by_coordinates(cell, coor_row, coor_column)
                lx += self.step
                rx += self.step
                coor_column += 1
                if rx > self.right_x:
                    rx = self.right_x
            ly -= self.step
            lx = self.left_x
            coor_column = 0
            coor_row += 1
        return grid

    def _get_shorter_path(self, feats, increase_points=0):
        # get shorter path
        min_path_geometry = [i.geometry() for i in feats]
        points = [i.asPolyline()[0] for i in min_path_geometry]
        # adding last point
        points.append(min_path_geometry[-1].asPolyline()[1])
        Visualizer.create_new_layer_points(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_point.shp",
                                           points)
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


        Visualizer.create_new_layer_points(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp",
                                           points)
        points_extended = []
        for point in points:
            point = QgsGeometry.fromPointXY(point)
            cell = self.grid.difine_point(point)
            point_extand = GeometryPointExpand(point, cell.n_row, cell.n_column)
            points_extended.append(point_extand)

        depth = 30

        list_min_path_indexes = [0]
        update_index = 1
        i = 0
        self.grid.vizualize(self.project)
        while i < len(points_extended):
            for k in range(i + 1, min(i + 1 + depth, len(points_extended))):
                line = QgsGeometry.fromPolylineXY([points_extended[i].point.asPoint(),
                                                   points_extended[k].point.asPoint()])

                geometry_obstacles = self.grid.get_multipolygon_by_points(points_extended[i],
                                                                          points_extended[k])

                # geometry_obstacles = self.grid.get_multipolygon_by_line(line)

                if geometry_obstacles.distance(line) > 0:
                    update_index = k
                else:
                    list_min_path_indexes.append(update_index)
                    i = update_index
                    i -= 1
                    break
            i += 1
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

        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_path.shp",
                                                    shortest_path_lines)

        return shortest_path_lines

    def _set_geometry_to_grid(self):
        # assign geometry to the cell
        for row in self.grid.cells:
            for cell in row:
                if cell.borders.distance(self.hall.hall_polygon) == 0:
                    cell.set_geometry(self.list_of_polygons)
