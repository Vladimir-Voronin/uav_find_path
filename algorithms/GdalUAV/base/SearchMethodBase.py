from abc import ABC

from qgis.core import *
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData

from checks.check_abstract import SearchMethod


class SearchMethodBase(SearchMethod, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        # others
        self.current_id = 0
        self.project = findpathdata.project
        self.obstacles = findpathdata.obstacles  # type: QgsVectorLayer
        self.path_to_save_layers = findpathdata.path_to_save_layers
        self.create_debug_layers = findpathdata.create_debug_layers
        self.source_list_of_geometry_obstacles = findpathdata.source_list_of_geometry_obstacles

        # # transform to EPSG 3395
        # # need to change "project" to "QgsProject.instance" when import to module
        # transformcontext = self.project.transformContext()
        # general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
        # xform = QgsCoordinateTransform(self.obstacles.crs(), general_projection, transformcontext)

        # # type: QgsPointXY
        # self.starting_point = xform.transform(findpathdata.start_point.asPoint())
        # self.target_point = xform.transform(findpathdata.target_point.asPoint())
        self.starting_point = findpathdata.start_point.asPoint()
        self.target_point = findpathdata.target_point.asPoint()

        # type: QgsGeometry
        self.starting_point_geometry = QgsGeometry.fromPointXY(QgsPointXY(self.starting_point.x(),
                                                                          self.starting_point.y()))
        self.target_point_geometry = QgsGeometry.fromPointXY(QgsPointXY(self.target_point.x(),
                                                                        self.target_point.y()))
        self.time_to_succeed = findpathdata.time_to_succeed
        self.debuglog = debuglog

    def run(self):
        raise NotImplementedError

    def visualize(self):
        raise NotImplementedError
