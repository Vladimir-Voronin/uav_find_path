from pandas.core.internals.construction import _list_of_series_to_arrays
from qgis.core import *


class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Point3D(Point2D):
    def __init__(self, x, y, z):
        super().__init__(x, y)
        self.z = z


class Transform:
    def __init__(self):
        self.list_of_points = None


class Transform2D(Transform):
    def __init__(self):
        super().__init__()

    def create_points_from_qgsgeometry_points(self, list_of_geometry_points):
        self.list_of_points = []
        for geom in list_of_geometry_points:
            point = geom.asPoint()
            self.list_of_points.append(Point2D(point.x(), point.y()))

    def create_points_from_qgsfeature_points(self, list_of_feature_points):
        self.list_of_points = []
        for feature in list_of_feature_points:
            point = feature.geometry().asPoint()
            self.list_of_points.append(Point2D(point.x(), point.y()))

    def create_points_from_qgsgeometry_lines(self, list_of_geometry_lines):
        if len(list_of_geometry_lines) == 0:
            raise QgsException("length of list of geometry lines is equal to 0")

        self.list_of_points = []
        point_first = list_of_geometry_lines[0].asPolyline()[0]
        self.list_of_points.append(Point2D(point_first.x(), point_first.y()))
        for i in range(len(list_of_geometry_lines)):
            point = list_of_geometry_lines[i].asPolyline()[1]
            self.list_of_points.append(Point2D(point.x(), point.y()))

    def create_points_from_qgsfeature_lines(self, list_of_feature_lines):
        if len(list_of_feature_lines) == 0:
            raise ValueError("length of list of feature lines is equal to 0")

        self.list_of_points = []
        point_first = list_of_feature_lines[0].geometry().asPolyline()[0]
        self.list_of_points.append(Point2D(point_first.x(), point_first.y()))
        for i in range(len(list_of_feature_lines)):
            point = list_of_feature_lines[i].geometry().asPolyline()[1]
            self.list_of_points.append(Point2D(point.x(), point.y()))


class Transform3D(Transform):
    def __init__(self, z_ground=0, z_plus_max=0):
        super().__init__()
        self.z_ground = z_ground
        self.z_plus_max = z_plus_max

    def create_points_from_qgspoints(self, list_of_qgspoints):
        if len(list_of_qgspoints) < 2:
            raise ValueError("list of geometry points have < 2 values")

        self.list_of_points = []

        if not self.z_plus_max == 0:
            point = list_of_qgspoints[0]
            self.list_of_points.append(Point3D(point.x(), point.y(), self.z_ground))

        for geom in list_of_qgspoints:
            point = geom
            self.list_of_points.append(Point3D(point.x(), point.y(), self.z_ground + self.z_plus_max))

        if not self.z_plus_max == 0:
            point = list_of_qgspoints[-1]
            self.list_of_points.append(Point3D(point.x(), point.y(), self.z_ground))

    def create_points_from_qgsgeometry_points(self, list_of_geometry_points):
        if len(list_of_geometry_points) < 2:
            raise ValueError("list of geometry points have < 2 values")

        self.list_of_points = []
        new_list = [x.asPoint() for x in list_of_geometry_points]
        self.create_points_from_qgspoints(new_list)

    def create_points_from_qgsfeature_points(self, list_of_feature_points):
        self.list_of_points = []
        new_list = [x.geometry().asPoint() for x in list_of_feature_points]
        self.create_points_from_qgspoints(new_list)

    def create_points_from_qgsgeometry_lines(self, list_of_geometry_lines):
        if len(list_of_geometry_lines) == 0:
            raise QgsException("length of list of geometry lines is equal to 0")

        self.list_of_points = []
        new_list = []
        point_first = list_of_geometry_lines[0].asPolyline()[0]
        new_list.append(point_first)
        new_list += [x.asPolyline()[1] for x in list_of_geometry_lines]
        self.create_points_from_qgspoints(new_list)

    def create_points_from_qgsfeature_lines(self, list_of_feature_lines):
        if len(list_of_feature_lines) == 0:
            raise ValueError("length of list of feature lines is equal to 0")

        self.list_of_points = []
        new_list = []
        point_first = list_of_feature_lines[0].geometry().asPolyline()[0]
        new_list.append(point_first)
        new_list += [x.geometry().asPolyline()[1] for x in list_of_feature_lines]
        self.create_points_from_qgspoints(new_list)
