import math

from qgis._analysis import QgsGraph, QgsNetworkDistanceStrategy
from qgis.core import *
from algorithms.abstract.SearchMethod import SearchMethodAbstract
from algorithms.addition.Visualizer import Visualizer
from algorithms.addition.QgsGraphSearcher import QgsGraphSearcher
from algorithms.addition.Decorators import measuretime
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.addition.MathFunctions import *


class AngleTurnMethod(AlgoritmsBasedOnHallAndGrid, SearchMethodAbstract):
    def __init__(self, starting_point, target_point, obstacles, project):
        super().__init__(starting_point, target_point, obstacles, project)
        self.path_list = []
        self.length_of_step = 20
        self.angle_shift = 5
        self.multi_polygon_geometry = self.__create_multipolygon_of_layer()

    def __create_multipolygon_of_layer(self):
        features = obstacles.getFeatures()

        list_of_geometry = []
        # Data for transform to EPSG: 3395
        transformcontext = self.project.transformContext()
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

        list_of_geometry_handled = []
        for geometry in list_of_geometry:
            list_of_geometry_handled.append(geometry)
        print("amount_of_objects: ", len(list_of_geometry_handled))
        # because we cant add Part of geometry to empty OgsGeometry instance
        multi_polygon_geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])

        for polygon in list_of_geometry_handled:
            multi_polygon_geometry.addPartGeometry(polygon)

        multi_polygon_geometry.deletePart(0)

        return multi_polygon_geometry

    @measuretime
    def __create_grid(self):
        super()._create_grid()

    @measuretime
    def __get_shorter_path(self, feats, increase_points=0):
        super()._get_shorter_path(feats, increase_points)

    @measuretime
    def __set_geometry_to_grid(self):
        super()._set_geometry_to_grid()

    def __is_left(self, current_point_as_point):
        return ((self.target_point.x() - self.starting_point.x()) * (
                current_point_as_point.y() - self.starting_point.y()) - (
                        self.target_point.y() - self.starting_point.y()) * (
                        current_point_as_point.x() - self.starting_point.x())) > 0

    # Doesnt_work
    def __check_for_intersection_by_cells(self, point1, point2):
        cell_point1 = self.grid.difine_point(point1)
        cell_point2 = self.grid.difine_point(point2)
        line = QgsGeometry.fromPolylineXY([point1.asPoint(),
                                           point2.asPoint()])
        geometry = self.grid.get_multipolygon_by_cells(cell_point1,
                                                       cell_point2)

        if geometry.distance(line):
            return True

        return False

    def __check_for_intersection_by_full_layer(self, point1, point2):
        line = QgsGeometry.fromPolylineXY([point1.asPoint(),
                                           point2.asPoint()])
        if self.multi_polygon_geometry.distance(line):
            return True

        return False

    def __get_new_point(self, current_point, angle=0):
        if angle >= 180:
            raise Exception("FAILED, THE PATH CANT TURN")
        rad = math.radians(angle)

        current_point_as_point = current_point.asPoint()
        # unit vector for start_point
        vector_from_current_to_target = [self.target_point.x() - current_point_as_point.x(),
                                         self.target_point.y() - current_point_as_point.y()]

        length_vector_from_current_to_target = math.sqrt(
            (vector_from_current_to_target[0]) ** 2 + (vector_from_current_to_target[1]) ** 2)

        # Check for end
        if length_vector_from_current_to_target < self.length_of_step:
            last_point = self.target_point_geometry
            if self.__check_for_intersection_by_full_layer(current_point, last_point):
                print("End")
                return last_point

        unit_vector = [vector_from_current_to_target[0] / length_vector_from_current_to_target,
                       vector_from_current_to_target[1] / length_vector_from_current_to_target]

        increments = [unit_vector[0] * self.length_of_step, unit_vector[1] * self.length_of_step]
        new_point_coordinates = [current_point_as_point.x() + increments[0], current_point_as_point.y() + increments[1]]
        Xp = (new_point_coordinates[0] - current_point_as_point.x()) * math.cos(rad) - (
                new_point_coordinates[1] - current_point_as_point.y()) * math.sin(rad)
        Yp = (new_point_coordinates[0] - current_point_as_point.x()) * math.sin(rad) + (
                new_point_coordinates[1] - current_point_as_point.y()) * math.cos(rad)

        new_point = QgsGeometry.fromPointXY(
            QgsPointXY(current_point_as_point.x() + Xp, current_point_as_point.y() + Yp))

        if self.__check_for_intersection_by_full_layer(current_point, new_point):
            return new_point
        return None

    @measuretime
    def __create_path(self):
        self.path_list.append(self.starting_point_geometry)
        while True:
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp",
                                                        self.path_list)

            is_it_left = self.__is_left(self.path_list[-1].asPoint())
            new_point = self.__get_new_point(self.path_list[-1])
            if new_point is None:
                angle = 0
                coef_left = -1
                if is_it_left:
                    coef_left = 1
                while True:
                    angle += self.angle_shift * coef_left
                    new_point = self.__get_new_point(self.path_list[-1], angle)
                    if new_point:
                        break
                    second_angle = -angle
                    new_point = self.__get_new_point(self.path_list[-1], second_angle)
                    if new_point:
                        break

            self.path_list.append(new_point)
            if new_point.asPoint().x() == self.target_point.x() and new_point.asPoint().y() == self.target_point.y():
                break

    @measuretime
    def __create_graph(self):
        qgs_graph = QgsGraph()
        for point in self.path_list:
            qgs_graph.addVertex(point.asPoint())

        for i in range(len(self.path_list) - 1):
            line = QgsGeometry.fromPolylineXY([self.path_list[i].asPoint(), self.path_list[i + 1].asPoint()])
            feat = QgsFeature()
            feat.setGeometry(line)
            qgs_graph.addEdge(i, i + 1,
                              [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        return qgs_graph

    @measuretime
    def run(self):
        self.__set_geometry_to_grid()

        # Check
        self.__create_path()
        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp",
                                                    self.path_list)
        # graph = None
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

        # self.__get_shorter_path(feats, 3)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point_1 = QgsGeometry.fromPointXY(QgsPointXY(39.7899186, 47.2674382))
    point_2 = QgsGeometry.fromPointXY(QgsPointXY(39.7855080,47.2822433))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    obstacles = QgsVectorLayer(path)
    check = AngleTurnMethod(point_1, point_2, obstacles, proj)
    check.run()
