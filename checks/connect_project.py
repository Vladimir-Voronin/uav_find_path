from qgis.core import QgsProject
# with open(r'C:\OSGEO4~1\share\proj\proj.db') as f:
#     ...
from qgis.core import *

# Supply path to qgis install location
QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
print("CP0")
#
# # Create a reference to the Qg
# sApplication.  Setting the
# # second argument to False disables the GUI.
qgs = QgsApplication([], False)
print("CP1")
#
# # Load providers
qgs.initQgis()
# #
# # # Write your code here to load some layers, use processing
# # # algorithms, etc.
# #
# # # Finally, exitQgis() is called to remove the
# # # provider and layer registries from memory
# qgs.exitQgis()
# print("End")

project = QgsProject.instance()
project.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
print(project.fileName())
layers = QgsProject.instance().layerTreeRoot().children()
for i in layers:
    print(i.layer())

path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
layer = QgsVectorLayer(path)
print(layer)
for i in layer.getFeatures():
    print(i)
print(layer.crs())