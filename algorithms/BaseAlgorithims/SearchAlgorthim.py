from abc import ABC

from qgis.core import *
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
import logging

from checks.check_abstract import SearchMethod


class SearchAlgorithm(SearchMethod):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        # others
        self.current_id = 0
        self.project = findpathdata.project
        self.obstacles = findpathdata.obstacles  # type: QgsVectorLayer
        self.path_to_save_layers = findpathdata.path_to_save_layers
        self.create_debug_layers = findpathdata.create_debug_layers
        # transform to EPSG 3395
        # need to change "project" to "QgsProject.instance" when import to module
        transformcontext = self.project.transformContext()
        general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
        xform = QgsCoordinateTransform(self.obstacles.crs(), general_projection, transformcontext)

        # type: QgsPointXY
        self.starting_point = xform.transform(findpathdata.start_point.asPoint())
        self.target_point = xform.transform(findpathdata.target_point.asPoint())

        # type: QgsGeometry
        self.starting_point_geometry = QgsGeometry.fromPointXY(QgsPointXY(self.starting_point.x(),
                                                                          self.starting_point.y()))
        self.target_point_geometry = QgsGeometry.fromPointXY(QgsPointXY(self.target_point.x(),
                                                                        self.target_point.y()))
        self.debuglog = debuglog

    def run(self):
        raise NotImplementedError

    def visualise(self):
        raise NotImplementedError
