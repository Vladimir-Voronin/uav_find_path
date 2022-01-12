from qgis.core import *
from algorithms.addition.CellOfTheGrid import CellOfTheGrid
import numpy as np


class GridForRoadmap:
    def __init__(self, row, column):
        self.cells = np.zeros((row, column), dtype=CellOfTheGrid)

    def add_cell_by_coordinates(self, value, n_row, n_column):
        if isinstance(value, CellOfTheGrid):
            self.cells[n_row][n_column] = value
            value.myGrid = self
            value.n_row = n_row
            value.n_column = n_column
        else:
            raise Exception("Only <CellOfTheGrid> object can recieved")

    def difine_point(self, point):
        for row in self.cells:
            for cell in row:
                if cell.borders.distance(point) <= 0.0:
                    return cell

    def difine_point_or_create(self, point):
        for row in self.cells:
            for cell in row:
                if cell.borders.distance(point) <= 0.0:
                    if cell.geometry is not None:
                        return cell



    def get_multipolygon_by_points(self, point1, point2):
        cell1 = self.cells[point1.n_row][point1.n_column]
        cell2 = self.cells[point2.n_row][point2.n_column]
        if (cell1 or cell2) is None:
            raise Exception("One or both points not in grid")
        if cell1 == cell2:
            # print(f"{cell1.number_of_polyg}", end=" ")
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

    def get_multipolygon_by_cells(self, cell1, cell2):
        if (cell1 or cell2) is None:
            raise Exception("One or both points not in grid")
        if cell1 == cell2:
            # print(f"{cell1.number_of_polyg}", end=" ")
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

    def vizualize(self, project):
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


if __name__ == "__main__":
    a = GridForRoadmap(2, 4)
    b = CellOfTheGrid(1, 1, 2, 2)
    a.add_cell_by_coordinates(b, 0, 1)
    print(a.cells)