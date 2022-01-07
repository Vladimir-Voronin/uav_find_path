from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy, QgsGraphAnalyzer
# uav_find_path.algorithms.abstract
from algorithms.abstract.SearchMethod import SearchMethodAbstract
from algorithms.addition.QgsGraphSearcher import QgsGraphSearcher
from algorithms.addition.GridForRoadmap import GridForRoadmap
from algorithms.addition.CellOfTheGrid import CellOfTheGrid
import math
import random
import functools
import time
import multiprocessing
import sys
import math
import ogr
import numpy as np


class GeometryPointExpand:
    current_id = -1

    def __init__(self, point, n_row, n_column):
        GeometryPointExpand.current_id += 1
        self.point = point
        self.n_row = n_row
        self.n_column = n_column
        self.id = GeometryPointExpand.current_id


class RandomizedRoadmapGridMethod(SearchMethodAbstract):
    def __init__(self, starting_point, target_point, obstacles, project):
        # constants
        self.const_square_meters = 400
        self.const_sight_of_points = 12
        self.step = 100  # step of the grid
        self.hall_width = 200

        # others
        self.current_id = 0
        self.obstacles = obstacles  # type: QgsVectorLayer
        self.project = project

        # transform to EPSG 3395
        # need to change "project" to "QgsProject.instance" when import to module
        transformcontext = project.transformContext()
        general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
        xform = QgsCoordinateTransform(self.obstacles.crs(), general_projection, transformcontext)

        # type: QgsPointXY
        self.starting_point = xform.transform(starting_point.asPoint())
        self.target_point = xform.transform(target_point.asPoint())

        # type: QgsGeometry
        self.starting_point_geometry = QgsGeometry.fromPointXY(QgsPointXY(self.starting_point.x(),
                                                                          self.starting_point.y()))
        self.target_point_geometry = QgsGeometry.fromPointXY(QgsPointXY(self.target_point.x(),
                                                                        self.target_point.y()))

        # borders coordinates
        self.left_x, self.right_x, self.bottom_y, self.top_y = self.__get_borders()

        # get mulmultipolygon layer
        self.list_of_polygons = RandomizedRoadmapGridMethod.__create_polygons_geometry(obstacles, self.left_x,
                                                                                       self.right_x,
                                                                                       self.bottom_y, self.top_y,
                                                                                       project)
        self.grid = self.__create_grid()

    def __create_grid(self):
        number_of_rows = math.ceil((self.top_y - self.bottom_y) / self.step)
        number_of_columns = math.ceil((self.right_x - self.left_x) / self.step)
        print(self.top_y - self.bottom_y)
        print(self.right_x - self.left_x)
        grid = GridForRoadmap(number_of_rows, number_of_columns)
        print("SP1")
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
                cell.set_geometry(self.list_of_polygons)
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

    @staticmethod
    def __create_polygons_geometry(obstacles, left_x, right_x, bottom_y, top_y, project):
        features = obstacles.getFeatures()

        list_of_geometry = []
        list_of_polygons = []
        # Data for transform to EPSG: 3395
        transformcontext = project.transformContext()
        source_projection = obstacles.crs()
        general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
        xform = QgsCoordinateTransform(source_projection, general_projection, transformcontext)
        for feature in features:
            geom = feature.geometry()

            # Transform to EPSG 3395
            check = geom.asGeometryCollection()[0].asPolygon()
            list_of_points_to_polygon = []
            for point in check[0]:
                point = xform.transform(point.x(), point.y())
                list_of_points_to_polygon.append(point)

            create_polygon = QgsGeometry.fromPolygonXY([list_of_points_to_polygon])
            list_of_geometry.append(create_polygon)
        polygon = QgsGeometry.fromPolygonXY([[QgsPointXY(left_x, bottom_y),
                                              QgsPointXY(right_x, bottom_y),
                                              QgsPointXY(right_x, top_y),
                                              QgsPointXY(left_x, top_y)]])

        list_of_geometry_handled = []
        for geometry in list_of_geometry:
            if polygon.distance(geometry) == 0.0:
                list_of_geometry_handled.append(geometry)
        # because we cant add Part of geometry to empty OgsGeometry instance
        print(list_of_geometry_handled)
        return list_of_geometry_handled

    def _get_hall(self):
        print("ALALALALALALALA"
              "ALALALALALLALAL"
              "ALALLALALALALALAL")
        # объект будет хранить 4 точки, в конце возвратим прямоугольник
        hall = [[0, 0], [0, 0], [0, 0], [0, 0]]
        # Коэфицент расширение коридора в длину
        coef_length = 0.15
        # Фиксированная ширина коридора (деленная на 2)
        hall_width = 200

        # Далее:
        # Изначальный вектор - a
        # точка 1 расширенного вектора - x3, y3
        # точка 2 расширенного вектора - x4, y4
        # расширенный вектор - ev
        # длина вектора - 'name'_len
        line_length = ((self.target_point.x() - self.starting_point.x()) ** 2 +
                       (self.target_point.y() - self.starting_point.y()) ** 2) ** 0.5

        x3 = self.starting_point.x() - (self.target_point.x() - self.starting_point.x()) * coef_length
        y3 = self.starting_point.y() - (self.target_point.y() - self.starting_point.y()) * coef_length
        x4 = self.target_point.x() + (self.target_point.x() - self.starting_point.x()) * coef_length
        y4 = self.target_point.y() + (self.target_point.y() - self.starting_point.y()) * coef_length
        print("point 3", x3, y3)
        print("point 4", x4, y4)

        ev = [x4 - x3, y4 - y3]

        ev_len = math.sqrt((x4 - x3) ** 2 + (y4 - y3) ** 2)
        # Высчитываем коэф уменьшения
        coef_decr = ev_len / hall_width
        print("Coef уменьшения", coef_decr)
        ev_decr = [0, 0]
        ev_decr[0], ev_decr[1] = ev[0] / coef_decr, ev[1] / coef_decr

        point_turn_x_1 = x3 + ev_decr[0]
        point_turn_y_1 = y3 + ev_decr[1]
        point_turn_x_2 = x4 - ev_decr[0]
        point_turn_y_2 = y4 - ev_decr[1]

        print(point_turn_x_1)
        print(point_turn_y_1)
        print(point_turn_x_2)
        print(point_turn_y_2)

        angle_turn_1 = 90
        angle_turn_2 = 270

        # Точки расположены в порядке создания прямоугольника, ЭТО НЕ ТОЧКИ ЭТО ПРИРАЩЕНИЯ
        hall[0][0] = self.starting_point.x() + point_turn_x_1 * math.cos(angle_turn_1) - point_turn_y_1 * math.sin(
            angle_turn_1)
        hall[0][1] = self.starting_point.y() + point_turn_x_1 * math.sin(angle_turn_1) + point_turn_y_1 * math.cos(
            angle_turn_1)

        hall[1][0] = self.starting_point.x() + point_turn_x_1 * math.cos(angle_turn_2) - point_turn_y_1 * math.sin(
            angle_turn_2)
        hall[1][1] = self.starting_point.y() + point_turn_x_1 * math.sin(angle_turn_2) + point_turn_y_1 * math.cos(
            angle_turn_2)

        hall[2][0] = self.target_point.x() + point_turn_x_2 * math.cos(angle_turn_2) - point_turn_y_2 * math.sin(
            angle_turn_2)
        hall[2][1] = self.target_point.y() + point_turn_x_2 * math.sin(angle_turn_2) + point_turn_y_2 * math.cos(
            angle_turn_2)

        hall[3][0] = self.target_point.x() + point_turn_x_2 * math.cos(angle_turn_1) - point_turn_y_2 * math.sin(
            angle_turn_1)
        hall[3][1] = self.target_point.y() + point_turn_x_2 * math.sin(angle_turn_1) + point_turn_y_2 * math.cos(
            angle_turn_1)

        point1 = QgsPointXY(hall[0][0], hall[0][1])
        point2 = QgsPointXY(hall[1][0], hall[1][1])
        point3 = QgsPointXY(hall[2][0], hall[2][1])
        point4 = QgsPointXY(hall[3][0], hall[3][1])
        hall_polygon = QgsGeometry.fromPolygonXY([[point1, point2, point4, point3]])
        print(hall_polygon)

        # region Визуализация коридора, УДАЛИТЬ ПОЗЖЕ
        layer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp")
        layer.dataProvider().truncate()
        feats = []
        for i in [point1, point2, point4, point3]:
            point = QgsGeometry.fromPointXY(i)
            feat = QgsFeature(layer.fields())
            feat.setGeometry(point)
            feats.append(feat)

        # feat = QgsFeature(layer.fields())
        # feat.setGeometry(hall_polygon)
        # feats.append(feat)

        layer.dataProvider().addFeatures(feats)
        layer.triggerRepaint()
        print("HERE")
        # endregion

    def __get_borders(self):
        # Отвечает за расширение границ прямоугольника
        coef_extand = 0.08

        left_x = self.starting_point.x() if self.starting_point.x() < self.target_point.x() else self.target_point.x()
        right_x = self.starting_point.x() if self.starting_point.x() > self.target_point.x() else self.target_point.x()
        bottom_y = self.starting_point.y() if self.starting_point.y() < self.target_point.y() else self.target_point.y()
        top_y = self.starting_point.y() if self.starting_point.y() > self.target_point.y() else self.target_point.y()

        expand_constant_x = (right_x - left_x) * coef_extand
        expand_constant_y = (top_y - bottom_y) * coef_extand

        left_x = left_x - expand_constant_x
        right_x = right_x + expand_constant_x
        bottom_y = bottom_y - expand_constant_y
        top_y = top_y + expand_constant_y

        return left_x, right_x, bottom_y, top_y

    # private method, which returns one checked point
    def __add_point(self):
        x = random.uniform(self.left_x, self.right_x)
        y = random.uniform(self.bottom_y, self.top_y)
        point = QgsGeometry.fromPointXY(QgsPointXY(x, y))
        cell = self.grid.difine_point(point)
        if cell.geometry.distance(point) > 0.0:
            point_expand = GeometryPointExpand(point, cell.n_row, cell.n_column)
            return point_expand
        else:
            return self.__add_point()

    # method for starting and target point, return list of points around this points
    def __add_points_around(self, source_point, distance):
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
            cell = self.grid.difine_point(point)
            if cell is None:
                break
            if cell.geometry.distance(point) > 0.0:
                point_expand = GeometryPointExpand(point, cell.n_row, cell.n_column)
                points_around.append(point_expand)
            f += shift
        return points_around

    def __get_list_of_points(self, amount_of_points):
        list_of_points = []

        for i in range(amount_of_points):
            point = self.__add_point()
            list_of_points.append(point)

        return list_of_points

    def __create_graph(self):
        # assign geometry to the cell
        for row in self.grid.cells:
            for cell in row:
                cell.set_geometry(self.list_of_polygons)

        area = (self.right_x - self.left_x) * (self.top_y - self.bottom_y)
        # 1 point for "self.const_square_meters" square meters
        amount_of_points = math.ceil(area / self.const_square_meters)
        list_of_points = self.__get_list_of_points(amount_of_points)

        # adding starting and target points + points around of them
        list_points_around_starting = self.__add_points_around(self.starting_point, 20)
        list_points_around_target = self.__add_points_around(self.target_point, 20)

        list_of_points.extend(list_points_around_starting)
        list_of_points.extend(list_points_around_target)
        cell_start = self.grid.difine_point(self.starting_point_geometry)
        start_point_expand = GeometryPointExpand(self.starting_point_geometry, cell_start.n_row, cell_start.n_column)
        cell_target = self.grid.difine_point(self.target_point_geometry)
        target_point_expand = GeometryPointExpand(self.target_point_geometry, cell_target.n_row, cell_target.n_column)

        list_of_points.append(start_point_expand)
        list_of_points.append(target_point_expand)
        # region display points, may delete
        vlayer1 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp")
        vlayer1.dataProvider().truncate()

        feats = []
        for point in list_of_points:
            feat = QgsFeature(vlayer1.fields())
            feat.setId(point.id)
            feat.setGeometry(point.point)
            feats.append(feat)
        vlayer1.dataProvider().addFeatures(feats)
        vlayer1.triggerRepaint()
        # endregion

        qgs_graph = QgsGraph()
        for point in list_of_points:
            qgs_graph.addVertex(point.point.asPoint())
        index = QgsSpatialIndex()
        index.addFeatures(feats)

        vlayer2 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp")
        vlayer2.dataProvider().truncate()
        # list to except double edges
        list_of_excepts = []
        # list to dublicate backwards
        list_to_duplicate_backwards = []
        # list_of_lines contain type QgsGeometry
        list_of_lines = []
        # feats_line contain type QgsFeature
        feats_line = []
        id_number = -1
        list_of_ticks = []
        tick3 = time.perf_counter()
        for id_1, point in enumerate(feats):
            nearest = index.nearestNeighbor(point.geometry().asPoint(), self.const_sight_of_points)
            nearest.pop(0)
            # iterates over nearest points, try to create line
            for nearest_point_id in nearest:
                if [id_1, nearest_point_id] not in list_of_excepts:
                    # add to list of excepts
                    list_of_excepts.append([id_1, nearest_point_id])

                    line = QgsGeometry.fromPolylineXY([point.geometry().asPoint(),
                                                       feats[nearest_point_id].geometry().asPoint()])

                    geometry = self.grid.get_multipolygon_by_points(list_of_points[id_1],
                                                                    list_of_points[nearest_point_id])
                    if geometry.distance(line):
                        pass
                        # add to list of duplicates backwards, ADDING IS BACKWARD
                        list_to_duplicate_backwards.append([nearest_point_id, id_1])
                        # # add to list_of_lines # QgsGeometry
                        list_of_lines.append(line)
                        id_number += 1
                        # Create QgsFeature and add to feats_line
                        feat = QgsFeature(vlayer2.fields())
                        feat.setId(id_number)
                        feat.setGeometry(line)
                        feats_line.append(feat)
                        qgs_graph.addEdge(id_1, nearest_point_id,
                                          [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        for pares in list_to_duplicate_backwards:
            point1 = pares[0]
            point2 = pares[1]
            line = QgsGeometry.fromPolylineXY([qgs_graph.vertex(pares[1]).point(), qgs_graph.vertex(pares[0]).point()])
            list_of_lines.append(line)
            id_number += 1
            # Create QgsFeature and add to feats_line
            feat = QgsFeature(vlayer2.fields())
            feat.setId(id_number)
            feat.setGeometry(line)
            feats_line.append(feat)
            qgs_graph.addEdge(point1, point2, [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        vlayer2.dataProvider().addFeatures(feats_line)
        vlayer2.triggerRepaint()
        return qgs_graph

    def check(self):
        for row in self.grid.cells:
            for cell in row:
                a = cell.geometry
                b = a.asGeometryCollection()
                print(b)

    def run(self):
        self.debug_info()
        tick = time.perf_counter()
        graph = self.__create_graph()
        searcher = QgsGraphSearcher(graph, self.starting_point, self.target_point, 0)

        if not searcher.check_to_pave_the_way():
            print("the algorithm failed to pave the way")
            return None

        print("Length of min path is: ", searcher.min_length_to_vertex())

        # visualize the shortest tree graph
        vlayer3 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_tree.shp")
        vlayer3.dataProvider().truncate()
        feats = searcher.get_shortest_tree_features_list(vlayer3)
        vlayer3.dataProvider().addFeatures(feats)
        vlayer3.triggerRepaint()

        # search min path and visualize
        vlayer4 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp")
        vlayer4.dataProvider().truncate()
        feats = searcher.get_features_from_min_path(vlayer4)
        vlayer4.dataProvider().addFeatures(feats)
        vlayer4.triggerRepaint()
        acc = time.perf_counter() - tick
        print(acc)

    def debug_info(self):
        print("starting_point: ", self.starting_point)
        print("target_point: ", self.target_point)
        print("area: ", (self.right_x - self.left_x) * (self.top_y - self.bottom_y))
        print(self.left_x, self.right_x, self.bottom_y, self.top_y)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7890839, 47.2690766))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(39.777808, 47.277062))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    obstacles = QgsVectorLayer(path)
    check = RandomizedRoadmapGridMethod(point1, point2, obstacles, proj)
    check._get_hall()
