from qgis.core import *
from ModuleInstruments.DebugLog import DebugInfo


class FindPathData:
    def __init__(self, project: QgsProject, start_point: QgsGeometry, target_point: QgsGeometry,
                 obstacles: QgsVectorLayer, path_to_save_layers: str, create_debug_layers: bool):
        self.project = project
        self.start_point = start_point
        self.target_point = target_point
        self.obstacles = obstacles
        self.path_to_save_layers = path_to_save_layers
        self.create_debug_layers = create_debug_layers


def check_if_FindPathData_is_ok(obj: FindPathData):
    # transform to EPSG 3395
    # need to change "project" to "QgsProject.instance" when import to module
    transformcontext = obj.project.transformContext()
    general_projection = QgsCoordinateReferenceSystem("EPSG:3395")
    xform = QgsCoordinateTransform(obj.obstacles.crs(), general_projection, transformcontext)

    # type: QgsPointXY
    obj.start_point = xform.transform(obj.start_point.asPoint())
    obj.target_point = xform.transform(obj.target_point.asPoint())
    return False
