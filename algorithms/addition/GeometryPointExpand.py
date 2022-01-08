class GeometryPointExpand:
    current_id = -1

    def __init__(self, point, n_row, n_column):
        GeometryPointExpand.current_id += 1
        self.point = point
        self.n_row = n_row
        self.n_column = n_column
        self.id = GeometryPointExpand.current_id

