from qgis._core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry


class Converter:
    @staticmethod
    def get_list_of_poligons_in_3395(obstacles, project):
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

        return list_of_geometry
