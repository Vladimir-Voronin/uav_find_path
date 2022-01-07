from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy, QgsGraphAnalyzer


class QgsGraphSearcher:
    def __init__(self, graph, starting_point, target_point, strategy):
        self.graph = graph
        self.starting_point = starting_point
        self.target_point = target_point
        self.id_target = graph.findVertex(target_point)
        self.strategy = strategy
        search = QgsGraphAnalyzer()
        self.dijkstra_result = search.dijkstra(graph, graph.findVertex(starting_point), strategy)
        self.shortest_tree = search.shortestTree(graph, graph.findVertex(starting_point), strategy)

    def check_to_pave_the_way(self):
        if self.dijkstra_result[0][self.id_target] == -1:
            return False
        return True

    def min_length_to_vertex(self):
        if self.check_to_pave_the_way():
            return self.dijkstra_result[1][self.id_target]

    def get_shortest_tree_features_list(self, layer):
        feats = []
        for i in range(self.shortest_tree.edgeCount()):
            a = self.shortest_tree.edge(i)
            line = QgsGeometry.fromPolylineXY([self.shortest_tree.vertex(a.fromVertex()).point(),
                                               self.shortest_tree.vertex(a.toVertex()).point()])
            feat = QgsFeature(layer.fields())
            feat.setId(i)
            feat.setGeometry(line)
            feats.append(feat)
        return feats

    def get_features_from_min_path(self, layer):
        shortest_tree_target_point_int = self.shortest_tree.findVertex(self.target_point)
        source_int = self.shortest_tree.findVertex(self.starting_point)
        path = []
        feats = []
        first_int = None
        first = self.shortest_tree.vertex(shortest_tree_target_point_int)
        while source_int != first_int:
            edge_int = first.incomingEdges()[0]
            edge = self.shortest_tree.edge(edge_int)
            path.append(edge)
            first_int = edge.fromVertex()
            first = self.shortest_tree.vertex(first_int)

            # to layer
            line = QgsGeometry.fromPolylineXY([self.shortest_tree.vertex(edge.fromVertex()).point(),
                                               self.shortest_tree.vertex(edge.toVertex()).point()])
            feat = QgsFeature(layer.fields())
            feat.setId(edge_int)
            feat.setGeometry(line)
            feats.append(feat)
        feats.reverse()
        path.reverse()
        return feats
