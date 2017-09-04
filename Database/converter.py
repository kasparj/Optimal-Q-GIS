#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import codecs
import qgis
from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui
from PyQt4.QtGui import QProgressBar
from qgis.utils import iface
from names import *
from vychova_strings import vychova_strings


POLY = QgsFeature()  # premenna pre jedne geom. objekt


def open_layer(name, address, type_ft):
    """Otvori vrstu, ktora sa zobrazi pod nazvom "name".

    otvori sa na adrese - cela cesta
    type_ft = ogr pre vektorove vrstvy, "delimitedText" pre csv
    """
    new_ft = QgsVectorLayer(address, name, type_ft)
    if (new_ft.featureCount() < 1):
        return
    QgsMapLayerRegistry.instance().addMapLayer(new_ft)
    canvas = qgis.utils.iface.mapCanvas()
    canvas.setExtent(new_ft.extent())


def create_points(lines):
    """Vytvori list z <L>, z kazdeho bodu <B> urobi QgsPoint."""
    points = []
    for point in lines.findall('B'):
        np = point.get('S')
        number1 = np[:np.find("$")]  # odstrihne od zaciatku po $
        number2 = np[np.find("$")+1:]  # odstrihne od $ dokonca
        points.append(QgsPoint(float(number2), -1 * float(number1)))
    return points


def create_from_MP(MP, layer, atts):
    """Vytvorenie polygonu.

    MP = objekt <MP>
    layer = vrstva do ktorej chceme pridat objekt
    atts = list vsetkych atributov, ktore chceme k danemu objektu priradit
    """
    finished_list = []
    for polygons in MP.findall('P'):
        one_poly = []
        for lines in polygons.findall('L'):
            points = create_points(lines)  # ziskam zoznam bodov
            one_poly.append(points)
        finished_list.append(one_poly)
    POLY.setGeometry(QgsGeometry.fromMultiPolygon(finished_list))  # vytvorim objekt
    POLY.setAttributes(atts)  # nastavenie atributov
    layer.addFeatures([POLY])


def create_from_ML(ML, layer, atts):
    """Obodba pre create_from_MP, ale pracuje s ML objektom."""
    for lines in ML.findall('L'):
        points = create_points(lines)
        POLY.setGeometry(QgsGeometry.fromPolyline(points))
        POLY.setAttributes(atts)
        layer.addFeatures([POLY])


def parse_polygon(psk, lyr, porast, odd_att, dil_att, por_atts, my_id, ETZ_ID,
                  DRV_ID, etz_file, drv_file, pos_file, zal_file, kat_file):
    """Spracuj jeden polygon."""
    known = False
    psk_atts = create_attributes(psk, LIST_PSK)
    try_id = psk.get("PSK_ID")
    if try_id:
        my_id = int(try_id)
        known = True
    if not psk.findall('PSK_OBRAZ'):
        return None
    progress_count = 0
    atts = [odd_att]
    atts.append(dil_att)
    for item in por_atts:
        atts.append(item)
    for item in psk_atts:
        atts.append(item)

    atts.append(my_id)
    my_id_id = len(atts)-1
    atts.extend(['BW', 50, 10000, 0, 0, 1, 0, ';', ';', -1])
    for psk_obraz in psk.findall('PSK_OBRAZ'):
        for MP in psk_obraz.findall('MP'):
            create_from_MP(MP, lyr, atts)

    for etaz in psk.findall('ETZ'):
        etz_id = ETZ_ID
        ETZ_ID += 1
        etz_atts = create_attributes(etaz, LIST_ETZ)
        etz_atts.append(str(my_id))
        etz_atts.append(str(etz_id))
        to_write = "\",\"".join(etz_atts)
        etz_file.write("\""+to_write+'\"\n')
        for drevina in etaz.findall('DRV'):
            my_drv_id = DRV_ID
            DRV_ID += 1
            drv_atts = create_attributes(drevina, LIST_DRV)
            drv_atts.append(str(etz_id))
            drv_atts.append(str(my_drv_id))

            to_write = "\",\"".join(drv_atts)
            drv_file.write("\""+to_write+'\"\n')

            for poskodenie in drevina.findall('POS'):
                pos_atts = create_attributes(poskodenie, LIST_POS)
                pos_atts.append(str(my_drv_id))
                to_write = "\",\"".join(pos_atts)
                pos_file.write("\""+to_write+'\"\n')
                progress_count += 1
        for zalozenie in etaz.findall('ZAL'):
            zal_atts = create_attributes(zalozenie, LIST_ZAL)
            zal_atts.append(str(etz_id))

            to_write = "\",\"".join(zal_atts)
            zal_file.write("\""+to_write+'\"\n')

    for kategoria in porast.findall('KAT'):
        kat_atts = create_attributes(kategoria, LIST_KAT)
        kat_atts.append(str(my_id))
        to_write = "\",\"".join(kat_atts)
        kat_file.write("\""+to_write+'\"\n')

    return (ETZ_ID, DRV_ID, progress_count)


