from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui
import os
import sys
from osgeo import gdal


pt = QgsFeature()   #premenna pre jednu feature

"""
#vytvorenie aplikacie (hlavne pre kreslenie na platno)
app=QgsApplication([], True)
qgis_prefix = os.getenv("QGISHOME")
QgsApplication.setPrefixPath(qgis_prefix,True)
QgsApplication.initQgis()

#vytvorenie platna
canvas = QgsMapCanvas()
canvas.setCanvasColor(Qt.white)
canvas.enableAntiAliasing(True)
"""





#vytvorenie vrstiev
Poly_layer = QgsVectorLayer("LineString", 'points', "memory")
#pripravenie vrstiev
QgsMapLayerRegistry.instance().addMapLayer(Poly_layer)
pr_poly = Poly_layer.dataProvider()


point1 = QgsPoint(1,1)
point2 = QgsPoint(112,113)

pt.setGeometry(QgsGeometry.fromPolyline([point1,point2]))
Poly_layer.addFeatures([pt])
Poly_layer.updateExtents()



error = QgsVectorFileWriter.writeAsVectorFormat(Poly_layer,
"/home/matej/Maps/map_polyi1.shp", "CP1250", None,"ESRI Shapefile")
if error == QgsVectorFileWriter.NoError:
    print "subor bol vytvoreny"
else:
    print "subor sa nepodarilo vytvori"



"""
#pridanie vrstvy na platno
canvas.setExtent(Poly_layer.extent())
canvas.setLayerSet([QgsMapCanvasLayer(Poly_layer)])
#zobrazenie platna
canvas.show()
#otvorenie okna
app.exec_()
QgsApplication.exitQgis()
"""
