#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import qgis
from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui
from PyQt4.QtGui import QProgressBar
from qgis.utils import iface
import os
import sys
import ntpath
import codecs

#------------------------------------------------------------------------
#globalne premenne
#------------------------------------------------------------------------


pt = QgsFeature()#premenna pre jedne geom. objekt

#mozu sa menit, ale treba zachovat poradie
#NEMENIT XXX_NUM, ani pordie, nepridavat nakoniec - radsej do stredu!
#tieto nazvy sa priamo zapisu do suboru ako hlavicky

names_of_pos = ['POSKOZ_D','POSKOZ_R','DRV_NUM']
names_of_zal = ['ZAL_DR','ZAL_DR_P','ETZ_NUM']
names_of_kat = ['KATEGORIE','KAT_SPEC','PSK_NUM']
names_of_drv = ['DR_ZKR','DR_KOD','DR_NAZ','DR_PUVOD',
'ZDR_REP','ZAST','VYSKA','TLOUSTKA',
'BON_R','BON_A','GEN_KLAS','VYB_STR','DR_ZAS_TAB',
'DR_ZAS_HA','DR_ZAS_CEL','DR_CBP','DR_CPP',
'DR_PMP','HMOT','HK','IMISE','DR_KVAL','PROC_SOUS',
'DR_TV','DR_TO','DR_TVYB','ETZ_NUM','DRV_NUM']
names_of_etz = ['ETAZ','ETAZ_PS','ETAZ_PP','HS','OBMYTI', 
'OBN_DOBA','POC_OBNOVY','MZD','VEK','ZAKM','HOSP_TV', 
'M_TEZ_PROC','ODVOZ_TEZ','M_Z_ZASOBY','PRO_P','PRO_NAL', 
'PRO_POC','TV_P','TV_NAL','TV_POC','TO_P','TO_NAL','TO_DUVOD', 
'TO_ZPUSOB ','TVYB_P','TVYB_NAL','ZAL_DRUH','ZAL_P','PSK_NUM','ETZ_NUM'] 
#------------------------------------------------------

#Tieto listy nemenit, to su zoznamy pre parsovanie dat
#menit iba ak sa zmeni standard, na poradi zalezi
#ak sa nenajde dany parameter, nic sa nedeje, ulozi ako prazdny retazec
#nemenit XXX_NUM 

list_of_pos = ['POSKOZ_D','POSKOZ_R']
list_of_zal = ['ZAL_DR','ZAL_DR_P']
list_of_kat = ['KATEGORIE','KAT_SPEC']
list_of_drv = ['DR_ZKR','DR_KOD','DR_NAZ','DR_PUVOD',
'ZDR_REP','ZAST','VYSKA','TLOUSTKA',
'BON_R','BON_A','GEN_KLAS','VYB_STR','DR_ZAS_TAB',
'DR_ZAS_HA','DR_ZAS_CEL','DR_CBP','DR_CPP',
'DR_PMP','HMOT','HK','IMISE','DR_KVAL','PROC_SOUS',
'DR_TV','DR_TO','DR_TVYB']
list_of_etz = ['ETAZ','ETAZ_PS','ETAZ_PP','HS','OBMYTI', 
'OBN_DOBA','POC_OBNOVY','MZD','VEK','ZAKM','HOSP_TV', 
'M_TEZ_PROC','ODVOZ_TEZ','M_Z_ZASOBY','PRO_P','PRO_NAL', 
'PRO_POC','TV_P','TV_NAL','TV_POC','TO_P','TO_NAL','TO_DUVOD', 
'TO_ZPUSOB ','TVYB_P','TVYB_NAL','ZAL_DRUH','ZAL_P'] 
list_of_por = ['POR','SDR_POR','MAJ_KOD','MAJ_NAZ', 
'MAJ_DRUH','ORG_UROVEN','PAS_OHR','LES_OBL', 
'LES_PODOBL','ZVL_STATUT','OLH_LIC','OLH', 
'POR_TEXT','HIST_LHC','HIST_LHPOD','HIST_ROZD']
list_of_psk = ['PSK','PSK_P0','PSK_V','PSK_P', 
'KVAL_P','ORP','KRAJ','KATUZE_KOD','KAT_PAR_KOD','SLT','LT',
'TER_TYP','PRIB_VZD','HOSP_ZP','DAN','PSK_TEXT','CISLO_TEL'] 
list_of_bzl = ['BZL','ORP','KRAJ','KATUZE_KOD','BZL_P0',
'BZL_V','BZL_P','KVAL_P','KAT_PAR_KOD',
'BZL_VYUZ','BZL_DRUH','CISLO_TEL']
list_of_jp = ['JP','JP_PUPFL','ORP','KRAJ','KATUZE_KOD',
'JP_P0','JP_V','JP_P','KVAL_P','KAT_PAR_KOD',
'JP_VYUZ','JP_DRUH','CISLO_TEL'] 
#list_of_kto = [ 'TEXT', 'TXT_STYL', 'TXT_UHEL', 'L_' ]
list_of_kpo = [ 'PLO_DRUH', 'PLO_ZNACKA', 'PLO_BARVA', 'L_']
list_of_klo = [ 'LIN_DRUH', 'LIN_ZNACKA', 'LIN_BARVA', 'L_']
#list_of_kbo = [ 'BOD_DRUH', 'BOD_ZNACKA', 'BOD_UHELZN', 'BOD_BARVA', 'L_']
list_of_lhc = ['LHC_KOD','LHC_NAZ','LHP_OD','LHP_DO','LHP_LIC',
'LHP_TAX','LHP_Z_OD','LHP_Z_DO','LHP_Z_LIC','LHP_Z_TAX',
'KU_DATUM','LHP_NEZDAR','TEZ_PROC','NOR_PAS','ETAT_TO',
'LHC_PN_PRO','ETAT_TV','ETAT_TVYB','LHC_IND','LHC_MAX',
'ETAT','MVYCH_DO40']


