from abc import ABC

from qgis.core import *
from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.AlgorithmsBasedOnFullObstaclesGeometryGrid import \
    AlgorithmsBasedOnFullObstaclesGeometryGrid
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm


class RRTDirectMethod(AlgorithmsBasedOnFullObstaclesGeometryGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        super().__init__(findpathdata, debuglog)

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

    def run(self):
        self._set_geometry_to_grid()

    def visualise(self):
        pass


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point1 = QgsGeometry.fromPointXY(QgsPointXY(39.765820, 47.276433))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(39.764336, 47.273276))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

    obstacles = QgsVectorLayer(path)
    source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
    find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp", False,
                                  source_list_of_geometry_obstacles)
    debug_log = DebugLog()
    check = RRTDirectMethod(find_path_data, debug_log)
    check.run()