#ziskam list atributov parsovanim
#OBJ je objekt, ktory obsahuje atributy, ktorych zoznam je v list_for_obj
#e.g. objekt je <ODD> tak k nemu dam list_of_odd
def create_attributes(OBJ, list_for_obj):
    atts = []
    for att in list_for_obj:#pre kazdu polozku zo zoznamu
        new_item = OBJ.get(att)#vyhladam co jej odpoveda
        if new_item:#ak najdem nieco
            atts.append(new_item.replace("\"","\\\'"))#tak to zapisem
        else:
            atts.append("")#inak zapisem prazdy retazec
    return atts#vratim list


def parse_taz_type(taz_typ, atts, file_to_write):
    """Parse TAZ_TYP."""
    atts.insert(0, taz_typ.get('PRIRAZENI'))
    atts.insert(0, taz_typ.get('TYP'))
    for sec in taz_typ.findall('SEC'):
        tmp_atts = atts[:]
        tmp_atts.insert(0, sec.get('ODSTUP'))
        for zasah in sec.findall('ZASAH'):
            tmp_atts1 = tmp_atts[:]
            tmp_atts1.insert(0, zasah.get('INTENZITA'))
            tmp_atts1.insert(0, zasah.get('DR'))
            tmp_atts1.insert(0, zasah.get('ETAZ'))
            to_write = "\",\"".join(tmp_atts1)
            file_to_write.write("\""+to_write+'\"\n')


#funkcia na ulozenie .shp vrstvy
#layer je platny ukazatel na vrstvu
#address je cesta aj s menom suboru kde sa ma ulozit
#pri chybe vracia 1 inak vracia 0
def save_layer(layer,address):
    error = QgsVectorFileWriter.writeAsVectorFormat(layer,
        address, "System", None,"ESRI Shapefile")
    if error == QgsVectorFileWriter.NoError:
        return 0
    else:
        return 1

#Tuto funkciu volat externe!
#pretty_name = adresa vstupneho suboru
#folder_name = adresa, kam sa bude ukladat vysledok
def convert_to_shp(pretty_name,folder_name):

    i = 0#percento dokoncenia pre progressBar
    progressMessageBar =\
            iface.messageBar().createMessage('Konvertujem')#pridam text konvertujem
    progress = QProgressBar()#vytvorim progressBar
    progress.setMaximum(100)#maxium je 100
    progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)#zarovnam ho vlavo
    progressMessageBar.layout().addWidget(progress)#a pridam ho do hroenj listy
    iface.messageBar().pushWidget(progressMessageBar,
                        iface.messageBar().INFO)
    


    #praca s CSV - otvorim si vsetky potrebne .csv subory a rovno do nich
        #zapisem aj hlavicku - mohlo by sa to vytiahnut nejako do funckie...
    #otvorim kazdy subor a zapisem tam aj hlavicky tabuliek
    try:
        vys_obn_file = codecs.open(folder_name+'/vys_obn_file.csv','w',encoding='utf-8')
        vys_obn_file.write(",".join(NAMES_OBN)+'\n')
    except:
        return 1

    try:
        taz_typ_file = codecs.open(folder_name+'/taz_typ_file.csv','w',encoding='utf-8')
        taz_typ_file.write(",".join(NAMES_TAZ_TYP)+'\n')
    except:
        return 1

    try:
        etz_file = codecs.open(folder_name+'/etz_file.csv','w',encoding='utf-8')
        etz_file.write(",".join(NAMES_ETZ)+'\n')
    except:
        return 1

    try:
        vys_vych_file = codecs.open(folder_name+'/vys_vych_file.csv','w',encoding='utf-8')
        vys_vych_file.write(",".join(NAMES_VYCH)+'\n')
    except:
        return 1

    try:
        drv_file = codecs.open(folder_name+'/drv_file.csv','w',encoding='utf-8')
        drv_file.write(",".join(NAMES_DRV)+'\n')
    except:
        return 1


    try:
        kat_file = codecs.open(folder_name+'/kat_file.csv','w',encoding='utf-8')
        kat_file.write(",".join(NAMES_KAT)+'\n')
    except:
        return 1


    try:
        zal_file = codecs.open(folder_name+'/zal_file.csv','w',encoding='utf-8')
        zal_file.write(",".join(NAMES_ZAL)+'\n')
    except:
        return 1


    try:
        pos_file = codecs.open(folder_name+'/pos_file.csv','w',encoding='utf-8')
        pos_file.write(",".join(NAMES_POS)+'\n')
    except:
        return 1