#------------------------------------------------------------------------
#funkcie
#------------------------------------------------------------------------

def open_layer(name, address,type_ft):

    new_ft = QgsVectorLayer(address,name,type_ft)
    QgsMapLayerRegistry.instance().addMapLayer(new_ft)
    #layer = iface.addVectorLayer(address, name, type_ft)
    caps  = new_ft.dataProvider().capabilities()
    canvas = qgis.utils.iface.mapCanvas()
    canvas.setExtent(new_ft.extent())

#Vytvori list z <L>, z kazdeho bodu <B> urobi QgsPoint
#vrati list vsetkych bodov v <L> = lines
def create_points(lines):
    points = []
    for point in lines.findall('B'):
        np =  point.get('S')
        number1 = np[:np.find("$")]#odstrihne od zaciatku po $
        number2 = np[np.find("$")+1:]#odstrihne od $ dokonca
        points.append(QgsPoint(float(number1),float(number2)))#vytvorim bod v
        #priestore a ten dam nakoniec zoznamu
    return points#zoznam bodov vratim


#MP = objekt <MP>, layer = vrstva do ktorej chceme pridat objekt,
    #atts = list vsetkych atributov, ktore chceme k danemu objektu priradit
def create_from_MP(MP, layer,atts):
    for polygon in MP.findall('P'):
        for lines in polygon.findall('L'):
            points = create_points(lines)#ziskam zoznam bodov
            pt.setGeometry(QgsGeometry.fromPolygon([points]))#vytvorim geom.
            #objekt
            pt.setAttributes(atts)#nastavim atributy
            layer.addFeatures([pt])
            #Poly_layer.updateExtents()


#obodba pre create_from MP, ale pracuje s ML objektom
def create_from_ML(ML, layer, atts):
    for lines in ML.findall('L'):
        points = create_points(lines)
        pt.setGeometry(QgsGeometry.fromPolyline(points))
        pt.setAttributes(atts)
        layer.addFeatures([pt])
        #Poly_layer.updateExtents()

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

    i = 0
    progressMessageBar =\
    iface.messageBar().createMessage('Konvertujem')
    progress = QProgressBar()
    progress.setMaximum(100)
    progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    progressMessageBar.layout().addWidget(progress)
    iface.messageBar().pushWidget(progressMessageBar,
                        iface.messageBar().INFO)
    


    #praca s CSV - otvorim si vsetky potrebne .csv subory a rovno do nich
        #zapisem aj hlavicku - mohlo by sa to vytiahnut nejako do funckie...
    
    try:
        #iny nazov, podla vstupneho suboru
        etz_file = codecs.open(folder_name+'/etz_file.csv','w',encoding='utf-8')
        etz_file.write(",".join(names_of_etz)+'\n')
    except:
        return 1
   
    
    try:
        #iny nazov, podla vstupneho suboru
        drv_file = codecs.open(folder_name+'/drv_file.csv','w',encoding='utf-8')
        drv_file.write(",".join(names_of_drv)+'\n')
    except:
        return 1


    try:
        #iny nazov, podla vstupneho suboru
        kat_file = codecs.open(folder_name+'/kat_file.csv','w',encoding='utf-8')
        kat_file.write(",".join(names_of_kat)+'\n')
    except:
        return 1


    try:
        #iny nazov, podla vstupneho suboru
        zal_file = codecs.open(folder_name+'/zal_file.csv','w',encoding='utf-8')
        zal_file.write(",".join(names_of_zal)+'\n')
    except:
        return 1


    try:
        #iny nazov, podla vstupneho suboru
        pos_file = codecs.open(folder_name+'/pos_file.csv','w',encoding='utf-8')
        pos_file.write(",".join(names_of_pos)+'\n')
    except:
        return 1
