from qgis._analysis import QgsGraph, QgsNetworkDistanceStrategy
from qgis.core import *

from ModuleInstruments.DebugLog import DebugLog
from algorithms.GdalUAV.processing.FindPathData import FindPathData
from algorithms.GdalUAV.Interfaces.SearchMethod import SearchMethodAbstract
from algorithms.GdalUAV.qgis.visualization.Visualizer import Visualizer
from algorithms.addition.Decorators import measuretime
from algorithms.GdalUAV.base.MethodBasedOnHallAndGrid import MethodBasedOnHallAndGrid
from algorithms.addition.MathFunctions import *


class AngleTurnMethod(MethodBasedOnHallAndGrid, SearchMethodAbstract):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        super().__init__(findpathdata, debuglog)
        self.path_list = []
        self.length_of_step = 50
        self.angle_shift = 15
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

    def __get_shorter_path(self, feats, increase_points=0):
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

        list_min_path_indexes = [0]
        update_index = 1
        i = 0
        self.grid.vizualize(self.project)

        depth = 10
        while i < len(points):
            for k in range(i + 1, min(i + 1 + depth, len(points))):
                line = QgsGeometry.fromPolylineXY([points[i],
                                                   points[k]])

                if self.multi_polygon_geometry.distance(line) > 0:
                    update_index = k
                else:
                    list_min_path_indexes.append(update_index)
                    i = update_index
                    i -= 1
                    break
            i += 1

        if len(points) - 1 != list_min_path_indexes[-1]:
            list_min_path_indexes.append(len(points) - 1)

        a = 0
        while a + 1 < len(list_min_path_indexes):
            if list_min_path_indexes[a] == list_min_path_indexes[a + 1]:
                list_min_path_indexes.remove(list_min_path_indexes[a])
                a -= 1
            a += 1

        shortes_min_path_points = [points[i] for i in list_min_path_indexes]
        shortest_path_lines = []
        for i in range(len(shortes_min_path_points) - 1):
            line = QgsGeometry.fromPolylineXY([shortes_min_path_points[i],
                                               shortes_min_path_points[i + 1]])
            shortest_path_lines.append(line)

        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_path.shp",
                                                    shortest_path_lines)

        return shortest_path_lines

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

        self.__get_shorter_path(feats, 1)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point_1 = QgsGeometry.fromPointXY(QgsPointXY(39.7886790, 47.2701361))
    point_2 = QgsGeometry.fromPointXY(QgsPointXY(39.7804552,47.2716039))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    obstacles = QgsVectorLayer(path)
    check = AngleTurnMethod(point_1, point_2, obstacles, proj)
    check.run()