#------------------------------------------------------------------------
#priprava vrstiev
#------------------------------------------------------------------------
#format:
#Multi[Polygon/LineString/Point] - podla typu geometrie ?crs=EPSG:5514 - typ ukladania
#Nazov vrsty, ktory je zobrazny v QGIS
#memory - pracujeme s mamory provider-om
    
    
    global KPO_layer
    #KPO_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:4326", 'KPO', "memory")
    KPO_layer = QgsVectorLayer("Polygon?crs=EPSG:5514", 'KPO', "memory")
    if not KPO_layer.isValid():
            return 1
    
    
    global JP_layer
    JP_layer = QgsVectorLayer("Polygon?crs=EPSG:5514", 'Ine plochy', "memory")
    if not JP_layer.isValid():
            return 1


    global BZL_layer
    BZL_layer = QgsVectorLayer("Polygon?crs=EPSG:5514", 'Bezlesie', "memory")
    if not BZL_layer.isValid():
            return 1

    global KLO_layer
    KLO_layer = QgsVectorLayer("LineString?crs=EPSG:5514", 'KLO', "memory")
    if not KLO_layer.isValid():
            return 1

    """
    global KBO_layer
    KBO_layer = QgsVectorLayer("MultiPoint?crs=EPSG:4326", 'Body', "memory")
    if not KBO_layer.isValid():
            return 1


    global KTO_layer
    KTO_layer = QgsVectorLayer("MultiPoint?crs=EPSG:4326", 'KTO', "memory")
    if not KTO_layer.isValid():
            return 1
    """
    global PSK_layer
    PSK_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:5514", 'Lesne porasty', "memory")
    if not PSK_layer.isValid():
            return 1

    global TAZ_layer
    TAZ_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:5514", 'Tazobne typy', "memory")
    if not TAZ_layer.isValid():
            return 1

    i = 5
    progress.setValue(i)
    # priprava vstiev, cast druha
    # format jedneho parametra :
    # QgsField(
    # "nazov stlpca v tabulke - moze sa menit lubovolne, ale nie poradie"
    # tieto parametre sa zobrazia v tabulke uzivatelovi
    # typ parametra QVariant.[String/Int/Double] - pomenit tak, aby odpovedalo
    # NEMENIT POSLEDNY PARAMTERE - XXXX-NUMB!


    global psk_poly
    psk_poly = PSK_layer.dataProvider()
    psk_poly.addAttributes([
                            QgsField("ODD", QVariant.String),
                            QgsField("DIL", QVariant.String),

                            QgsField("POR", QVariant.String),
                            QgsField("SDR_POR", QVariant.String),
                            QgsField("MAJ_KOD", QVariant.String),
                            QgsField("MAJ_NAZ", QVariant.String),
                            QgsField("MAJ_DRUH", QVariant.String),
                            QgsField("ORG_UROVEN", QVariant.String),
                            QgsField("PAS_OHR", QVariant.String),
                            QgsField("LES_OBL", QVariant.String),
                            QgsField("LES_PODOBL", QVariant.String),
                            QgsField("ZVL_STATUT", QVariant.String),
                            QgsField("OLH_LIC", QVariant.String),
                            QgsField("OLH", QVariant.String),
                            QgsField("POR_TEXT", QVariant.String),
                            QgsField("HIST_LHC", QVariant.String),
                            QgsField("HIST_LHPOD", QVariant.String),
                            QgsField("HIST_ROZD", QVariant.String),

                            QgsField("PSK", QVariant.String),
                            QgsField("PSK_P0", QVariant.Double),
                            QgsField("PSK_V", QVariant.Double),
                            QgsField("PSK_P", QVariant.Double),
                            QgsField("KVAL_P", QVariant.Int),
                            QgsField("ORP", QVariant.Int),
                            QgsField("KRAJ", QVariant.String),
                            QgsField("KATUZE_KOD", QVariant.Int),
                            QgsField("KAT_PAR_KOD", QVariant.Int),
                            QgsField("SLT", QVariant.String),
                            QgsField("LT", QVariant.String),
                            QgsField("TER_TYP", QVariant.Int),
                            QgsField("PRIB_VZD", QVariant.Int),
                            QgsField("HOSP_ZP", QVariant.Int),
                            QgsField("DAN", QVariant.String),
                            QgsField("PSK_TEXT", QVariant.String),
                            QgsField("CISLO_TEL", QVariant.Int),

                            QgsField("PSK_NUM", QVariant.Int),
                            QgsField("COLOR", QVariant.String),
                            QgsField("max_len", QVariant.Double),
                            QgsField("max_area", QVariant.Double),
                            QgsField("min_len", QVariant.Double),
                            QgsField("min_area", QVariant.Double),
                            QgsField("max_to_neigh", QVariant.Double),
                            QgsField("priorita", QVariant.Int),
                            QgsField("sekvencia", QVariant.String),
                            QgsField("neighbours", QVariant.String),
                            QgsField("original", QVariant.Int),
                            ])
    PSK_layer.updateFields()

    global taz_poly
    taz_poly = TAZ_layer.dataProvider()
    taz_poly.addAttributes([
                            QgsField("ODD", QVariant.String),
                            QgsField("DIL", QVariant.String),

                            QgsField("POR", QVariant.String),
                            QgsField("SDR_POR", QVariant.String),
                            QgsField("MAJ_KOD", QVariant.String),
                            QgsField("MAJ_NAZ", QVariant.String),
                            QgsField("MAJ_DRUH", QVariant.String),
                            QgsField("ORG_UROVEN", QVariant.String),
                            QgsField("PAS_OHR", QVariant.String),
                            QgsField("LES_OBL", QVariant.String),
                            QgsField("LES_PODOBL", QVariant.String),
                            QgsField("ZVL_STATUT", QVariant.String),
                            QgsField("OLH_LIC", QVariant.String),
                            QgsField("OLH", QVariant.String),
                            QgsField("POR_TEXT", QVariant.String),
                            QgsField("HIST_LHC", QVariant.String),
                            QgsField("HIST_LHPOD", QVariant.String),
                            QgsField("HIST_ROZD", QVariant.String),

                            QgsField("PSK", QVariant.String),
                            QgsField("PSK_P0", QVariant.Double),
                            QgsField("PSK_V", QVariant.Double),
                            QgsField("PSK_P", QVariant.Double),
                            QgsField("KVAL_P", QVariant.Int),
                            QgsField("ORP", QVariant.Int),
                            QgsField("KRAJ", QVariant.String),
                            QgsField("KATUZE_KOD", QVariant.Int),
                            QgsField("KAT_PAR_KOD", QVariant.Int),
                            QgsField("SLT", QVariant.String),
                            QgsField("LT", QVariant.String),
                            QgsField("TER_TYP", QVariant.Int),
                            QgsField("PRIB_VZD", QVariant.Int),
                            QgsField("HOSP_ZP", QVariant.Int),
                            QgsField("DAN", QVariant.String),
                            QgsField("PSK_TEXT", QVariant.String),
                            QgsField("CISLO_TEL", QVariant.Int),

                            QgsField("PSK_NUM", QVariant.Int),
                            QgsField("COLOR", QVariant.String),
                            QgsField("max_len", QVariant.Double),
                            QgsField("max_area", QVariant.Double),
                            QgsField("min_len", QVariant.Double),
                            QgsField("min_area", QVariant.Double),
                            QgsField("max_to_neigh", QVariant.Double),
                            QgsField("priorita", QVariant.Int),
                            QgsField("sekvencia", QVariant.String),
                            QgsField("neighbours", QVariant.String),
                            QgsField("original", QVariant.Int),
                            ])
    TAZ_layer.updateFields()

    global kpo_poly
    kpo_poly = KPO_layer.dataProvider()
    kpo_poly.addAttributes([
                            QgsField("PLO_DRUH", QVariant.Int),
                            QgsField("PLO_ZNACKA", QVariant.Int),
                            QgsField("PLO_BARVA", QVariant.Int),
                            QgsField("L_", QVariant.String)
                            ])
    KPO_layer.updateFields()

    global jp_poly
    jp_poly = JP_layer.dataProvider()
    jp_poly.addAttributes([
                            QgsField("ODD", QVariant.String),
                            QgsField("DIL", QVariant.String),

                            QgsField("POR", QVariant.String),
                            QgsField("SDR_POR", QVariant.String),
                            QgsField("MAJ_KOD", QVariant.String),
                            QgsField("MAJ_NAZ", QVariant.String),
                            QgsField("MAJ_DRUH", QVariant.String),
                            QgsField("ORG_UROVEN", QVariant.String),
                            QgsField("PAS_OHR", QVariant.String),
                            QgsField("LES_OBL", QVariant.String),
                            QgsField("LES_PODOBL", QVariant.String),
                            QgsField("ZVL_STATUT", QVariant.String),
                            QgsField("OLH_LIC", QVariant.String),
                            QgsField("OLH", QVariant.String),
                            QgsField("POR_TEXT", QVariant.String),
                            QgsField("HIST_LHC", QVariant.String),
                            QgsField("HIST_LHPOD", QVariant.String),
                            QgsField("HIST_ROZD", QVariant.String),

                            QgsField("JP", QVariant.Int),
                            QgsField("JP_PUPFL", QVariant.String),
                            QgsField("ORP", QVariant.Int),
                            QgsField("KRAJ", QVariant.String),
                            QgsField("KATUZE_KOD", QVariant.Int),
                            QgsField("JP_PO", QVariant.Double),
                            QgsField("JP_V", QVariant.Double),
                            QgsField("JP_P", QVariant.Double),
                            QgsField("KVAL_P", QVariant.Int),
                            QgsField("KAT_PAR_KOD", QVariant.Int),
                            QgsField("JP_VYUZ", QVariant.String),
                            QgsField("JP_DRUH", QVariant.String),
                            QgsField("CISLO_TEL", QVariant.Int),
                            ])
    JP_layer.updateFields()

    global bzl_poly
    bzl_poly = BZL_layer.dataProvider()
    bzl_poly.addAttributes([
                            QgsField("ODD", QVariant.String),
                            QgsField("DIL", QVariant.String),

                            QgsField("POR", QVariant.String),
                            QgsField("SDR_POR", QVariant.String),
                            QgsField("MAJ_KOD", QVariant.String),
                            QgsField("MAJ_NAZ", QVariant.String),
                            QgsField("MAJ_DRUH", QVariant.String),
                            QgsField("ORG_UROVEN", QVariant.String),
                            QgsField("PAS_OHR", QVariant.String),
                            QgsField("LES_OBL", QVariant.String),
                            QgsField("LES_PODOBL", QVariant.String),
                            QgsField("ZVL_STATUT", QVariant.String),
                            QgsField("OLH_LIC", QVariant.String),
                            QgsField("OLH", QVariant.String),
                            QgsField("POR_TEXT", QVariant.String),
                            QgsField("HIST_LHC", QVariant.String),
                            QgsField("HIST_LHPOD", QVariant.String),
                            QgsField("HIST_ROZD", QVariant.String),

                            QgsField("BZL", QVariant.Int),
                            QgsField("ORP", QVariant.Int),
                            QgsField("KRAJ", QVariant.String),
                            QgsField("KATUZE_KOD", QVariant.Int),
                            QgsField("BZL_PO", QVariant.Double),
                            QgsField("BZL_V", QVariant.Double),
                            QgsField("BZL_P", QVariant.Double),
                            QgsField("KVAL_P", QVariant.Int),
                            QgsField("KAT_PAR_KOD", QVariant.Int),
                            QgsField("BZL_VYUZ", QVariant.String),
                            QgsField("BZL_DRUH", QVariant.String),
                            QgsField("CISLO_TEL", QVariant.Int),
                            ])
    BZL_layer.updateFields()

    global klo_line
    klo_line = KLO_layer.dataProvider()
    klo_line.addAttributes([
                            QgsField("LIN_DRUH", QVariant.Int),
                            QgsField("LIN_ZNACKA", QVariant.Int),
                            QgsField("LIN_BARVA", QVariant.Int),
                            QgsField("L_", QVariant.String),
                            ])
    KLO_layer.updateFields()

    """
    global kbo_line
    kbo_line = KBO_layer.dataProvider()
    kbo_line.addAttributes([
                            QgsField("BOD_DRUH", QVariant.Int),
                            QgsField("BOD_ZNACKA", QVariant.Int),
                            QgsField("BOD_UHELZN", QVariant.Double),
                            QgsField("BOD_BARVA", QVariant.Int),
                            QgsField("L_", QVariant.String),
                            ])
    KBO_layer.updateFields()


    #QgsMapLayerRegistry.instance().addMapLayer(KTO_layer)
    global kto_line
    kto_line = KTO_layer.dataProvider()
    kto_line.addAttributes([
                            QgsField("text", QVariant.String),
                            QgsField("TXT_STYL", QVariant.Int),
                            QgsField("TXT_UHEL", QVariant.Double),
                            QgsField("L_",QVariant.String)
                            ])
    KTO_layer.updateFields()
    """

    i = 7
    progress.setValue(i)

