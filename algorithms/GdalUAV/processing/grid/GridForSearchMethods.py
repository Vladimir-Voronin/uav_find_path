from qgis.core import *
from algorithms.GdalUAV.processing.grid.CellOfTheGrid import CellOfTheGrid
import numpy as np

from algorithms.GdalUAV.processing.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalUAV.qgis.visualization.Visualizer import Visualizer


class GridForSearchMethods:
    def __init__(self, row, column, step_of_the_grid, bottom_y, left_x):
        self.cells = np.zeros((row, column), dtype=CellOfTheGrid)
        self.step_of_the_grid = step_of_the_grid
        self.bottom_y = bottom_y
        self.left_x = left_x

    def add_cell_by_coordinates(self, value, n_row, n_column):
        if isinstance(value, CellOfTheGrid):
            self.cells[n_row][n_column] = value
            value.myGrid = self
            value.n_row = n_row
            value.n_column = n_column
        else:
            raise Exception("Only <CellOfTheGrid> object can recieved")

    def define_point_using_math_search(self, point):
        x_shift = int((point.x() - self.left_x) // self.step_of_the_grid)
        y_shift = int((point.y() - self.bottom_y) // self.step_of_the_grid)
        if 0 <= x_shift < len(self.cells[0]) and 0 <= y_shift < len(self.cells):
            return self.cells[y_shift][x_shift]

        return None

    def difine_point(self, point):
        for row in self.cells:
            for cell in row:
                if not cell.borders.distance(point):
                    return cell

    def difine_point_or_create(self, point):
        for row in self.cells:
            for cell in row:
                if not cell.borders.distance(point):
                    if cell.geometry is not None:
                        return cell

    def get_point_expand_by_geometry_of_point(self, point):
        point_x = point.asPoint().x()
        point_y = point.asPoint().y()
        for row in self.cells:
            for cell in row:
                if cell.point_lx_ty.x() > point_x and point_x < cell.point_rx_ty.x():
                    if cell.point_rx_by.y() > point_y and point_y < cell.point_lx_ty.y():
                        return GeometryPointExpand(point, cell.n_row, cell.n_column)

    def get_point_expand_by_point(self, point):
        point_x = point.x()
        point_y = point.y()
        for row in self.cells:
            for cell in row:
                if cell.point_lx_ty.x() <= point_x <= cell.point_rx_ty.x():
                    if cell.point_rx_by.y() <= point_y <= cell.point_lx_ty.y():
                        return GeometryPointExpand(point, cell.n_row, cell.n_column)

    def get_multipolygon_by_points(self, point1, point2):
        cell1 = self.cells[point1.n_row][point1.n_column]
        cell2 = self.cells[point2.n_row][point2.n_column]
        if (cell1 or cell2) is None:
            raise Exception("One or both points not in grid")
        if cell1 == cell2:
            return cell1.geometry

        list_of_cells = []
        min_row = min(cell1.n_row, cell2.n_row)
        max_row = max(cell1.n_row, cell2.n_row)
        min_column = min(cell1.n_column, cell2.n_column)
        max_column = max(cell1.n_column, cell2.n_column)
        numbers = 0
        for i in range(min_row, max_row + 1):
            for k in range(min_column, max_column + 1):
                numbers += self.cells[i][k].number_of_polyg
                list_of_cells.append(self.cells[i][k])

        polygon = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2), QgsPointXY(2, 1)]])
        for i in range(len(list_of_cells)):
            if list_of_cells[i].geometry is not None and not list_of_cells[i].geometry.isNull():
                polygon.addPartGeometry(list_of_cells[i].geometry)
        polygon.deletePart(0)
        return polygon

    def get_multipolygon_by_cells(self, cell1, cell2):
        if (cell1 or cell2) is None:
            raise Exception("One or both points not in grid")
        if cell1 == cell2:
            return cell1.geometry

        list_of_cells = []
        min_row = min(cell1.n_row, cell2.n_row)
        max_row = max(cell1.n_row, cell2.n_row)
        min_column = min(cell1.n_column, cell2.n_column)
        max_column = max(cell1.n_column, cell2.n_column)
        numbers = 0
        for i in range(min_row, max_row + 1):
            for k in range(min_column, max_column + 1):
                numbers += self.cells[i][k].number_of_polyg
                list_of_cells.append(self.cells[i][k])

        polygon = QgsGeometry(list_of_cells[0].geometry)
        for i in range(1, len(list_of_cells)):
            if list_of_cells[i].geometry is not None:
                polygon.addPartGeometry(list_of_cells[i].geometry)
        return polygon

    def get_multipolygon_by_line(self, line):
        list_of_cells = []
        for row in self.cells:
            for cell in row:
                if cell.borders.distance(line) == 0:
                    list_of_cells.append(cell)

        polygon = QgsGeometry(list_of_cells[0].geometry)
        for i in range(1, len(list_of_cells)):
            polygon.addPartGeometry(list_of_cells[i].geometry)
        return polygon

    def visualize(self, project):
        project.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
        layer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\grid.shp")
        layer.dataProvider().truncate()
        feats = []
        for i in self.cells:
            for k in i:
                feat = QgsFeature(layer.fields())
                feat.setGeometry(k.borders)
                feats.append(feat)
        layer.dataProvider().addFeatures(feats)
        layer.triggerRepaint()

    def visualize_geometry_of_the_grid(self):
        geometry_list = []
        for row in self.cells:
            for cell in row:
                geometry_list.append(cell.geometry)
        Visualizer.update_layer_by_geometry_objects(r'C:\Users\Neptune\Desktop\Voronin qgis\shp\short_path2.shp',
                                                    geometry_list)


if __name__ == "__main__":
    a = GridForSearchMethods(2, 4)
    b = CellOfTheGrid(1, 1, 2, 2)
    a.add_cell_by_coordinates(b, 0, 1)
    print(a.cells)
