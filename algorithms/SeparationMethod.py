import math
import random
import time
from abc import ABC

from qgis.core import *
from shapely.geometry import MultiLineString

from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.AStarMethod import AStarMethod
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.GdalFPExtension.calculations.ObjectsCalculations import get_distance
from algorithms.GdalFPExtension.gdalObjects.Converter import ObjectsConverter
from algorithms.GdalFPExtension.gdalObjects.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalFPExtension.qgis.visualization.Visualizer import Visualizer
from algorithms.RRTDirectMethod import RRTDirectMethod


class SeparationMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, method, tolerance, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 100
        super().__init__(findpathdata, debuglog, hall_width)
        self.find_path_data = findpathdata
        self.method = method
        self.tolerance = tolerance

        cell_start = self.grid.difine_point(self.starting_point_geometry)
        self.starting_point_expand = GeometryPointExpand(self.starting_point_geometry, cell_start.n_row,
                                                         cell_start.n_column)
        cell_target = self.grid.difine_point(self.target_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point_geometry, cell_target.n_row,
                                                       cell_target.n_column)

        self.__vector_geometry = QgsGeometry.fromPolylineXY([self.starting_point, self.target_point])

        self.points_to_search = []

    def __distance_from_start_point(self, pare):
        x_full_difference = pare[0] - self.starting_point.x()
        y_full_difference = pare[1] - self.starting_point.y()
        result = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        return (result * result) ** 0.5

    def __distance_to_target_point(self, pare):
        x_full_difference = self.target_point.x() - pare[0]
        y_full_difference = self.target_point.y() - pare[1]
        result = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        return (result * result) ** 0.5

    def __distance_from_one_begin_to_next(self, begin, next):
        x_full_difference = next[0] - begin[0]
        y_full_difference = next[1] - begin[1]
        result = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        return (result * result) ** 0.5

    def run(self):
        from_start_to_target = get_distance(self.starting_point, self.target_point)

        # just start common method
        if from_start_to_target < self.tolerance:
            pass

        else:
            self.debuglog.start_block("set geometry to the grid block")
            self._set_geometry_to_grid()
            self.debuglog.end_block("set geometry to the grid block")

            geometry = self.grid.get_multipolygon_by_points(self.starting_point_expand, self.target_point_expand)

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
                            rep.append([i.x(), i.y()])

                        if rep not in points_except_repeats:
                            points_except_repeats.append(rep)
                            pares.append(rep)
                    except:
                        multi = intersections.asMultiPolyline()
                        for points in multi:
                            # to delete repeat geometry
                            rep = []
                            for i in points:
                                rep.append([i.x(), i.y()])

                            if rep not in points_except_repeats:
                                points_except_repeats.append(rep)
                                pares.append(rep)

            pares.sort(key=lambda x: self.__distance_from_start_point(x[0]))

            pares.insert(0, [[0, 0], [self.starting_point.x(), self.starting_point.y()]])
            pares.append([[self.target_point.x(), self.target_point.y()], [0, 0]])

            search_vectors = []
            for i in range(len(pares) - 1):
                new_pare = [[pares[i][1][0], pares[i][1][1]], [pares[i + 1][0][0], pares[i + 1][0][1]]]
                search_vectors.append(new_pare)

            vectors_geometry = []
            for vect in search_vectors:
                point1 = QgsPointXY(vect[0][0], vect[0][1])
                point2 = QgsPointXY(vect[1][0], vect[1][1])
                line = QgsGeometry.fromPolylineXY([point1, point2])
                vectors_geometry.append(line)

            for vect in vectors_geometry:
                if vect.length() < 6:
                    vectors_geometry.remove(vect)

            x_full_difference = self.target_point.x() - self.starting_point.x()
            y_full_difference = self.target_point.y() - self.starting_point.y()
            result = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
            correction_x = x_full_difference / result
            correction_y = y_full_difference / result

            self.points_to_search = []
            current_p = vectors_geometry[0].asPolyline()[0]
            current_vector_index = 0
            while True:
                self.points_to_search.append(current_p)

                if self.__distance_to_target_point(current_p) < self.tolerance:
                    self.points_to_search.append(self.target_point)
                    break

                save_vector_index = current_vector_index
                for i in range(save_vector_index, len(vectors_geometry)):
                    line = vectors_geometry[i].asPolyline()
                    point1 = line[0]
                    point2 = line[1]
                    a = self.__distance_from_start_point(point2)
                    b = self.__distance_from_start_point(point1)
                    if self.__distance_from_one_begin_to_next(current_p, point2) > self.tolerance:
                        if self.__distance_from_one_begin_to_next(current_p, point1) < self.tolerance:
                            current_p = QgsPointXY(current_p.x() + correction_x * self.tolerance,
                                                   current_p.y() + correction_y * self.tolerance)
                            break
                        else:
                            best_point = None
                            value = -1
                            current_vector = vectors_geometry[current_vector_index].asPolyline()
                            corrections_here = [0.5, 1.5, 5, 10, 20]
                            points = []
                            for cor in corrections_here:
                                points.append(QgsPointXY(
                                    current_vector[1].x() - correction_x * cor,
                                    current_vector[1].y() - correction_y * cor))

                            for point in points:
                                point_geom = QgsGeometry.fromPointXY(point)
                                cell = self.grid.difine_point(point_geom)
                                if cell.geometry is not None:
                                    d = cell.geometry.distance(point_geom)
                                    if d > value:
                                        value = d
                                        best_point = point
                            current_p = best_point
                            break
                    else:
                        current_vector_index = i

            points_to_search_geom = [QgsGeometry.fromPointXY(x) for x in self.points_to_search]
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp",
                                                        points_to_search_geom)
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                        vectors_geometry)

            list_of_path = []
            for i in range(len(points_to_search_geom) - 1):
                self.find_path_data.start_point = points_to_search_geom[i]
                self.find_path_data.target_point = points_to_search_geom[i + 1]
                self.debuglog = DebugLog()
                algor = self.method(self.find_path_data, self.debuglog)
                algor.run()
                for i in algor.final_path:
                    list_of_path.append(i)

            Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                     list_of_path)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    my_time = time.perf_counter()
    n = 1
    for i in range(n):
        proj = QgsProject.instance()
        proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4429486.8, 5954990.5))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4426529.1, 5957649.7))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = SeparationMethod(AStarMethod, 1000, find_path_data, debug_log)
        check.run()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
