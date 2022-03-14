import math
from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy, QgsGraphAnalyzer


class Hall:
    def __init__(self, source_point_x, source_point_y, target_point_x, target_point_y,
                 hall_width=150, coef_length=0.1):
        self.source_point_x = source_point_x
        self.source_point_y = source_point_y
        self.target_point_x = target_point_x
        self.target_point_y = target_point_y

        # Координаты расширенного вектора
        self.start_extended_point_x = None
        self.start_extended_point_y = None
        self.target_extended_point_x = None
        self.target_extended_point_y = None

        # Крайние точки коридора
        self.point1 = None
        self.point2 = None
        self.point3 = None
        self.point4 = None

        self.cos = None
        self.sin = None
        # Приращения
        self.Xp = None
        self.Yp = None

        self.hall_width = hall_width
        self.coef_length = coef_length

        self.hall_polygon = None
        self.square = None
        self.get_hall()

    def get_hall(self):
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
        x3 = self.source_point_x - (self.target_point_x - self.source_point_x) * coef_length
        y3 = self.source_point_y - (self.target_point_y - self.source_point_y) * coef_length
        x4 = self.target_point_x + (self.target_point_x - self.source_point_x) * coef_length
        y4 = self.target_point_y + (self.target_point_y - self.source_point_y) * coef_length

        self.start_extended_point_x = x3
        self.start_extended_point_y = y3
        self.target_extended_point_x = x4
        self.target_extended_point_y = y4

        ev = [x4 - x3, y4 - y3]
        ev_len = math.sqrt((x4 - x3) ** 2 + (y4 - y3) ** 2)
        # Высчитываем коэф уменьшения
        coef_decr = ev_len / hall_width

        self.cos = ev[0] / ev_len
        self.sin = ev[1] / ev_len
        self.Xp = hall_width * self.sin
        self.Yp = hall_width * self.cos
        self.square = (ev_len * self.hall_width * 2)

        # Точки расположены в порядке создания прямоугольника
        hall[0][0] = x3 + self.Xp
        hall[0][1] = y3 - self.Yp

        hall[1][0] = x3 - self.Xp
        hall[1][1] = y3 + self.Yp

        hall[2][0] = x4 - self.Xp
        hall[2][1] = y4 + self.Yp

        hall[3][0] = x4 + self.Xp
        hall[3][1] = y4 - self.Yp

        self.point1 = QgsPointXY(hall[0][0], hall[0][1])
        self.point2 = QgsPointXY(hall[1][0], hall[1][1])
        self.point3 = QgsPointXY(hall[2][0], hall[2][1])
        self.point4 = QgsPointXY(hall[3][0], hall[3][1])
        self.hall_polygon = QgsGeometry.fromPolygonXY([[self.point1, self.point2, self.point3, self.point4]])

        return self.hall_polygon

    def visualize(self):
        # region Визуализация коридора, УДАЛИТЬ ПОЗЖЕ
        layer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\hall.shp")
        layer.dataProvider().truncate()
        feats = []
        # for i in [point1, point2, point4, point3]:
        feat = QgsFeature(layer.fields())
        feat.setGeometry(self.hall_polygon)
        feats.append(feat)

        layer.dataProvider().addFeatures(feats)
        layer.triggerRepaint()
        print("HERE")

    def create_multipolygon_geometry_by_hall(self, obstacles, project):
        features = obstacles.getFeatures()

        list_of_geometry = []
        # Data for transform to EPSG: 3395
        transformcontext = project.transformContext()
        source_projection = obstacles.crs()
        general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
        xform = QgsCoordinateTransform(source_projection, general_projection, transformcontext)
        for feature in features:
            geom = feature.geometry()

            # Transform to EPSG 3395
            check = geom.asGeometryCollection()[0].asPolygon()
            list_of_points_to_polygon = []
            for point in check[0]:
                point = xform.transform(point.x(), point.y())
                list_of_points_to_polygon.append(point)

            created_polygon = QgsGeometry.fromPolygonXY([list_of_points_to_polygon])
            list_of_geometry.append(created_polygon)
        polygon = self.hall_polygon

        list_of_geometry_handled = []
        for geometry in list_of_geometry:
            if polygon.distance(geometry) == 0.0:
                list_of_geometry_handled.append(geometry)
        print("objects_number: ", len(list_of_geometry_handled))
        # because we cant add Part of geometry to empty OgsGeometry instance
        multi_polygon_geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])

        for polygon in list_of_geometry_handled:
            multi_polygon_geometry.addPartGeometry(polygon)

        multi_polygon_geometry.deletePart(0)

        return multi_polygon_geometry

    def create_list_of_obstacles(self, obstacles, project):
        features = obstacles.getFeatures()
        list_of_obstacles = []
        for feature in features:
            geom = feature.geometry()
            # check for type of the objects
            if geom.type() == QgsWkbTypes.LineGeometry:
                list_of_obstacles = self.create_list_of_lines(obstacles, project)
            elif geom.type() == QgsWkbTypes.PolygonGeometry:
                list_of_obstacles = self.create_list_of_polygons(obstacles, project)
            else:
                raise Exception("This layer contains not lines or polygons")
            break

        return list_of_obstacles

    def create_list_of_polygons(self, obstacles, project):
        features = obstacles.getFeatures()

        list_of_geometry = []
        # Data for transform to EPSG: 3395
        transformcontext = project.transformContext()
        source_projection = obstacles.crs()
        general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
        xform = QgsCoordinateTransform(source_projection, general_projection, transformcontext)
        for feature in features:
            geom = feature.geometry()
            if source_projection != general_projection:
                check = geom.asGeometryCollection()[0].asPolygon()
                if not check:
                    continue

                list_of_points_to_polygon = []
                if source_projection != general_projection:
                    for point in check[0]:
                        point = xform.transform(point.x(), point.y())
                        list_of_points_to_polygon.append(point)
                    create_polygon = QgsGeometry.fromPolygonXY([list_of_points_to_polygon])
                else:
                    create_polygon = QgsGeometry.fromPolygonXY(check[0])
                list_of_geometry.append(create_polygon)
            else:
                list_of_geometry.append(geom)

        list_of_geometry_handled = self.create_list_of_polygons_by_source_geometry(list_of_geometry)

        return list_of_geometry_handled

    def create_list_of_polygons_by_source_geometry(self, source_geometry):
        polygon = self.hall_polygon
        list_of_geometry_handled = []
        for geometry in source_geometry:
            if polygon.distance(geometry) == 0.0:
                list_of_geometry_handled.append(geometry)

        return list_of_geometry_handled

    def create_list_of_lines(self, obstacles, project):
        features = obstacles.getFeatures()

        list_of_geometry = []
        # Data for transform to EPSG: 3395
        transformcontext = project.transformContext()
        source_projection = obstacles.crs()
        general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
        xform = QgsCoordinateTransform(source_projection, general_projection, transformcontext)
        for feature in features:
            geom = feature.geometry()

            # Transform to EPSG 3395
            check = geom.asGeometryCollection()[0].asPolyline()

            if not check:
                continue

            list_of_points_to_line = []

            for point in check:
                point = xform.transform(point.x(), point.y())
                list_of_points_to_line.append(point)

        ######################################## HERE BEGINS Errors
            create_line = QgsGeometry.fromPolylineXY(list_of_points_to_line)
            list_of_geometry.append(create_line)
        polygon = self.hall_polygon

        list_of_geometry_handled = []
        for geometry in list_of_geometry:
            if polygon.distance(geometry) == 0.0:
                list_of_geometry_handled.append(geometry)

        return list_of_geometry_handled