#------------------------------------------------------------------------
#priprava vrstiev
#------------------------------------------------------------------------
#format:
#Multi[Polygon/LineString/Point] - podla typu geometrie ?crs=EPSG:4326 - typ ukladania
#Nazov vrsty, ktory je zobrazny v QGIS
#memory - pracujeme s mamory provider-om
    
    my_crs = QgsCoordinateReferenceSystem()
    my_crs.createFromProj4("+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333\
    +alpha=30.28813975277778 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +units=m\
    +no_defs")
    print my_crs.isValid()

    
    global KPO_layer
    #KPO_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:4326", 'KPO', "memory")
    KPO_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:5514", 'KPO', "memory")
    if not KPO_layer.isValid():
            return 1
    
    
    global JP_layer
    JP_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:5514", 'Ine plochy', "memory")
    if not JP_layer.isValid():
            return 1


    global BZL_layer
    BZL_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:5514", 'Bezlesie', "memory")
    if not BZL_layer.isValid():
            return 1

    global KLO_layer
    KLO_layer = QgsVectorLayer("MultiLineString?crs=EPSG:5514", 'KLO', "memory")
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

    
    i = 5  
    progress.setValue(i)
#priprava vstiev, cast druha
#format jedneho parametra :
    #QgsField(
    #"nazov stlpca v tabulke - moze sa menit lubovolne, ale nie poradie"
    #tieto parametre sa zobrazia v tabulke uzivatelovi
    #typ parametra QVariant.[String/Int/Double] - pomenit tak, aby odpovedalo
    #NEMENIT POSLEDNY PARAMTERE - XXXX-NUMB!
    
    
    #QgsMapLayerRegistry.instance().addMapLayer(PSK_layer)
    global psk_poly
    psk_poly = PSK_layer.dataProvider()
    psk_poly.addAttributes([
                            QgsField("ODD" , QVariant.String),
                            QgsField("DIL" , QVariant.String),

                            QgsField("POR" , QVariant.String),
                            QgsField("SDR_POR" , QVariant.String),
                            QgsField("MAJ_KOD" , QVariant.String),
                            QgsField("MAJ_NAZ" , QVariant.String),
                            QgsField("MAJ_DRUH" , QVariant.String),
                            QgsField("ORG_UROVEN" , QVariant.String),
                            QgsField("PAS_OHR" , QVariant.String),
                            QgsField("LES_OBL" , QVariant.String),
                            QgsField("LES_PODOBL" , QVariant.String),
                            QgsField("ZVL_STATUT" , QVariant.String),
                            QgsField("OLH_LIC" , QVariant.String),
                            QgsField("OLH" , QVariant.String),
                            QgsField("POR_TEXT" , QVariant.String),
                            QgsField("HIST_LHC" , QVariant.String),
                            QgsField("HIST_LHPOD" , QVariant.String),
                            QgsField("HIST_ROZD" , QVariant.String),

                            QgsField("PSK" , QVariant.String),
                            QgsField("PSK_P0" , QVariant.Double),
                            QgsField("PSK_V" , QVariant.Double),
                            QgsField("PSK_P" , QVariant.Double),
                            QgsField("KVAL_P" , QVariant.Int),
                            QgsField("ORP" , QVariant.Int),
                            QgsField("KRAJ" , QVariant.String),
                            QgsField("KATUZE_KOD" , QVariant.Int),
                            QgsField("KAT_PAR_KOD" , QVariant.Int),
                            QgsField("SLT" , QVariant.String),
                            QgsField("LT" , QVariant.String),
                            QgsField("TER_TYP" , QVariant.Int),
                            QgsField("PRIB_VZD" , QVariant.Int),
                            QgsField("HOSP_ZP" , QVariant.Int),
                            QgsField("DAN" , QVariant.String),
                            QgsField("PSK_TEXT" , QVariant.String),
                            QgsField("CISLO_TEL" , QVariant.Int),

                            QgsField("PSK_NUM" , QVariant.Int),
                            QgsField("COLOR" , QVariant.String),
                            QgsField("max_len" , QVariant.Double),
                            QgsField("max_area" , QVariant.Double),
                            

                            ])
    PSK_layer.updateFields()


    #QgsMapLayerRegistry.instance().addMapLayer(KPO_layer)
    global kpo_poly
    kpo_poly = KPO_layer.dataProvider()
    kpo_poly.addAttributes([
                            QgsField("PLO_DRUH" , QVariant.Int),
                            QgsField("PLO_ZNACKA" , QVariant.Int),
                            QgsField("PLO_BARVA" , QVariant.Int),
                            QgsField("L_" , QVariant.String)
                            ])
    KPO_layer.updateFields()


    #QgsMapLayerRegistry.instance().addMapLayer(JP_layer)
    global jp_poly
    jp_poly = JP_layer.dataProvider()
    jp_poly.addAttributes([
                            QgsField("ODD" , QVariant.String),
                            QgsField("DIL" , QVariant.String),

                            QgsField("POR" , QVariant.String),
                            QgsField("SDR_POR" , QVariant.String),
                            QgsField("MAJ_KOD" , QVariant.String),
                            QgsField("MAJ_NAZ" , QVariant.String),
                            QgsField("MAJ_DRUH" , QVariant.String),
                            QgsField("ORG_UROVEN" , QVariant.String),
                            QgsField("PAS_OHR" , QVariant.String),
                            QgsField("LES_OBL" , QVariant.String),
                            QgsField("LES_PODOBL" , QVariant.String),
                            QgsField("ZVL_STATUT" , QVariant.String),
                            QgsField("OLH_LIC" , QVariant.String),
                            QgsField("OLH" , QVariant.String),
                            QgsField("POR_TEXT" , QVariant.String),
                            QgsField("HIST_LHC" , QVariant.String),
                            QgsField("HIST_LHPOD" , QVariant.String),
                            QgsField("HIST_ROZD" , QVariant.String),

                            QgsField("JP" , QVariant.Int),
                            QgsField("JP_PUPFL" , QVariant.String),
                            QgsField("ORP" , QVariant.Int),
                            QgsField("KRAJ" , QVariant.String),
                            QgsField("KATUZE_KOD" , QVariant.Int),
                            QgsField("JP_PO" , QVariant.Double),
                            QgsField("JP_V" , QVariant.Double),
                            QgsField("JP_P" , QVariant.Double),
                            QgsField("KVAL_P" , QVariant.Int),
                            QgsField("KAT_PAR_KOD" , QVariant.Int),
                            QgsField("JP_VYUZ" , QVariant.String),
                            QgsField("JP_DRUH" , QVariant.String),
                            QgsField("CISLO_TEL" , QVariant.Int),
                            ])
    JP_layer.updateFields()


    #QgsMapLayerRegistry.instance().addMapLayer(BZL_layer)
    global bzl_poly
    bzl_poly = BZL_layer.dataProvider()
    bzl_poly.addAttributes([
                            QgsField("ODD" , QVariant.String),
                            QgsField("DIL" , QVariant.String),

                            QgsField("POR" , QVariant.String),
                            QgsField("SDR_POR" , QVariant.String),
                            QgsField("MAJ_KOD" , QVariant.String),
                            QgsField("MAJ_NAZ" , QVariant.String),
                            QgsField("MAJ_DRUH" , QVariant.String),
                            QgsField("ORG_UROVEN" , QVariant.String),
                            QgsField("PAS_OHR" , QVariant.String),
                            QgsField("LES_OBL" , QVariant.String),
                            QgsField("LES_PODOBL" , QVariant.String),
                            QgsField("ZVL_STATUT" , QVariant.String),
                            QgsField("OLH_LIC" , QVariant.String),
                            QgsField("OLH" , QVariant.String),
                            QgsField("POR_TEXT" , QVariant.String),
                            QgsField("HIST_LHC" , QVariant.String),
                            QgsField("HIST_LHPOD" , QVariant.String),
                            QgsField("HIST_ROZD" , QVariant.String),

                            QgsField("BZL" , QVariant.Int),
                            QgsField("ORP" , QVariant.Int),
                            QgsField("KRAJ" , QVariant.String),
                            QgsField("KATUZE_KOD" , QVariant.Int),
                            QgsField("BZL_PO" , QVariant.Double),
                            QgsField("BZL_V" , QVariant.Double),
                            QgsField("BZL_P" , QVariant.Double),
                            QgsField("KVAL_P" , QVariant.Int),
                            QgsField("KAT_PAR_KOD" , QVariant.Int),
                            QgsField("BZL_VYUZ" , QVariant.String),
                            QgsField("BZL_DRUH" , QVariant.String),
                            QgsField("CISLO_TEL" , QVariant.Int),
                            ])
    BZL_layer.updateFields()


    #QgsMapLayerRegistry.instance().addMapLayer(KLO_layer)
    global klo_line
    klo_line = KLO_layer.dataProvider()
    klo_line.addAttributes([
                            QgsField("LIN_DRUH" , QVariant.Int),
                            QgsField("LIN_ZNACKA" , QVariant.Int),
                            QgsField("LIN_BARVA" , QVariant.Int),
                            QgsField("L_" , QVariant.String),
                            ])
    KLO_layer.updateFields()


    #QgsMapLayerRegistry.instance().addMapLayer(KBO_layer)
    """
    global kbo_line
    kbo_line = KBO_layer.dataProvider()
    kbo_line.addAttributes([
                            QgsField("BOD_DRUH" , QVariant.Int),
                            QgsField("BOD_ZNACKA" , QVariant.Int),
                            QgsField("BOD_UHELZN" , QVariant.Double),
                            QgsField("BOD_BARVA" , QVariant.Int),
                            QgsField("L_" , QVariant.String),
                            ])
    KBO_layer.updateFields()


    #QgsMapLayerRegistry.instance().addMapLayer(KTO_layer)
    global kto_line
    kto_line = KTO_layer.dataProvider()
    kto_line.addAttributes([
                            QgsField("text" , QVariant.String),
                            QgsField("TXT_STYL", QVariant.Int),
                            QgsField("TXT_UHEL", QVariant.Double),
                            QgsField("L_",QVariant.String)
                            ])
    KTO_layer.updateFields()
    """
    
    i = 7  
    progress.setValue(i)
