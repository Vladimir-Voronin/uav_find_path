import pickle
from qgis.core import *
from algorithms.GdalUAV.serialization.GdalPreSerializeObjects import QgsPointXYSerializable, \
    QgsPolygonSerializable, QgsVertexSerializable, QgsEdgeSerializable, QgsGraphSerializable


class GeometrySerializate:
    @staticmethod
    def serialize_geometry_polygons_to_file(list_of_polygons, path_to_file):
        to_serialize = []
        for geometry in list_of_polygons:
            polygons = geometry.asPolygon()
            for polygon in polygons:
                points_to_serialize = []
                for point in polygon:
                    points_to_serialize.append(QgsPointXYSerializable(point.x(), point.y()))
                to_serialize.append(QgsPolygonSerializable(points_to_serialize))

        with open(path_to_file, 'wb') as f:
            pickle.dump(to_serialize, f)

        return True

    @staticmethod
    def deserialize_geometry_polygons_from_file(path_to_file):
        with open(path_to_file, 'rb') as f:
            from_serialize = pickle.load(f)

        result = []
        for polygon in from_serialize:
            result.append(polygon.get_polygon())

        return result


class QgsGraphSerializate:
    @staticmethod
    def serialize_qgsgraph_to_file(graph, path_to_file):
        list_of_vertices = []
        for i in range(graph.vertexCount()):
            pre_point = graph.vertex(i).point()
            serializable_point = QgsPointXYSerializable(pre_point.x(), pre_point.y())
            serializable_vertex = QgsVertexSerializable(serializable_point, i)
            list_of_vertices.append(serializable_vertex)

        list_of_edges = []
        for i in range(graph.edgeCount()):
            serializable_edge = QgsEdgeSerializable(graph.edge(i).fromVertex(), graph.edge(i).toVertex())
            list_of_edges.append(serializable_edge)

        serializable_graph = QgsGraphSerializable(list_of_vertices, list_of_edges)

        with open(path_to_file, 'wb') as f:
            pickle.dump(serializable_graph, f)

        return True

    @staticmethod
    def deserialize_qgsgraph_from_file(path_to_file):
        with open(path_to_file, 'rb') as f:
            from_serialize = pickle.load(f)

        qgs_graph = from_serialize.get_qgsGraph()
        return qgs_graph


if __name__ == "__main__":
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

    obstacles = QgsVectorLayer(path)
    b = GeometrySerializate.deserialize_geometry_polygons_from_file(r"C:\Users\Neptune\Desktop\ForSerialize.txt")
