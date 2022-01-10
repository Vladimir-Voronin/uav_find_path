from qgis.core import *

class GeometryPointExpand:
    current_id = -1

    def __init__(self, point, n_row, n_column):
        GeometryPointExpand.current_id += 1
        self.point = point
        self.n_row = n_row
        self.n_column = n_column
        self.id = GeometryPointExpand.current_id

    @staticmethod
    def transform_to_list_of_feats(points: list):
        feats = []
        for point in points:
            feat = QgsFeature()
            feat.setId(point.id)
            feat.setGeometry(point.point)
            feats.append(feat)
        return feats