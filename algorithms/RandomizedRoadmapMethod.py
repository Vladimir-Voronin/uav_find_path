from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy, QgsGraphAnalyzer
from algorithms.abstract.SearchMethod import SearchMethodAbstract
from algorithms.addition.QgsGraphSearcher import QgsGraphSearcher
from algorithms.addition.Hall import Hall
from algorithms.addition.RandomizeFunctions import RandomizeFunctions
import math
import random
import functools
import time
import multiprocessing
import sys

sys.path.insert(0, r'C:\OSGeo4W64\apps\Python37\lib')

timethis_enabled = True


def timethis(func=None):
    if func is None:
        return lambda func: timethis(func)

    @functools.wraps(func)
    def inner(*args, **kwargs):
        print(func.__name__, end=' ... ')
        tick = time.perf_counter()
        result = func(*args, **kwargs)
        acc = time.perf_counter() - tick
        print(acc)
        return result

    return inner if timethis_enabled is True else func


class RandomizedRoadmapMethod(SearchMethodAbstract):
    def __init__(self, starting_point, target_point, obstacles, project):
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
        self.left_x, self.right_x, self.bottom_y, self.top_y = self.__get_borders()

        # get mulmultipolygon layer
        # self.multi_polygon_geometry = RandomizedRoadmapMethod.__create_multipolygon_geometry(obstacles, self.left_x,
        #                                                                                      self.right_x,
        #                                                                                      self.bottom_y, self.top_y,
        #                                                                                      project)

        self.multi_polygon_geometry = self.hall.create_multipolygon_geometry_by_hall(obstacles, project)

        # constants
        self.const_square_meters = 400
        self.const_sight_of_points = 12

    # private method, which create the multipolygon layer from all polygons
    @staticmethod
    def __create_multipolygon_geometry(obstacles, left_x, right_x, bottom_y, top_y, project):
        features = obstacles.getFeatures()

        list_of_geometry = []
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
        print("objects_number: ", len(list_of_geometry_handled))
        # because we cant add Part of geometry to empty OgsGeometry instance
        multi_polygon_geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])

        for polygon in list_of_geometry_handled:
            multi_polygon_geometry.addPartGeometry(polygon)

        multi_polygon_geometry.deletePart(0)
        return multi_polygon_geometry

    # private method, which create the borders of rectangle
    def __get_borders(self):
        left_x = self.starting_point.x() if self.starting_point.x() < self.target_point.x() else self.target_point.x()
        right_x = self.starting_point.x() if self.starting_point.x() > self.target_point.x() else self.target_point.x()
        bottom_y = self.starting_point.y() if self.starting_point.y() < self.target_point.y() else self.target_point.y()
        top_y = self.starting_point.y() if self.starting_point.y() > self.target_point.y() else self.target_point.y()

        expand_constant_x = (right_x - left_x) * 0.08
        expand_constant_y = (top_y - bottom_y) * 0.08

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
        if self.multi_polygon_geometry.distance(point) > 0.0:
            return point
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
            if self.multi_polygon_geometry.distance(point) > 0.0:
                points_around.append(point)
            f += shift
        return points_around

    def __get_list_of_points(self, amount_of_points):
        list_of_points = []

        for i in range(amount_of_points):
            point = self.__add_point()
            list_of_points.append(point)

        return list_of_points

    def __create_graph(self):
        # 1 point for "self.const_square_meters" square meters
        amount_of_points = math.ceil(self.hall.square / self.const_square_meters)


        # __get_list_of_points or __get_list_of_points_multiprocessing
        # list_of_points = self.__get_list_of_points(amount_of_points)

        list_of_points = RandomizeFunctions.get_random_points(self.hall, amount_of_points, self.multi_polygon_geometry)

        # adding starting and target points + points around of them
        list_points_around_starting = RandomizeFunctions.get_points_around(self.starting_point,
                                                                           20,
                                                                           self.multi_polygon_geometry)
        list_points_around_target = RandomizeFunctions.get_points_around(self.target_point,
                                                                           20,
                                                                           self.multi_polygon_geometry)

        list_of_points.extend(list_points_around_starting)
        list_of_points.extend(list_points_around_target)
        list_of_points.append(self.starting_point_geometry)
        list_of_points.append(self.target_point_geometry)

        # region display points, may delete
        vlayer1 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp")
        vlayer1.dataProvider().truncate()

        feats = []
        id_number = -1
        for point in list_of_points:
            id_number += 1
            feat = QgsFeature(vlayer1.fields())
            feat.setId(id_number)
            feat.setGeometry(point)
            feats.append(feat)
        vlayer1.dataProvider().addFeatures(feats)
        # endregion
        print("ST1")

        # creating graph
        qgs_graph = QgsGraph()
        for point in list_of_points:
            qgs_graph.addVertex(point.asPoint())
        index = QgsSpatialIndex()
        index.addFeatures(feats)

        vlayer2 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp")
        vlayer2.dataProvider().truncate()
        # list to except double edges
        list_of_excepts = []
        # list to dublicate backwords
        list_to_duplicate_backwords = []
        # list_of_lines contain type QgsGeometry
        list_of_lines = []
        # feats_line contain type QgsFeature
        feats_line = []
        id_number = -1
        for point in feats:
            nearest = index.nearestNeighbor(point.geometry().asPoint(), self.const_sight_of_points)
            nearest.pop(0)

            # iterates over nearest points, try to create line
            for nearest_point_id in nearest:

                point1 = qgs_graph.findVertex(point.geometry().asPoint())
                point2 = qgs_graph.findVertex(feats[nearest_point_id].geometry().asPoint())
                if sorted([point1, point2]) not in list_of_excepts:
                    # add to list of excepts
                    list_of_excepts.append([point1, point2])
                    line = QgsGeometry.fromPolylineXY([point.geometry().asPoint(),
                                                       feats[nearest_point_id].geometry().asPoint()])

                    tick = time.perf_counter()
                    if self.multi_polygon_geometry.distance(line) > 0.0:
                        # add to list of duplicates backwords, ADDING IS BACKWORD
                        list_to_duplicate_backwords.append([point2, point1])
                        # add to list_of_lines # QgsGeometry
                        list_of_lines.append(line)
                        id_number += 1
                        # Create QgsFeature and add to feats_line
                        feat = QgsFeature(vlayer2.fields())
                        feat.setId(id_number)
                        feat.setGeometry(line)
                        feats_line.append(feat)
                        qgs_graph.addEdge(point1, point2, [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        # duplicate edge backwords
        for pares in list_to_duplicate_backwords:
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
        return qgs_graph

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
    point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7880504,47.2698874))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(39.787049,47.274414))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    obstacles = QgsVectorLayer(path)
    print(obstacles)
    check = RandomizedRoadmapMethod(point1, point2, obstacles, proj)
    check.run()