# ------------------------------------------------------------------------
#                        parser xml + samotne ukladanie
# ------------------------------------------------------------------------

    tree = ET.parse(pretty_name)  # pripravime si vstupn subor
    if not tree:
        return 2
    root = tree.getroot()

    PSK_ID = 0
    TAZ_ID = 0
    ETZ_ID = 0
    DRV_ID = 0

    for child in root:
        # TODO save_LHC(child.attrib)
        # TODO HS,OU1,OU2,MZD

        i = 15
        progress.setValue(i)
        """
        for KBO in child.findall('KBO'):
            atts = create_attributes(KBO, LIST_KBO)
            if not KBO.findall('BOD_OBRAZ'):
                return 3
            for BOD_obraz in KBO.findall('BOD_OBRAZ'):

                for MB in BOD_obraz.findall('MB'):
                    for point in MB.findall('B'):
                        np =  point.get('S')
                        number1 = np[:np.find("$")]
                        number2 = np[np.find("$")+1:]
                        POLY.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(number1),float(number2))))
                        POLY.setAttributes(atts)
                        kbo_line.addFeatures([POLY])

        i = 22  
        progress.setValue(i)

        for KTO in child.findall('KTO'):
            atts = create_attributes(KTO,LIST_KTO)
            if not KTO.findall('TXT_OBRAZ'):
                return 3
            for TXT_obraz in KTO.findall('TXT_OBRAZ'):
                for B in TXT_obraz.findall('B'):
                    np= B.get('S')
                    number1 = np[:np.find("$")]
                    number2 = np[np.find("$")+1:]
                    POLY.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(number1),float(number2))))
                    POLY.setAttributes(atts)
                    kto_line.addFeatures([POLY])

        i = 29  
        progress.setValue(i)

        """
        """
        findall - najde vsetky podradene tagy ktore su ako argument
        vytovim zoznam atributov volanim funkcie create_attributes
        """

        for KPO in child.findall('KPO'):
            if not KPO.findall('PLO_OBRAZ'):
                return 3
            atts = create_attributes(KPO, LIST_KPO)
            for KPO_obraz in KPO.findall('PLO_OBRAZ'):
                for MP in KPO_obraz.findall('MP'):
                    create_from_MP(MP, kpo_poly, atts)



        i = 19  
        progress.setValue(i)
        for KLO in child.findall('KLO'):
            atts = create_attributes(KLO, LIST_KLO)
            if not KLO.findall('LIN_OBRAZ'):
                return 3
            for KLO_obraz in KLO.findall('LIN_OBRAZ'):
                for ML in KLO_obraz.findall('ML'):
                    create_from_ML(ML,klo_line,atts)
        i = 24
        progress.setValue(i)


        for oddiel in child.findall('ODD'):
            odd_att =  oddiel.get('ODD')
            for diel in oddiel.findall('DIL'):
                dil_att =  diel.get('DIL')
                for porast in diel.findall('POR'):
                    por_atts = create_attributes(porast,LIST_POR)
                    for bezlesie in porast.findall('BZL'):
                        if not bezlesie.findall('BZL_OBRAZ'):
                            return 3
                        bzl_atts = create_attributes(bezlesie, LIST_BZL)
