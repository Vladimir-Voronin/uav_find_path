from qgis.core import *
import time


def multipolygon_full(path):
    obstacles = QgsVectorLayer(path)
    features = obstacles.getFeatures()
    list_of_polygons = []

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

        create_polygon = QgsGeometry.fromPolygonXY([list_of_points_to_polygon])

        geom_single_type = QgsWkbTypes.isSingleType(geom.wkbType())
        if geom.type() == QgsWkbTypes.PolygonGeometry:
            if geom_single_type:
                list_of_polygons.append(create_polygon.asGeometryCollection())
            else:
                list_of_polygons.append(create_polygon.asGeometryCollection())

    # because we cant add Part of geometry to empty OgsGeometry instance
    multi_polygon_geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])

    for polygon in list_of_polygons:
        multi_polygon_geometry.addPartGeometry(polygon[0])

    multi_polygon_geometry.deletePart(0)
    return multi_polygon_geometry


def multipolygon_part(path):
    obstacles = QgsVectorLayer(path)
    features = obstacles.getFeatures()

    list_of_geometry = []
    list_of_polygons = []
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

        create_polygon = QgsGeometry.fromPolygonXY([list_of_points_to_polygon])
        list_of_geometry.append(create_polygon)

    polygon = QgsGeometry.fromPolygonXY([[QgsPointXY(4429216.32920877, 5955149.056874463),
                                          QgsPointXY(4429521.800578178, 5955149.056874463),
                                          QgsPointXY(4429521.800578178, 5955729.268706462),
                                          QgsPointXY(4429216.32920877, 5955729.268706462)]])

    list_of_geometry_handled = []
    for geometry in list_of_geometry:
        if polygon.distance(geometry) == 0.0:
            list_of_geometry_handled.append(geometry)

    print(len(list_of_geometry_handled))

    # because we cant add Part of geometry to empty OgsGeometry instance
    multi_polygon_geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])

    for polygon in list_of_geometry_handled:
        multi_polygon_geometry.addPartGeometry(polygon)

    multi_polygon_geometry.deletePart(0)
    print(multi_polygon_geometry)
    return multi_polygon_geometry


def polygons_full(path):
    obstacles = QgsVectorLayer(path)
    features = obstacles.getFeatures()
    list_of_polygons = []

    # Data for transform to EPSG: 3395
    transformcontext = project.transformContext()
    source_projection = QgsCoordinateReferenceSystem("EPSG:4326")
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

        create_polygon = QgsGeometry.fromPolygonXY([list_of_points_to_polygon])
        list_of_polygons.append(create_polygon)
    return list_of_polygons


def polytgons_part():
    pass


if __name__=="__main__":
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    project = QgsProject.instance()
    project.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    full_multi = multipolygon_full(path)
    print(full_multi)
    full_polygons = polygons_full(path)
    print(full_polygons)
    layer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp")

    part_multi = multipolygon_part(path)
    print("first", part_multi)
    added = part_multi
    tick = time.perf_counter()
    added.addPartGeometry(part_multi)
    acc = time.perf_counter() - tick
    print(acc)
    print("second", part_multi)

    # a = 0
    # tick = time.perf_counter()
    # for feature in layer.getFeatures():
    #     a += 1
    #     if full_multi.distance(feature.geometry()) > 0.0:
    #         pass
    #     if a > 200:
    #         break
    # acc = time.perf_counter() - tick
    # print(acc)
    #
    # part_multi = multipolygon_part(path)
    #
    # # fastest
    # a = 0
    # tick = time.perf_counter()
    # for feature in layer.getFeatures():
    #     a += 1
    #     if part_multi.distance(feature.geometry()) > 0.0:
    #         pass
    #     # if a > 200:
    #     #     break
    # acc = time.perf_counter() - tick
    # print(acc)
    #
    # # super slow
    # a = 0
    # tick = time.perf_counter()
    # for feature in layer.getFeatures():
    #     a += 1
    #
    #     for polygon in full_polygons:
    #         if polygon.distance(feature.geometry()) > 0:
    #             pass
    #     # if a > 200:
    #     #     break
    # acc = time.perf_counter() - tick
    # print(acc)










