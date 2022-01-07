import random
import string
from qgis.core import *


class Visualizer:
    @staticmethod
    def create_new_layer_points_extend(address, file_name, points: list, include_id=False):
        random_string = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
        full_address = address + '/' + file_name + random_string + '.shp'

        layer = QgsVectorLayer(full_address)
        layer.dataProvider().truncate()

        feats = []
        for point in points:
            feat = QgsFeature(layer.fields())
            if include_id:
                feat.setId(point.id)
            feat.setGeometry(point.point)
            feats.append(feat)

        layer.dataProvider().addFeatures(feats)
        layer.triggerRepaint()

        return True

    @staticmethod
    def create_new_layer_points(address, file_name, points: list):
        random_string = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
        full_address = address + '/' + file_name + random_string + '.shp'

        layer = QgsVectorLayer(full_address, 'points', 'ogr')

        layer.dataProvider().truncate()

        feats = []
        for point in points:
            point = QgsGeometry.fromPointXY(point)
            feat = QgsFeature(layer.fields())
            feat.setGeometry(point)
            feats.append(feat)

        layer.dataProvider().addFeatures(feats)
        layer.triggerRepaint()

        QgsProject.instance().addMapLayer(layer)
        return True