#------------------------------------------------------------------------
#parser xml + samotne ukladanie
#------------------------------------------------------------------------

    tree = ET.parse(pretty_name)
    if not tree:
        return 2
    root = tree.getroot()

    PSK_ID = 0#pocitadla etazi, porastov...
    ETZ_ID = 0
    DRV_ID = 0

    
    for child in root:
        #save_LHC(child.attrib)!
        #for HS,OU1,OU2,MZD!
        
                
                
        i = 15  
        progress.setValue(i)
        """
        for KBO in child.findall('KBO'):
            atts = create_attributes(KBO, list_of_kbo)
            if not KBO.findall('BOD_OBRAZ'):
                return 3
            for BOD_obraz in KBO.findall('BOD_OBRAZ'):

                for MB in BOD_obraz.findall('MB'):
                    for point in MB.findall('B'):
                        np =  point.get('S')
                        number1 = np[:np.find("$")]
                        number2 = np[np.find("$")+1:]
                        pt.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(number1),float(number2))))
                        pt.setAttributes(atts)
                        kbo_line.addFeatures([pt])

        i = 22  
        progress.setValue(i)

        for KTO in child.findall('KTO'):
            atts = create_attributes(KTO,list_of_kto)
            if not KTO.findall('TXT_OBRAZ'):
                return 3
            for TXT_obraz in KTO.findall('TXT_OBRAZ'):
                for B in TXT_obraz.findall('B'):
                    np= B.get('S')
                    number1 = np[:np.find("$")]
                    number2 = np[np.find("$")+1:]
                    pt.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(number1),float(number2))))
                    pt.setAttributes(atts)
                    kto_line.addFeatures([pt])

        i = 29  
        progress.setValue(i)

        """
        for KPO in child.findall('KPO'):
            if not KPO.findall('PLO_OBRAZ'):
                return 3
            atts = create_attributes(KPO, list_of_kpo)
            for KPO_obraz in KPO.findall('PLO_OBRAZ'):
                for MP in KPO_obraz.findall('MP'):
                    create_from_MP(MP,kpo_poly,atts)


        i = 19  
        progress.setValue(i)
        for KLO in child.findall('KLO'):
            atts = create_attributes(KLO, list_of_klo)
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
                    por_atts = create_attributes(porast,list_of_por)
                    for bezlesie in porast.findall('BZL'):
                        if not bezlesie.findall('BZL_OBRAZ'):
                            return 3
                        bzl_atts = create_attributes(bezlesie, list_of_bzl)
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
                                create_from_MP(MP,bzl_poly,atts)

                    for jine in porast.findall('JP'):
                        jp_atts = create_attributes(jine, list_of_jp)
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
                                create_from_MP(MP,jp_poly,atts)

                    #na porastoch dat join
                    for psk in porast.findall('PSK'):
                        my_id = PSK_ID
                        PSK_ID += 1

                        psk_atts = create_attributes(psk, list_of_psk)
                        if not psk.findall('PSK_OBRAZ'):
                            return 3
                        
