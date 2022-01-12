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
from algorithms.addition.Decorators import measuretime
import time
import math


class SearchAlgorithm:
    def __init__(self, starting_point, target_point, obstacles, project):
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

        self.left_x, self.right_x, self.bottom_y, self.top_y = None, None, None, None
