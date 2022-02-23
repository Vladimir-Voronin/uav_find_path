from qgis.core import *


class GeometryPointExpand:
    def __init__(self, point, n_row, n_column):
        self.point = point
        self.n_row = n_row
        self.n_column = n_column
        self.id = None

    @staticmethod
    def transform_to_list_of_feats(points: list):
        feats = []
        current_id = 0
        for point in points:
            feat = QgsFeature()
            feat.setId(current_id)
            feat.setGeometry(point.point)
            feats.append(feat)
            current_id += 1
        return feats
