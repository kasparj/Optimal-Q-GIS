from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui
import os
import sys
from osgeo import gdal


#konstanty a glob. premenne
POLYGON = 2 #nemenit
LINE    = 1 #nemenit
stat = 0    #stav kenecneho automatu
type_of_feature = 0 #prepinac typov
pt = QgsFeature()   #premenna pre jednu feature
points = []  #premenna pre pole bodov


#otvorenie subor ->prvy parameter
try:
    file_name = open(sys.argv[1],"r")
except:
    print "Nepodarilo sa otvorit subor"
    exit(1)


#vytvorenie aplikacie (hlavne pre kreslenie na platno)
app=QgsApplication([], True)
qgis_prefix = os.getenv("QGISHOME")
QgsApplication.setPrefixPath(qgis_prefix,True)
QgsApplication.initQgis()

#vytvorenie platna
canvas = QgsMapCanvas()
canvas.setCanvasColor(Qt.white)
canvas.enableAntiAliasing(True)

#vytvorenie vrstiev
Poly_layer = QgsVectorLayer("MultiPolygon", 'points', "memory")
if not Poly_layer.isValid():
    print "neplatna vrstva"

Line_layer = QgsVectorLayer("MultiLineString", 'points', "memory")
if not Line_layer.isValid():
    print "neplatna vrstva"

#pripravenie vrstiev
QgsMapLayerRegistry.instance().addMapLayer(Poly_layer)
QgsMapLayerRegistry.instance().addMapLayer(Line_layer)
pr_poly = Poly_layer.dataProvider()
pr_line = Line_layer.dataProvider()
pr_poly.addAttributes( [ QgsField("etaz", QVariant.String),
                    QgsField("typ" , QVariant.Int),
                    QgsField("size", QVariant.Double) ])
pr_line.addAttributes( [ QgsField("etaz", QVariant.String),
                    QgsField("typ" , QVariant.Int),
                    QgsField("size", QVariant.Double) ])
Poly_layer.updateFields()
Line_layer.updateFields()


#konecny automat pre spracovanie celeho suboru
#prepina sa do stavov podla najdenych tagov
for line in file_name:
    if "<ML>" in line:
        type_of_feature = LINE
    if "<MP>" in line:
        type_of_feature = POLYGON
    if "</L>" in line:
        stat = 0
        if type_of_feature == LINE:
            pt.setGeometry(QgsGeometry.fromPolyline(points))
            pt.setAttributes( ["slovo", 20, 0.3])
            pr_line.addFeatures([pt])
            Line_layer.updateExtents()
        elif type_of_feature == POLYGON:
            pt.setGeometry(QgsGeometry.fromPolygon([points]))
            pt.setAttributes( ["slovo", 20, 0.3])
            pr_poly.addFeatures([pt])
            Poly_layer.updateExtents()
        else:
            print "chybny typ" #toto by nemalo nastat
        points = []
    elif stat:
        number1 = line[line.find("\"")+1:line.find("$")]
        number2 = line[line.find("$")+1:line.find("\"", line.find("$"))]
        points.append(QgsPoint(float(number1),float(number2)))
    elif "<L>" in line:
        stat = 1

#testovacie veci - nechcem zatial vymazat
#props = { "color" : "255,128,0","style" : "no", "style" : "solid"}
#s = QgsFillSymbolV2.createSimple(props)
#Poly_layer.setRendererV2(QgsSingleSymbolRendererV2(s))
#Poly_layer.updateExtents()
#Poly_layer.updateFields()
#QgsMapLayerRegistry.instance().addMapLayer(Poly_layer)


#ulozenie vektorovej vrstvy
error = QgsVectorFileWriter.writeAsVectorFormat(Line_layer,
"/home/matej/map_line.shp", "CP1250", None,"ESRI Shapefile")
if error == QgsVectorFileWriter.NoError:
    print "subor bol vytvoreny"
else:
    print "subor sa nepodarilo vytvori"

error = QgsVectorFileWriter.writeAsVectorFormat(Poly_layer,
"/home/matej/map_poly.shp", "CP1250", None,"ESRI Shapefile")
if error == QgsVectorFileWriter.NoError:
    print "subor bol vytvoreny"
else:
    print "subor sa nepodarilo vytvori"

#pridanie vrstvy na platno
canvas.setExtent(Line_layer.extent())
canvas.setLayerSet([QgsMapCanvasLayer(Line_layer)])
#canvas.setExtent(Poly_layer.extent())
#canvas.setLayerSet([QgsMapCanvasLayer(Poly_layer)])
#zobrazenie platna
canvas.show()
#otvorenie okna
app.exec_()
QgsApplication.exitQgis()

