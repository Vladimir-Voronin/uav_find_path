from qgis.core import *

# connect to project
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


# main code
l = [layer.name() for layer in project.mapLayers().values()]
# dictionary with key = layer name and value = layer object
layers_list = {}
for l in project.mapLayers().values():
  layers_list[l.name()] = l

print(layers_list)

vlayer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp")

if not vlayer.isValid():
    print("Layer failed to load!")
else:
    project.addMapLayer(vlayer)

print(type(vlayer))
features = vlayer.getFeatures()

for feature in features:
    print(type(feature.geometry()))
    # retrieve every feature with its geometry and attributes
    print("Feature ID: ", feature.id())
    # fetch geometry
    # show some information about the feature geometry
    geom = feature.geometry()
    geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
    if geom.type() == QgsWkbTypes.PointGeometry:
        # the geometry type can be of single or multi type
        if geomSingleType:
            x = geom.asPoint()
            print("Point: ", x)
        else:
            x = geom.asMultiPoint()
            print("MultiPoint: ", x)
    elif geom.type() == QgsWkbTypes.LineGeometry:
        if geomSingleType:
            x = geom.asPolyline()
            print("Line: ", x, "length: ", geom.length())
        else:
            x = geom.asMultiPolyline()
            print("MultiLine: ", x, "length: ", geom.length())
    elif geom.type() == QgsWkbTypes.PolygonGeometry:
        if geomSingleType:
            x = geom.asPolygon()
            print("Polygon: ", x, "Area: ", geom.area())
        else:
            x = geom.asMultiPolygon()
            print("MultiPolygon: ", x, "Area: ", geom.area())
    else:
        print("Unknown or invalid geometry")
    # fetch attributes
    attrs = feature.attributes()
    # attrs is a list. It contains all the attribute values of this feature
    print(attrs)
    # for this test only print the first feature
    break