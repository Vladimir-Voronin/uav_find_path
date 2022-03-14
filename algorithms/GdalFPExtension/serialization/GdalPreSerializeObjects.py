class QgsPointXYSerialize:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class QgsPolygonSerialize:
    def __init__(self, list_of_points):
        self.list_of_points = list_of_points
