from abc import ABC

from qgis._core import QgsGeometry, QgsPointXY, QgsFeature

from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.GdalFPExtension.gdalObjects.Converter import ObjectsConverter
from algorithms.GdalFPExtension.grid.Hall import Hall
from algorithms.GdalFPExtension.methodsInterfaces.SearchMethod import SearchMethodAbstract


class AlgorithmsBasedOnHallOnly(SearchAlgorithm, SearchMethodAbstract, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog, hall_width):
        super().__init__(findpathdata, debuglog)

        self.hall = Hall(self.starting_point.x(), self.starting_point.y(), self.target_point.x(), self.target_point.y(),
                         hall_width)
        if self.source_list_of_geometry_obstacles is None:
            self.list_of_obstacles_geometry = self.hall.create_list_of_obstacles(self.obstacles, self.project)
        else:
            self.list_of_obstacles_geometry = self.hall.create_list_of_polygons_by_source_geometry(
                self.source_list_of_geometry_obstacles)

        self.multi_polygon_geometry = self.hall.create_multipolygon_geometry_by_hall_and_list(
            self.list_of_obstacles_geometry)

    def __get_shorter_path(self, feats_or_geometry, increase_points=0, depth=30):
        if type(feats_or_geometry[0]) == QgsFeature:
            # get shorter path
            min_path_geometry = [i.geometry() for i in feats_or_geometry]
        else:
            min_path_geometry = feats_or_geometry
        points = [i.asPolyline()[0] for i in min_path_geometry]
        # adding last point
        points.append(min_path_geometry[-1].asPolyline()[1])
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

        list_min_path_indexes = [0]
        current_index = 0
        list_min_path_indexes.append(current_index)
        while current_index < len(points) - 1:
            next_index = current_index + 1
            for k in range(current_index + 2, min(current_index + 2 + depth, len(points))):
                line = QgsGeometry.fromPolylineXY([points[current_index],
                                                   points[k]])

                if self.multi_polygon_geometry.isNull() or self.multi_polygon_geometry.distance(line) > 0:
                    next_index = k
                else:
                    break
            current_index = next_index
            list_min_path_indexes.append(current_index)

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

        result_feats = ObjectsConverter.list_of_geometry_to_feats(shortest_path_lines)

        return result_feats
