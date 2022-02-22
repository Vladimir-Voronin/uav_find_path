from qgis._core import QgsFeature, QgsVectorLayer


class Converter:
    @staticmethod
    def list_of_geometry_points_to_feats(list_of_points):
        layer = QgsVectorLayer()
        feats = []
        for point in list_of_points:
            feat = QgsFeature(layer.fields())
            feat.setGeometry(point.point)
            feats.append(feat)
        return feats

    @staticmethod
    def list_of_geometry_to_feats(list_of_geometry):
        layer = QgsVectorLayer()
        feats = []
        id_number = 0
        for obj in list_of_geometry:
            id_number += 1
            feat = QgsFeature(layer.fields())
            feat.setId(id_number)
            feat.setGeometry(obj)
            feats.append(feat)

        return feats