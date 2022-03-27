from qgis.core import *


class FindPathData:
    def __init__(self, project: QgsProject, start_point: QgsGeometry, target_point: QgsGeometry,
                 obstacles: QgsVectorLayer, path_to_save_layers: str, create_debug_layers: bool,
                 source_list_of_geometry_obstacles, ):
        self.project = project
        self.start_point = start_point
        self.target_point = target_point
        self.obstacles = obstacles
        self.path_to_save_layers = path_to_save_layers
        self.create_debug_layers = create_debug_layers
        self.source_list_of_geometry_obstacles = source_list_of_geometry_obstacles


def check_if_FindPathData_is_ok(find_path_data: FindPathData):
    flag_check = True
    message = ""

    features = find_path_data.obstacles.getFeatures()
    for feature in features:
        geom = feature.geometry()
        # check for type of the objects
        if geom.type() == QgsWkbTypes.LineGeometry or geom.type() == QgsWkbTypes.PolygonGeometry:
            pass
        else:
            flag_check = False
            message += "Obstacle layer is not correct\n"
            raise Exception(message)
        break

    # transform to EPSG 3395
    # need to change "project" to "QgsProject.instance" when import to module
    transformcontext = find_path_data.project.transformContext()
    general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
    xform = QgsCoordinateTransform(find_path_data.obstacles.crs(), general_projection, transformcontext)

    # type: QgsPointXY
    start_point = xform.transform(find_path_data.start_point.asPoint())
    target_point = xform.transform(find_path_data.target_point.asPoint())
    features = find_path_data.obstacles.getFeatures()
    list_of_geometry = []
    for feature in features:
        geom = feature.geometry()

        check = None
        # Transform to EPSG 3395
        check = geom.asGeometryCollection()[0].asPolygon()

        if not check:
            continue

        list_of_points_to_polygon = []

        if general_projection != find_path_data.obstacles.crs():
            for point in check[0]:
                point = xform.transform(point.x(), point.y())
                list_of_points_to_polygon.append(point)
        else:
            for point in check[0]:
                list_of_points_to_polygon.append(point)

        created_polygon = QgsGeometry.fromPolygonXY([list_of_points_to_polygon])

        list_of_geometry.append(created_polygon)

    for geom in list_of_geometry:
        if geom.distance(QgsGeometry.fromPointXY(start_point)) == 0:
            flag_check = False
            message += "Start point is on the object\n"
        if geom.distance(QgsGeometry.fromPointXY(target_point)) == 0:
            flag_check = False
            message += "Target point is on the object\n"

    if not flag_check:
        raise Exception(message)

    return flag_check
