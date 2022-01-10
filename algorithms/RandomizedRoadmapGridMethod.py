from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy, QgsGraphAnalyzer
# uav_find_path.algorithms.abstract
from algorithms.abstract.SearchMethod import SearchMethodAbstract
from algorithms.addition.Visualizer import Visualizer
from algorithms.addition.QgsGraphSearcher import QgsGraphSearcher
from algorithms.addition.GridForRoadmap import GridForRoadmap
from algorithms.addition.CellOfTheGrid import CellOfTheGrid
from algorithms.addition.GeometryPointExpand import GeometryPointExpand
from algorithms.addition.RandomizeFunctions import RandomizeFunctions
from algorithms.addition.Hall import Hall
import random
import time
import math


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

        self.hall = Hall(self.starting_point.x(), self.starting_point.y(), self.target_point.x(), self.target_point.y())

        # borders coordinates
        self.left_x, self.right_x, self.bottom_y, self.top_y = None, None, None, None

        self.list_of_polygons = self.hall.create_list_of_polygons(obstacles, project)

        self.grid = self.__create_grid()

    def __create_grid(self):
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

    def get_shorter_path(self):
        pass

    def __create_graph(self):
        # with hall
        self.hall = Hall(self.starting_point.x(), self.starting_point.y(), self.target_point.x(), self.target_point.y())

        # assign geometry to the cell
        for row in self.grid.cells:
            for cell in row:
                cell.set_geometry(self.list_of_polygons)

        self.grid.vizualize(self.project)
        # 1 point for "self.const_square_meters" square meters
        amount_of_points = math.ceil(self.hall.square / self.const_square_meters)

        list_of_points = RandomizeFunctions.get_random_extended_points(self.hall, amount_of_points, self.grid)

        # adding starting and target points + points around of them
        list_points_around_starting = RandomizeFunctions.get_extended_points_around(self.starting_point, 20, self.grid)
        list_points_around_target = RandomizeFunctions.get_extended_points_around(self.target_point, 20, self.grid)

        list_of_points.extend(list_points_around_starting)
        list_of_points.extend(list_points_around_target)
        cell_start = self.grid.difine_point(self.starting_point_geometry)
        start_point_expand = GeometryPointExpand(self.starting_point_geometry, cell_start.n_row, cell_start.n_column)
        cell_target = self.grid.difine_point(self.target_point_geometry)
        target_point_expand = GeometryPointExpand(self.target_point_geometry, cell_target.n_row, cell_target.n_column)

        list_of_points.append(start_point_expand)
        list_of_points.append(target_point_expand)

        # region display points, may delete
        Visualizer.update_layer_by_extended_points(
            r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp",
            list_of_points, True)
        # endregion

        feats = GeometryPointExpand.transform_to_list_of_feats(list_of_points)

        qgs_graph = QgsGraph()
        for point in list_of_points:
            qgs_graph.addVertex(point.point.asPoint())
        index = QgsSpatialIndex()
        index.addFeatures(feats)

        # list to except double edges
        list_of_excepts = []
        # list to dublicate backwards
        list_to_duplicate_backwards = []
        # list_of_lines contain type QgsGeometry
        list_of_lines = []
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
                        # add to list of duplicates backwards, ADDING IS BACKWARD
                        list_to_duplicate_backwards.append([nearest_point_id, id_1])
                        # # add to list_of_lines # QgsGeometry
                        list_of_lines.append(line)
                        feat = QgsFeature()
                        feat.setGeometry(line)
                        qgs_graph.addEdge(id_1, nearest_point_id,
                                          [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        for pares in list_to_duplicate_backwards:
            point1 = pares[0]
            point2 = pares[1]
            line = QgsGeometry.fromPolylineXY([qgs_graph.vertex(pares[1]).point(), qgs_graph.vertex(pares[0]).point()])
            list_of_lines.append(line)
            qgs_graph.addEdge(point1, point2, [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp",
                                                    list_of_lines)
        return qgs_graph

    def run(self):
        tick = time.perf_counter()
        graph = self.__create_graph()
        searcher = QgsGraphSearcher(graph, self.starting_point, self.target_point, 0)

        if not searcher.check_to_pave_the_way():
            print("the algorithm failed to pave the way")
            return None

        print("Length of min path is: ", searcher.min_length_to_vertex())

        # visualize the shortest tree graph
        feats = searcher.get_shortest_tree_features_list()
        Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_tree.shp", feats)

        # search min path and visualize
        feats = searcher.get_features_from_min_path()
        Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp", feats)

        acc = time.perf_counter() - tick
        print("time: ", acc)

        min_path_geometry = [i.geometry() for i in feats]

        points = [i.asPolyline()[0] for i in min_path_geometry]
        print(points)
        points_extended = []
        for point in points:
            point = QgsGeometry.fromPointXY(point)
            cell = self.grid.difine_point(point)
            point_extand = GeometryPointExpand(point, cell.n_row, cell.n_column)
            points_extended.append(point_extand)

        print(points_extended)
        list_min_path_indexes = [0]
        update_index = 1
        i = 0
        while i < len(points_extended):
            for k in range(i + 1, len(points_extended)):
                line = QgsGeometry.fromPolylineXY([points_extended[i].point.asPoint(),
                                                   points_extended[k].point.asPoint()])

                geometry = self.grid.get_multipolygon_by_points(points_extended[i],
                                                                points_extended[k])
                if geometry.distance(line):
                    update_index = k
                else:
                    list_min_path_indexes.append(update_index)
                    i = k
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

        layer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_path.shp")
        layer.dataProvider().truncate()
        feats = []
        for line in shortest_path_lines:
            feat = QgsFeature(layer.fields())
            feat.setGeometry(line)
            feats.append(feat)

        layer.dataProvider().addFeatures(feats)
        layer.triggerRepaint()

        print(shortest_path_lines)
        print("len: ", len(points_extended))
        print(list_min_path_indexes)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7830177, 47.2731885))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(39.7797230, 47.2740633))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    obstacles = QgsVectorLayer(path)
    check = RandomizedRoadmapGridMethod(point1, point2, obstacles, proj)
    check.run()
