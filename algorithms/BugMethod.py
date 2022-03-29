import math
import time
from abc import ABC
from qgis.core import *
from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallOnly import AlgorithmsBasedOnHallOnly
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.GdalFPExtension.calculations import ObjectsCalculations
from algorithms.GdalFPExtension.gdalObjects.Converter import ObjectsConverter
from algorithms.GdalFPExtension.gdalObjects.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalFPExtension.qgis.visualization.Visualizer import Visualizer


class Pare:
    def __init__(self, start_point, end_point, obstacle_geometry):
        self.start_point = start_point
        self.end_point = end_point
        self.obstacle_geometry = obstacle_geometry
        self.round_path = []

    @staticmethod
    def __is_point_on_line(point_line_1, point_line_2, point):
        full_distance = math.sqrt(
            (point_line_2.x() - point_line_1.x()) ** 2 + (point_line_2.y() - point_line_1.y()) ** 2)
        distance_from_point_to_first = math.sqrt(
            (point.x() - point_line_1.x()) ** 2 + (point.y() - point_line_1.y()) ** 2)
        distance_from_point_to_second = math.sqrt(
            (point_line_2.x() - point.x()) ** 2 + (point_line_2.y() - point.y()) ** 2)

        difference = full_distance - (distance_from_point_to_first + distance_from_point_to_second)

        if (difference * difference) ** 0.5 <= 0.00001:
            return True
        return False

    def build_round_path(self):
        start_point_id = None
        end_point_id = None
        points_of_lines = []
        for polygon in self.obstacle_geometry.asGeometryCollection():
            points_of_lines = polygon.asPolygon()[0]
            for i in range(len(points_of_lines) - 1):
                first_point = points_of_lines[i]
                second_point = points_of_lines[i + 1]

                if Pare.__is_point_on_line(first_point, second_point, self.start_point):
                    start_point_id = i + 1
                if Pare.__is_point_on_line(first_point, second_point, self.end_point):
                    end_point_id = i + 1

        if end_point_id > start_point_id:
            points_of_lines.insert(start_point_id, self.start_point)
            end_point_id += 1
            points_of_lines.insert(end_point_id, self.end_point)
        else:
            points_of_lines.insert(end_point_id, self.end_point)
            start_point_id += 1
            points_of_lines.insert(start_point_id, self.start_point)

        path1 = []
        distance_path1 = 0

        current = start_point_id
        target = end_point_id
        while current != target:
            path1.append(current)
            if current + 1 < len(points_of_lines):
                distance_path1 += ObjectsCalculations.get_distance(points_of_lines[current],
                                                                   points_of_lines[current + 1])
                current += 1
            else:
                distance_path1 += ObjectsCalculations.get_distance(points_of_lines[current], points_of_lines[0])
                current = 0
        path1.append(target)
        path2 = []
        distance_path2 = 0
        current = start_point_id
        target = end_point_id
        while current != target:
            path2.append(current)
            if current - 1 >= 0:
                distance_path2 += ObjectsCalculations.get_distance(points_of_lines[current],
                                                                   points_of_lines[current - 1])
                current = current - 1
            else:
                distance_path2 += ObjectsCalculations.get_distance(points_of_lines[0],
                                                                   points_of_lines[len(points_of_lines) - 1])
                current = len(points_of_lines) - 1

        path2.append(target)
        final_path_indexes = path1 if distance_path1 < distance_path2 else path2
        for i in final_path_indexes:
            self.round_path.append(points_of_lines[i])

        lala = []
        for i in range(len(self.round_path) - 1):
            point1 = self.round_path[i]
            point2 = self.round_path[i + 1]
            if point1.x() == point2.x() and point1.y() == point2.y():
                continue
            line = QgsGeometry.fromPolylineXY([point1, point2])
            lala.append(line)


class BugMethod(AlgorithmsBasedOnHallOnly, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 50
        super().__init__(findpathdata, debuglog, hall_width)

        self.__vector_geometry = None
        self.point_path = []
        self.line_path = []
        self.final_path = []

    def __get_vector_geometry(self):
        self.__vector_geometry = QgsGeometry.fromPolylineXY([self.starting_point, self.target_point])
        # geometry = self.grid.get_multipolygon_by_points(self.starting_point_expand, self.target_point_expand)
        geometry = self.hall.create_multipolygon_geometry_by_hall_and_list(self.list_of_obstacles_geometry)
        pares = []
        geometry_list = geometry.asGeometryCollection()

        # to delete repeated geometry
        points_except_repeats = []

        for part in geometry_list:
            intersections = self.__vector_geometry.intersection(part)
            if intersections:
                try:
                    points = intersections.asPolyline()

                    # to delete repeat geometry
                    rep = []
                    for i in points:
                        rep.append(i.x())
                        rep.append(i.y())

                    if rep not in points_except_repeats:
                        points_except_repeats.append(rep)

                        pare = Pare(points[0], points[1], part)
                        pares.append(pare)
                except TypeError:
                    multi = intersections.asMultiPolyline()
                    for points in multi:
                        # to delete repeat geometry
                        rep = []
                        for i in points:
                            rep.append(i.x())
                            rep.append(i.y())

                        if rep not in points_except_repeats:
                            points_except_repeats.append(rep)

                            pare = Pare(points[0], points[1], part)
                            pares.append(pare)

        for pare in pares:
            pare.build_round_path()

        return pares

    def __sort(self, point):
        return ObjectsCalculations.get_distance(self.starting_point, point.start_point)

    def run(self):
        pares = self.__get_vector_geometry()
        pares.sort(key=self.__sort)

        self.point_path.append(self.starting_point)
        for pare in pares:
            for point in pare.round_path:
                self.point_path.append(point)
        self.point_path.append(self.target_point)

        for i in range(len(self.point_path) - 1):
            point1 = self.point_path[i]
            point2 = self.point_path[i + 1]
            if point1.x() == point2.x() and point1.y() == point2.y():
                continue
            line = QgsGeometry.fromPolylineXY([point1, point2])
            self.line_path.append(line)

        self.final_path = ObjectsConverter.list_of_geometry_to_feats(self.line_path)

    def visualize(self):
        if self.create_debug_layers:
            pass

        line_path = ObjectsConverter.list_of_geometry_to_feats(self.line_path)
        Visualizer.create_and_add_new_final_path(self.project, self.path_to_save_layers, line_path)
        if __name__ == '__main__':
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                        [self.__vector_geometry])
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                        self.line_path)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    n = 1
    for i in range(n):
        proj = QgsProject.instance()
        proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4427147.689249892, 5955279.540250717))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4426955.309876399, 5955334.222758474))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = BugMethod(find_path_data, debug_log)
        my_time_full = 0
        my_time = time.perf_counter()
        check.run()
        my_time = (time.perf_counter() - my_time) / n
        print(my_time)
