import math
from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy, QgsGraphAnalyzer


class Hall:
    def __init__(self, source_point_x, source_point_y, target_point_x, target_point_y,
                 hall_width=200, coef_length=0.1):
        self.source_point_x = source_point_x
        self.source_point_y = source_point_y
        self.target_point_x = target_point_x
        self.target_point_y = target_point_y

        self.start_extended_point_x = None
        self.start_extended_point_y = None
        self.target_extended_point_x = None
        self.target_extended_point_y = None

        self.hall_width = hall_width
        self.coef_length = coef_length

        self.hall_polygon = None

    def _get_hall(self):
        # объект будет хранить 4 точки, в конце возвратим прямоугольник
        hall = [[0, 0], [0, 0], [0, 0], [0, 0]]
        # Коэфицент расширение коридора в длину
        coef_length = self.coef_length
        # Фиксированная ширина коридора (деленная на 2)
        hall_width = self.hall_width

        # Далее:
        # Изначальный вектор - a
        # точка 1 расширенного вектора - x3, y3
        # точка 2 расширенного вектора - x4, y4
        # расширенный вектор - ev
        # длина вектора - 'name'_len
        x3 = self.starting_point.x() - (self.target_point.x() - self.starting_point.x()) * coef_length
        y3 = self.starting_point.y() - (self.target_point.y() - self.starting_point.y()) * coef_length
        x4 = self.target_point.x() + (self.target_point.x() - self.starting_point.x()) * coef_length
        y4 = self.target_point.y() + (self.target_point.y() - self.starting_point.y()) * coef_length

        self.start_extended_point_x = x3
        self.start_extended_point_y = y3
        self.target_extended_point_x = x4
        self.target_extended_point_y = y4

        ev = [x4 - x3, y4 - y3]
        ev_len = math.sqrt((x4 - x3) ** 2 + (y4 - y3) ** 2)
        # Высчитываем коэф уменьшения
        coef_decr = ev_len / hall_width

        ev_decr = [0, 0]
        ev_decr[0], ev_decr[1] = ev[0] / coef_decr, ev[1] / coef_decr

        cos_ev = ev[0] / ev_len
        sin_ev = ev[1] / ev_len
        Xp = hall_width * sin_ev
        Yp = hall_width * cos_ev

        # Точки расположены в порядке создания прямоугольника, ЭТО НЕ ТОЧКИ ЭТО ПРИРАЩЕНИЯ
        hall[0][0] = x3 + Xp
        hall[0][1] = y3 - Yp

        hall[1][0] = x3 - Xp
        hall[1][1] = y3 + Yp

        hall[2][0] = x4 - Xp
        hall[2][1] = y4 + Yp

        hall[3][0] = x4 + Xp
        hall[3][1] = y4 - Yp

        point1 = QgsPointXY(hall[0][0], hall[0][1])
        point2 = QgsPointXY(hall[1][0], hall[1][1])
        point3 = QgsPointXY(hall[2][0], hall[2][1])
        point4 = QgsPointXY(hall[3][0], hall[3][1])
        self.hall_polygon = QgsGeometry.fromPolygonXY([[point1, point2, point4, point3]])

        return self.hall_polygon

        # endregion

    def visualize(self, address):
        # region Визуализация коридора, УДАЛИТЬ ПОЗЖЕ
        layer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp")
        layer.dataProvider().truncate()
        feats = []
        # for i in [point1, point2, point4, point3]:
        #     point = QgsGeometry.fromPointXY(i)
        #     feat = QgsFeature(layer.fields())
        #     feat.setGeometry(point)
        #     feats.append(feat)

        # feat = QgsFeature(layer.fields())
        # feat.setGeometry(hall_polygon)
        # feats.append(feat)

        layer.dataProvider().addFeatures(feats)
        layer.triggerRepaint()
        print("HERE")