#from this
                        atts = [odd_att]
                        atts.append(dil_att)
                        for item in por_atts:
                            atts.append(item)
                        for item in bzl_atts:
                            atts.append(item)
#to this
                        for bzl_obraz in bezlesie.findall('BZL_OBRAZ'):
                            for MP in bzl_obraz.findall('MP'):
                                create_from_MP(MP, bzl_poly, atts)

                    for jine in porast.findall('JP'):
                        jp_atts = create_attributes(jine, LIST_JP)
                        if not jine.findall('JP_OBRAZ'):
                            return 3
#from this
                        atts = [odd_att]
                        atts.append(dil_att)
                        for item in por_atts:
                            atts.append(item)
                        for item in jp_atts:
                            atts.append(item)
#to this
                        for jp_obraz in jine.findall('JP_OBRAZ'):
                            for MP in jp_obraz.findall('MP'):
                                create_from_MP(MP, jp_poly, atts)

                    for psk in porast.findall('PSK'):
                        etz_id, drv_id, new_i = parse_polygon(psk,
                                                              psk_poly,
                                                              porast,
                                                              odd_att,
                                                              dil_att,
                                                              por_atts,
                                                              PSK_ID,
                                                              ETZ_ID,
                                                              DRV_ID,
                                                              etz_file,
                                                              drv_file,
                                                              pos_file,
                                                              zal_file,
                                                              kat_file)
                        PSK_ID += 1
                        ETZ_ID = etz_id
                        DRV_ID = drv_id
                        i += new_i
                        if (i > 95):
                            i = 95
                        progress.setValue(i)

                    for taz in porast.findall('TazebniPrvek'):
                        PSK_layer.updateExtents()
                        psk_id = taz.get("ID_PSK")

                        for vys_vych in taz.findall('VYSLEDEK_VYCHOVA'):
                            vys_vych_atts = create_attributes(vys_vych,
                                                              LIST_VYCH)
                            vys_vych_atts[-1] = vychova_strings[int(vys_vych_atts[-1])]
                            vys_vych_atts.append(psk_id)
                            for per in vys_vych.findall('TEZBA_PERIODA'):
                                tmp_atts = vys_vych_atts[:]
                                tmp_atts.insert(0, per.get('VAL'))
                                tmp_atts.insert(0, per.get('PER'))

                                to_write = "\",\"".join(tmp_atts)
                                vys_vych_file.write("\""+to_write+'\"\n')

                        for vys_obn in taz.findall('VYSLEDEK_OBNOVA'):
                            vys_obn_atts = create_attributes(vys_obn,
                                                             LIST_OBN)
                            vys_obn_atts.append(psk_id)
                            to_write = "\",\"".join(vys_obn_atts)
                            vys_obn_file.write("\""+to_write+'\"\n')

                        for taz_typ in taz.findall('TAZ_TYP'):
                            atts = [taz_typ.get('ID')]
                            atts.append(psk_id)
                            atts.insert(0, taz_typ.get('PRIRAZENI'))
                            atts.insert(0, taz_typ.get('TYP'))
                            for sec in taz_typ.findall('SEC'):
                                tmp_atts = atts[:]
                                tmp_atts.insert(0, sec.get('ID'))
                                tmp_atts.insert(0, sec.get('ODSTUP'))
                                for zasah in sec.findall('ZASAH'):
                                    tmp_atts1 = tmp_atts[:]
                                    tmp_atts1.insert(0, zasah.get('INTENZITA'))
                                    tmp_atts1.insert(0, zasah.get('DR'))
                                    tmp_atts1.insert(0, zasah.get('ETAZ'))
                                    to_write = "\",\"".join(tmp_atts1)
                                    taz_typ_file.write("\""+to_write+'\"\n')

                        request = QgsFeatureRequest()
                        request.setFilterExpression(u'"PSK_NUM" = %s' % psk_id)
                        psk_ft = psk_poly.getFeatures(request).next()
                        POLY.setGeometry(psk_ft.geometry())
                        POLY.setAttributes(psk_ft.attributes())
                        taz_poly.addFeatures([POLY])

    PSK_layer.updateExtents()
    TAZ_layer.updateExtents()
    canvas = qgis.utils.iface.mapCanvas()
    if (TAZ_layer.featureCount() > 1):
        canvas.setExtent(TAZ_layer.extent())
    else:
        canvas.setExtent(PSK_layer.extent())
    qgis.utils.iface.mapCanvas().refresh()

    vys_vych_file.close()
    vys_obn_file.close()
    taz_typ_file.close()
    etz_file.close()
    drv_file.close()
    kat_file.close()
    pos_file.close()
    zal_file.close()

    #otvorim si csv ako delimitedText
    #ulozim to ako vektorovu vrstvu - vznikne mi .dbf
    #to otvorim ako vektorovu vrstvu
    #a mam editovatlnu vrstvu atributov

    etz_csv = QgsVectorLayer("file:///"+folder_name+'/etz_file.csv',"Porast","delimitedtext")
    save_layer(etz_csv,folder_name+'/etz')
    new_etz = QgsVectorLayer(folder_name+'/etz.dbf',"Porast","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_etz)

    taz_typ_csv = QgsVectorLayer("file:///"+folder_name+'/taz_typ_file.csv',"Tazobne typy","delimitedtext")
    save_layer(taz_typ_csv,folder_name+'/taz_typ')
    new_taz_typ = QgsVectorLayer(folder_name+'/taz_typ.dbf',"Tazobne typy","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_taz_typ)

    drv_csv = QgsVectorLayer("file:///"+folder_name+'/drv_file.csv',"Dreviny","delimitedtext")
    save_layer(drv_csv,folder_name+'/drv')
    new_drv = QgsVectorLayer(folder_name+'/drv.dbf',"Dreviny","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_drv)

    kat_csv = QgsVectorLayer("file:///"+folder_name+'/kat_file.csv',"Kategorie","delimitedtext")
    save_layer(kat_csv,folder_name+'/kat')
    new_kat = QgsVectorLayer(folder_name+'/kat.dbf',"Kategorie","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_kat)

    zal_csv = QgsVectorLayer("file:///"+folder_name+'/zal_file.csv',"Zalozenie","delimitedtext")
    save_layer(zal_csv,folder_name+'/zal')
    new_zal = QgsVectorLayer(folder_name+'/zal.dbf',"Zalozenie","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_zal)

    pos_csv = QgsVectorLayer("file:///"+folder_name+'/pos_file.csv',"Poskodenia","delimitedtext")
    save_layer(pos_csv,folder_name+'/pos')
    new_pos = QgsVectorLayer(folder_name+'/pos.dbf',"Poskodenia","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_pos)

    vys_vych_csv = QgsVectorLayer("file:///"+folder_name+'/vys_vych_file.csv',"VysledkyVychova","delimitedtext")
    save_layer(vys_vych_csv,folder_name+'/vys_vych')
    new_vys_vych = QgsVectorLayer(folder_name+'/vys_vych.dbf',"VysledkyVychova","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_vys_vych)

    vys_obn_csv = QgsVectorLayer("file:///"+folder_name+'/vys_obn_file.csv',"VysledkyObnova","delimitedtext")
    save_layer(vys_obn_csv,folder_name+'/vys_obn')
    new_vys_obn = QgsVectorLayer(folder_name+'/vys_obn.dbf',"VysledkyObnova","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_vys_obn)

    #etz1=qgis.utils.iface.addVectorLayer("file:///"+folder_name+'/etz.dbf',"Porast1","ogr")
    #joinObject = QgsVectorJoinInfo()
    #joinObject.joinLayerId = por_csv.id()
    #joinObject.joinFieldName = 'MY_ID'
    #joinObject.targetFieldName = 'POR_NUMB'
    #PSK_layer.addJoin(joinObject)

    #ulozim vrstvy 
    error_code = 0
    err_stat = save_layer(PSK_layer,folder_name+'/PSK')
    if err_stat != 0:
        err_code = err_stat

    err_stat = save_layer(TAZ_layer,folder_name+'/TAZ')
    if err_stat != 0:
        err_code = err_stat

    err_stat = save_layer(KPO_layer,folder_name+'/KPO')
    if err_stat != 0:
        err_code = err_stat

    err_stat = save_layer(JP_layer,folder_name+'/JP')
    if err_stat != 0:
        err_code = err_stat

    err_stat = save_layer(BZL_layer,folder_name+'/BZL')
    if err_stat != 0:
        err_code = err_stat

    err_stat = save_layer(KLO_layer,folder_name+'/KLO')
    if err_stat != 0:
        err_code = err_stat
    """
    err_stat = save_layer(KBO_layer,folder_name+'/KBO')
    if err_stat != 0:
        err_code = err_stat

    err_stat = save_layer(KTO_layer,folder_name+'/KTO')
    if err_stat != 0:
        err_code = err_stat
    """
    if error_code != 0:
        return error_code


    progress.setValue(100)
    iface.messageBar().clearWidgets()

    #otvaram nanovo vrsty - zistil som ze je to tak vyhodnejsie

    #open_layer("KTO",folder_name+'/KTO.shp',"ogr")
    #open_layer("Body",folder_name+'/KBO.shp',"ogr")
    open_layer("KLO",folder_name+'/KLO.shp',"ogr")
    open_layer("Bezlesie",folder_name+'/BZL.shp',"ogr")
    open_layer("Ine plochy",folder_name+'/JP.shp',"ogr")
    open_layer("KPO",folder_name+'/KPO.shp',"ogr")
    open_layer("Lesne porasty",folder_name+'/PSK.shp',"ogr")
    open_layer("Tazobne prvky",folder_name+'/TAZ.shp',"ogr")

    return 0


if __name__ == '__main__':
    convert_to_shp("name")

