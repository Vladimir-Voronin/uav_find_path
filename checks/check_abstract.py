import time

from qgis._core import QgsGeometry, QgsPointXY, QgsVectorLayer, QgsApplication, QgsProject

from algorithms.GdalUAV.processing.FindPathData import FindPathData
from algorithms.GdalUAV.transformation.coordinates.CoordinateTransform import CoordinateTransform


def create_multipolygon_geometry_by_hall_and_list(list_of_obstacles):
    list_of_geom = []
    for obstacle in list_of_obstacles:
        list_of_geom.append(obstacle)

    geometry = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])
    for polygon in list_of_geom:
        if polygon is not None:
            geometry.addPartGeometry(polygon)
    geometry.deletePart(0)
    return geometry


if __name__ == "__main__":
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    point1 = QgsGeometry.fromPointXY(QgsPointXY(4428210.45, 5955160.67))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(4428636.43, 5955381.07))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\New_pathes\check.shp"
    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    obstacles = QgsVectorLayer(path)
    source_list_of_geometry_obstacles = CoordinateTransform.get_list_of_poligons_in_3395(obstacles, proj)
    find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                  True,
                                  source_list_of_geometry_obstacles)

    all_megapolygons = []
    for i in range(10, len(source_list_of_geometry_obstacles) - 4000, 40):
        all_megapolygons.append(create_multipolygon_geometry_by_hall_and_list(source_list_of_geometry_obstacles[:i]))

    point = QgsGeometry.fromPolylineXY([QgsPointXY(4422265.8,5951558.8), QgsPointXY(4415919.9, 5953888.3)])
    for megapol in all_megapolygons:
        check_time = time.perf_counter()
        for i in range(100):
            megapol.distance(point)
        check_time = time.perf_counter() - check_time
        print(check_time)