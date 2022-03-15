from qgis._analysis import QgsGraph, QgsNetworkDistanceStrategy
from qgis.core import *


class QgsPointXYSerializable:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_pointXY(self):
        return QgsPointXY(self.x, self.y)


class QgsPolygonSerializable:
    def __init__(self, list_of_points: [QgsPointXYSerializable]):
        self.list_of_points = list_of_points

    def get_polygon(self):
        real_points = []
        for i in self.list_of_points:
            real_points.append(i.get_pointXY())
        return QgsGeometry.fromPolygonXY([real_points])


class QgsVertexSerializable:
    def __init__(self, point: QgsPointXYSerializable, number):
        self.point = point
        self.number = number


class QgsEdgeSerializable:
    def __init__(self, from_vertex_number, to_vertex_number):
        self.from_vertex_number = from_vertex_number
        self.to_vertex_number = to_vertex_number


class QgsGraphSerializable:
    def __init__(self, list_of_vertices: [QgsVertexSerializable], list_of_edges: [QgsEdgeSerializable]):
        self.list_of_vertices = list_of_vertices
        self.list_of_edges = list_of_edges

    def get_qgsGraph(self):
        qgs_graph = QgsGraph()
        for point in self.list_of_vertices:
            qgs_graph.addVertex(point.point.get_pointXY())

        for edge in self.list_of_edges:
            line = QgsGeometry.fromPolylineXY([qgs_graph.vertex(edge.from_vertex_number).point(),
                                               qgs_graph.vertex(edge.to_vertex_number).point()])
            feat = QgsFeature()
            feat.setGeometry(line)
            qgs_graph.addEdge(edge.from_vertex_number, edge.to_vertex_number,
                              [QgsNetworkDistanceStrategy().cost(line.length(), feat)])
        return qgs_graph