#from this
                        atts = [odd_att]
                        atts.append(dil_att)
                        for item in por_atts:
                            atts.append(item)
                        for item in psk_atts:
                            atts.append(item)
#to this

                        for psk_obraz in psk.findall('PSK_OBRAZ'):
                            for MP in psk_obraz.findall('MP'):
                                atts.append(my_id)
                                
                                create_from_MP(MP,psk_poly,atts)

                        for etaz in psk.findall('ETZ'):
                            etz_id = ETZ_ID
                            ETZ_ID += 1
                            etz_atts = create_attributes(etaz,list_of_etz)
                            etz_atts.append(str(my_id))
                            etz_atts.append(str(etz_id))
                            
                            to_write = "\",\"".join(etz_atts)
                            etz_file.write("\""+to_write+'\"\n')
                            for drevina in etaz.findall('DRV'):
                                my_drv_id = DRV_ID
                                DRV_ID += 1
                                drv_atts = create_attributes(drevina,list_of_drv)
                                drv_atts.append(str(etz_id))
                                drv_atts.append(str(my_drv_id))

                                to_write = "\",\"".join(drv_atts)
                                drv_file.write("\""+to_write+'\"\n')

                                
                                for poskodenie in drevina.findall('POS'):
                                    pos_atts = create_attributes(poskodenie,
                                            list_of_pos)
                                    pos_atts.append(str(my_drv_id))
                                    to_write = "\",\"".join(pos_atts)
                                    pos_file.write("\""+to_write+'\"\n')
                                    if i < 95:
                                        i += 1
                                    progress.setValue(i)


                            
                            
                            for zalozenie in etaz.findall('ZAL'):
                                zal_atts = create_attributes(zalozenie,list_of_zal)
                                zal_atts.append(str(etz_id))

                                to_write = "\",\"".join(zal_atts)
                                zal_file.write("\""+to_write+'\"\n')
                            
                    for kategoria in porast.findall('KAT'):
                        kat_atts = create_attributes(kategoria,list_of_kat)
                        kat_atts.append(str(my_id))
                        to_write = "\",\"".join(kat_atts)
                        kat_file.write("\""+to_write+'\"\n')

    
    PSK_layer.updateExtents()
    canvas = qgis.utils.iface.mapCanvas()
    canvas.setExtent(PSK_layer.extent())
    qgis.utils.iface.mapCanvas().refresh()



    etz_file.close()
    drv_file.close()
    kat_file.close()
    pos_file.close()
    zal_file.close()
    
    #otvorim csv subory pre potreby QGIS    
    etz_csv = QgsVectorLayer("file:///"+folder_name+'/etz_file.csv',"Porast","delimitedtext")
    save_layer(etz_csv,folder_name+'/etz')
    new_etz = QgsVectorLayer(folder_name+'/etz.dbf',"Porast","ogr")
    QgsMapLayerRegistry.instance().addMapLayer(new_etz)


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

    #open_layer("KTO",folder_name+'/KTO.shp',"ogr")
    #open_layer("Body",folder_name+'/KBO.shp',"ogr")
    open_layer("KLO",folder_name+'/KLO.shp',"ogr")
    open_layer("Bezlesie",folder_name+'/BZL.shp',"ogr")
    open_layer("Ine plochy",folder_name+'/JP.shp',"ogr")
    open_layer("KPO",folder_name+'/KPO.shp',"ogr")
    open_layer("Lesne porasty",folder_name+'/PSK.shp',"ogr")

    
    return 0


if __name__ == '__main__':
    convert_to_shp("name")

