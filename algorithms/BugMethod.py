import math
import numpy as np
import time
from abc import ABC
from operator import attrgetter
from qgis.core import *
from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.addition.GdalExtentions import ObjectsConverter
from algorithms.addition.GeometryPointExpand import GeometryPointExpand
from algorithms.addition.Visualizer import Visualizer


class BugMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 50
        super().__init__(findpathdata, debuglog, hall_width)

        cell_starting = self.grid.difine_point(self.starting_point_geometry)
        self.starting_point_expand = GeometryPointExpand(self.target_point, cell_starting.n_row,
                                                       cell_starting.n_column)
        cell_target = self.grid.difine_point(self.target_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point, cell_target.n_row,
                                                       cell_target.n_column)

        self.__vector_geometry = None

    def __create_grid(self):
        self.debuglog.start_block("create grid")
        super()._create_grid()
        self.debuglog.end_block("create grid")

    def __get_shorter_path(self, feats, increase_points=0):
        self.debuglog.start_block("get shorter path")
        result = super()._get_shorter_path(feats, increase_points)
        self.debuglog.end_block("get shorter path")
        return result

    def __set_geometry_to_grid(self):
        self.debuglog.start_block("set geometry to grid")
        super()._set_geometry_to_grid()
        self.debuglog.end_block("set geometry to grid")

    def __get_vector_geometry(self):
        self.__vector_geometry = QgsGeometry.fromPolylineXY([self.starting_point, self.target_point])
        lala = QgsGeometry.fromPolygonXY([[self.starting_point, QgsPointXY(39.8865602, 47.2745263), QgsPointXY(40.8865602, 47.2745263), self.target_point]])
        geometry = self.grid.get_multipolygon_by_points(self.starting_point_expand, self.target_point_expand)

        inter = []
        for i in self.list_of_obstacles_geometry:
            if self.__vector_geometry.intersection(i):
                inter.append(self.__vector_geometry.intersection(i))

        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_path.shp",
                                                    inter)
        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                    [self.__vector_geometry])
        a = geometry.intersection(lala)
        b = 3

    def run(self):
        self.__set_geometry_to_grid()
        self.__get_vector_geometry()


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    my_time = time.perf_counter()
    n = 1
    for i in range(n):
        proj = QgsProject.instance()
        proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
        point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7885824, 47.2740465))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(39.7874983, 47.2740442))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = BugMethod(find_path_data, debug_log)
        my_time_full = 0
        check.run()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
