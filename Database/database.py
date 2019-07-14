# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Database
                                 A QGIS plugin
 Does something
                              -------------------
        begin                : 2015-08-04
        git sha              : $Format:%H$
        copyright            : (C) 2015 by M. Marusak
        email                : marusak.matej@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
#pyrcc4 -o resources_rc.py resources.qrc

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication,\
    Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox, QTableWidgetItem, QProgressBar
from PyQt5 import QtGui, QtCore
from qgis.utils import iface
import qgis
#from qgis.core import QgsFeatureRequest
from . import resources_rc
from . database_dialog import DatabaseDialog
from . show_atts import ShowAtts
from . save import Save_all 
from . add_drv import Add_drv 
from . add_etz import Add_etz 
from . sekvencie import Sekvencie 
from . distance import Distance 
from . set_ranges import Set_ranges 
from . open_all import Open_all 
from . out_xml import OutXml
from . create_processes import CreateProcesses
import os.path
from . converter import convert_to_shp
import sys 
from . import dtutils
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
import codecs
import time

from qgis.core import *
from . names import NAMES_TAZ_TYP

pretty_name = ""#nazov pre vstupny subor
pretty_folder = ""#nazov priecinku pre ukladanie
input_folder = ""#nazov pre vstupny priecinok
edit_pos = 0#povoluje editovanie - aby si nemyslelo ze editujem, ked len
    #nastavujem hodnoty do tabulky
list_of_kats_ids = []#globalne uloziska pre id  prave vypisanych hodnot
list_of_etzs_ids = []#sluzi na rychjesiu editaciu parametrov
list_of_vys_vych_ids = []
list_of_vys_obn_ids = []
list_of_drvs_ids = []
list_of_zals_ids = []
list_of_poss_ids = []
maximum_length = 50 #predvolena hodnota maximalnej sirky
maximum_area = 10000#predvolena hodnota maximalnej plochy
minimum_length = 0 #predvolena hodnota minimalnej sirky
minimum_area = 0#predvolena hodnota minimalnej plochy


class Database:

    #tu sa reaguje sa signaly
    #popisane je to na ShowAtts - zvysok je obdoba
    def __init__(self, iface):
        
        self.num_of_sek = 1
        self.num_of_item = 0
        self.edit_sek = 0

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Database_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = DatabaseDialog()
        
        #----------------------------------
        self.shower = ShowAtts()#toto sa importuje
        
        table = self.shower.drevina

        p = QtGui.QPalette(table.palette())
        #p.setBrush(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText,
                #QtGui.QBrush(QColor("red")))
        #p.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.HighlightedText,
                #QtGui.QBrush(QColor("red")))
        p.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,
                QtGui.QBrush(QColor(255,0,0,127)))
        p.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Highlight,
                QtGui.QBrush(QColor("0,0,255,127")))
        table.setPalette(p)


        #self.shower.refresh.clicked.connect(self.edit_main)#ked kliknem na
            #refrsh zavola sa edit_main
        self.shower.tableWidget.itemChanged.connect(self.edit_main)#ak pride
        #signal itemChanged zavola sa funkcia edit_main
        self.shower.kategoria.itemChanged.connect(self.edit_kats)
        self.shower.etaz.itemChanged.connect(self.edit_etzs)
        self.shower.zalozene.itemChanged.connect(self.edit_zals)
        self.shower.pos.itemChanged.connect(self.edit_poss)
        self.shower.drevina.itemChanged.connect(self.edit_drvs)

        self.save_all = Save_all()
        self.add_drv = Add_drv()
        self.add_etz = Add_etz()
        self.sekvencie = Sekvencie()
        self.distance = Distance()

        self.out_xml = OutXml()
        self.out_xml.address.clear()
        self.out_xml.lookup.clicked.connect(self.select_output_folder)
        self.out_xml.save.clicked.connect(self.export_xml)

        self.create_processes = CreateProcesses()
        self.create_processes.pridat.clicked.connect(self.add_new_process)
        self.create_processes.etaz.currentIndexChanged.connect(self.update_drv_in_processes)
        self.create_processes.holosec.toggled.connect(self.toggle_holosec)
        self.create_processes.definovane.itemSelectionChanged.connect(self.toggle_definovane_zasahy)
        self.create_processes.sec_id.currentIndexChanged.connect(self.toggle_sec)
        self.create_processes.typ_id.currentIndexChanged.connect(self.toggle_typ)
        self.create_processes.remove.clicked.connect(self.remove_zasahy)
        self.create_processes.new_id.clicked.connect(self.new_typ_id)
        self.create_processes.new_sec.clicked.connect(self.new_sec_id)

        self.sekvencie.finish.clicked.connect(self.end_sek)
        self.sekvencie.new_s.clicked.connect(self.new_sek)

        self.distance.finish.clicked.connect(self.set_distance_to_nei)

        self.save_all.address.clear()
        self.save_all.lookup.clicked.connect(self.select_output_folder)
        self.save_all.save.clicked.connect(self.save_all_1)

        self.add_etz.add_button.clicked.connect(self.save_new_etz)
        self.shower.add_etz.clicked.connect(self.add_etz_f)


        self.add_drv.add_button.clicked.connect(self.save_new_drv)
        self.shower.add_drv.clicked.connect(self.add_drv_f)

        self.set_ranges = Set_ranges()
        self.set_ranges.min_area.setText("0.0")
        self.set_ranges.min_len.setText("0.0")
        self.set_ranges.set_all.clicked.connect(self.set_ranges_f)

        self.shower.priorita.editingFinished.connect(self.edit_priorita)
        self.shower.area_max.editingFinished.connect(self.edit_area_max)
        self.shower.area_min.editingFinished.connect(self.edit_area_min)
        self.shower.length_max.editingFinished.connect(self.edit_length_max)
        self.shower.length_min.editingFinished.connect(self.edit_length_min)


        self.open_all = Open_all()
        self.open_all.address.clear()
        self.open_all.lookup.clicked.connect(self.select_input_folder)
        self.open_all.open.clicked.connect(self.open_all_1)
        
        self.shower.etaz.itemSelectionChanged.connect(self.highlight_drv)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Optimal')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Database')
        self.toolbar.setObjectName(u'Database')

        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_input_file)
        self.dlg.lineEdit_2.clear()
        self.dlg.pushButton_2.clicked.connect(self.select_output_folder_c)

        iface.mapCanvas().selectionChanged.connect(self.show_atts)        


        

        
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Database', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

   

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        #tu vzdy pridat cely tento kus
        #zmenit cestu k ikonke a zmenit popis
        #zmenit aj volanu funkciu
        icon_path = ':/plugins/Database/icons/icon_convert.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Convert format'),
            callback=self.run,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/Database/icons/colorize.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Color polygons'),
            #callback=self.show_atts,
            callback=self.open_ranges,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/Database/icons/create_processes.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create processes'),
            callback=self.open_processes,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/Database/icons/icon_save.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Save All'),
            callback=self.save_all_11,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/Database/icons/icon_open.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Open All'),
            callback=self.open_all_11,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/Database/icons/icon_cut.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Cut polygon'),
            callback=self.cut_polygon,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/Database/icons/icon_sek.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Sekvenice'),
            callback=self.sekvence,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/Database/icons/icon_set_nei.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Set distance to neighbours'),
            callback=self.set_nei,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/Database/icons/icon_nei.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Select neighbours'),
            callback=self.nei,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/Database/icons/icon_xml.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Export XML'),
            callback=self.show_xml,
            parent=self.iface.mainWindow())
        
        self.handler = None
        self.selected_layer = None

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Optimal'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def prettify(self, string):
        return minidom.parseString(string).toprettyxml(indent="  ")

    def add_list_to_dict(self, dict_, key, value):
        if key not in dict_.keys():
            dict_[key] = [value]
        else:
            dict_[key].append(value)

    def fillup_attributes_dict(self, names, ids, attributes):
        dict_ = {}
        for name, id_ in zip(names, ids):
            if isinstance(attributes[id_], (int, long, float)):
                dict_[name] = str(attributes[id_])
            elif isinstance(attributes[id_], (float)):
                dict_[name] = repr(attributes[id_])
            else:
                dict_[name] = attributes[id_]
        return dict_

    def process_etz(self, root, etzs_list):
        for etz in etzs_list:
            dict_ = self.fillup_attributes_dict(self.ETZ_items, self.ETZ_ids,
                                                etz.attributes())
            etz_root = ET.SubElement(root, "ETZ", dict_)
            if etz.attributes()[self.id_ETZ] in self.drvs.keys():
                for drv in self.drvs[etz.attributes()[self.id_ETZ]]:
                    dict_ = self.fillup_attributes_dict(self.DRV_items, self.DRV_ids,
                                                        drv.attributes())
                    drv_root = ET.SubElement(etz_root, "DRV", dict_)
                    if drv[self.id_DRV] in self.poss.keys():
                        for pos in self.poss[drv.attributes()[self.id_DRV]]:
                            dict_ = self.fillup_attributes_dict(self.POS_items, self.POS_ids,
                                                                pos.attributes())
                            ET.SubElement(drv_root, "POS", dict_)

            if etz.attributes()[self.id_ETZ] in self.zals.keys():
                for zal in self.zals[etz.attributes()[self.id_ETZ]]:
                    dict_ = self.fillup_attributes_dict(self.ZAL_items, self.ZAL_ids,
                                                        zal.attributes())
                    ET.SubElement(etz_root, "ZAL", dict_)

    def generate_globals(self):
        lyr = None
        csv_kat = None
        csv_por = None
        csv_drv = None
        csv_zal = None
        csv_pos = None

        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Lesne porasty":
                lyr = layer
            elif layer.name() == "Kategorie":
                csv_kat = layer
            elif layer.name() == "Porast":
                csv_por = layer
            elif layer.name() == "Dreviny":
                csv_drv = layer
            elif layer.name() == "Zalozenie":
                csv_zal = layer
            elif layer.name() == "Poskodenia":
                csv_pos = layer

        self.POR_items = ['SDR_POR', 'MAJ_KOD', 'MAJ_NAZ', 'MAJ_DRUH', 'ORG_UROVEN',
                     'PAS_OHR', 'LES_OBL', 'LES_PODOBL', 'ZVL_STATUT', 'POR',
                     'OLH_LIC', 'OLH', 'POR_TEXT', 'HIST_LHC', 'HIST_LHPOD',
                     'HIST_ROZD']
        self.KAT_items = ['KATEGORIE', 'KAT_SPEC']
        self.PSK_items = ['PSK', 'PSK_P0', 'PSK_V', 'PSK_P', 'KVAL_P', 'KRAJ',
                     'KATUZE_KOD', 'KAT_PAR_KOD', 'SLT', 'LT', 'TER_TYP',
                     'PRIB_VZD', 'HOSP_ZP', 'DAN', 'PSK_TEXT', 'CISLO_TEL',
                     'ORP']
        self.ETZ_items = [
            'ETAZ', 'ETAZ_PS', 'ETAZ_PP', 'HS', 'OBMYTI', 'OBN_DOBA',
            'POC_OBNOVY', 'MZD', 'VEK', 'ZAKM', 'HOSP_TV', 'M_TEZ_PROC',
            'ODVOZ_TEZ', 'M_Z_ZASOBY', 'PRO_P', 'PRO_NAL', 'PRO_POC',
            'TV_P', 'TV_NAL', 'TV_POC', 'TO_P', 'TO_NAL', 'TO_DUVOD',
            'TO_ZPUSOB', 'TVYB_P', 'TVYB_NAL', 'ZAL_DRUH', 'ZAL_P'
                ]
        self.DRV_items = [
             'DR_ZKR', 'DR_KOD', 'DR_NAZ', 'DR_PUVOD', 'ZDR_REP', 'ZAST', 'VYSKA',
             'TLOUSTKA', 'BON_R', 'BON_A', 'GEN_KLAS', 'VYB_STR', 'DR_ZAS_TAB',
             'DR_ZAS_HA', 'DR_ZAS_CEL', 'DR_CBP', 'DR_CPP', 'DR_PMP',
             'HMOT', 'HK', 'IMISE', 'DR_KVAL', 'PROC_SOUS', 'DR_TV',
             'DR_TO', 'DR_TVYB']
        self.ZAL_items = ['ZAL_DR', 'ZAL_DR_P']
        self.POS_items = ['POSKOZ_D', 'POSKOZ_R']

        self.zals = {}
        self.ZAL_ids = []
        if csv_zal:
            self.ZAL_ids = [csv_zal.fieldNameIndex(x[:10]) for x in self.ZAL_items]
            self.ETZ_NUM_zal = csv_zal.fieldNameIndex('ETZ_NUM')
            zals = self.zals
            for ft in csv_zal.getFeatures():
                if ft.attributes()[self.ETZ_NUM_zal] in zals.keys():
                    zals[ft.attributes()[self.ETZ_NUM_zal]].append(ft)
                else:
                    zals[ft.attributes()[self.ETZ_NUM_zal]] = [ft]

        self.poss = {}
        self.POS_ids = []
        if csv_pos:
            self.POS_ids = [csv_pos.fieldNameIndex(x[:10]) for x in self.POS_items]
            self.DRV_NUM_pos = csv_pos.fieldNameIndex('DRV_NUM')
            poss = self.poss
            for ft in csv_pos.getFeatures():
                if ft.attributes()[self.DRV_NUM_pos] in poss.keys():
                    poss[ft.attributes()[self.DRV_NUM_pos]].append(ft)
                else:
                    poss[ft.attributes()[self.DRV_NUM_pos]] = [ft]

        self.drvs = {}
        self.DRV_ids = []
        if csv_drv:
            self.DRV_ids = [csv_drv.fieldNameIndex(x[:10]) for x in self.DRV_items]
            self.id_DRV = csv_drv.fieldNameIndex('DRV_NUM')
            self.ETZ_NUM_drv = csv_drv.fieldNameIndex('ETZ_NUM')
            drvs = self.drvs
            for ft in csv_drv.getFeatures():
                if ft.attributes()[self.ETZ_NUM_drv] in drvs.keys():
                    drvs[ft.attributes()[self.ETZ_NUM_drv]].append(ft)
                else:
                    drvs[ft.attributes()[self.ETZ_NUM_drv]] = [ft]

        self.etzs = {}
        self.ETZ_ids = []
        if csv_por:
            self.ETZ_ids = [csv_por.fieldNameIndex(x[:10]) for x in self.ETZ_items]
            self.id_ETZ = csv_por.fieldNameIndex('ETZ_NUM')
            self.PSK_NUM_por = csv_por.fieldNameIndex('PSK_NUM')
            etzs = self.etzs
            for ft in csv_por.getFeatures():
                if ft.attributes()[self.PSK_NUM_por] in etzs.keys():
                    etzs[ft.attributes()[self.PSK_NUM_por]].append(ft)
                else:
                    etzs[ft.attributes()[self.PSK_NUM_por]] = [ft]

        self.kats = {}
        self.KAT_ids = []
        if csv_kat:
            self.KAT_ids = [csv_kat.fieldNameIndex(x[:10]) for x in self.KAT_items]
            self.PSK_id_kat = csv_kat.fieldNameIndex('PSK_NUM')
            kats = self.kats
            for ft in csv_kat.getFeatures():
                if ft.attributes()[self.PSK_id_kat] in kats.keys():
                    kats[ft.attributes()[self.PSK_id_kat]].append(ft)
                else:
                    kats[ft.attributes()[self.PSK_id_kat]] = [ft]

        if lyr:
            self.PSK_ids = [lyr.fieldNameIndex(x[:10]) for x in self.PSK_items]
            self.POR_ids = [lyr.fieldNameIndex(x[:10]) for x in self.POR_items]
            self.id_ODD = lyr.fieldNameIndex('ODD')
            self.id_DIL = lyr.fieldNameIndex('DIL')
            self.id_POR = lyr.fieldNameIndex('POR')
            self.id_PSK = lyr.fieldNameIndex('PSK_NUM')
            self.sekvence_id = lyr.fieldNameIndex('sekvencia')
            self.priorita_id = lyr.fieldNameIndex('priorita')
            self.nei_id = lyr.fieldNameIndex('neighbours')
            self.id_original = lyr.fieldNameIndex('original')

    def process_psk(self, lyr, root, fts_list):
        parents = []
        children = []
        #TODO chidren into dict by parent, or maybe just go throug them and find
        # appropriate, if is_original is -1 then add implicit children
        for ft in fts_list:
            if ft.attributes()[self.id_original] == -1:
                parents.append(ft)
                children.append(ft)
            elif ft.attributes()[self.id_original] == -2:
                parents.append(ft)
            else:
                children.append(ft)
        for ft in parents:
            dict_ = self.fillup_attributes_dict(self.PSK_items, self.PSK_ids,
                                                ft.attributes())
            dict_['PSK_ID'] = str(ft.id())
            psk = ET.SubElement(root, "PSK", dict_)
            psk_obraz = ET.SubElement(psk, "PSK_OBRAZ")
            p = ET.SubElement(psk_obraz, "MP")
            ml = ET.SubElement(p, "P")
            for ring in ft.geometry().asPolygon():
                l = ET.SubElement(ml, "L")
                for point in ring:
                    ET.SubElement(l, "B", S="{0}${1}".format(-1 * point[1], -1 * point[0]))

            self.process_etz(psk, self.etzs[ft.attributes()[self.id_PSK]])
            if ft.attributes()[self.id_original] == -2:
                # polygon was split, there must be some children
                for child_ft in children:
                    if child_ft.attributes()[self.id_original] == ft.id():
                        self.process_tazebni_prvek(root, child_ft, ft.id())
            elif ft.attributes()[self.id_original] == -1:
                # polygon was not split, it is its own Tazebni_prvek
                self.process_tazebni_prvek(root, ft, ft.id())

    def process_tazebni_prvek(self, root, ft, parent_psk_id):
        self.finished += 1
        self.progress.setValue(self.finished)
        _dict = {}
        _dict['ID'] = str(ft.id())
        # parent_psk_id == attributes()[is_original] !! test just for fun
        _dict['ID_PSK'] = str(parent_psk_id)
        _dict['TP_vymera'] = repr(ft.geometry().area())
        _dict['Sekvence'] = ft.attributes()[self.sekvence_id]
        #_dict['Poradi_sekvence'] = ft.attributes()[self.poradi_id]
        _dict['Nalehavost'] = str(ft.attributes()[self.priorita_id])
        taz_prv = ET.SubElement(root, "TazebniPrvek", _dict)
        neighs = ft.attributes()[self.nei_id].split(';')
        for nei in neighs:
            ET.SubElement(taz_prv, "Soused", ID=nei)


        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Tazobne typy":
                taz_typ_csv = layer

        id_typ = taz_typ_csv.fieldNameIndex('TYP')
        id_prirazeni = taz_typ_csv.fieldNameIndex('PRIRAZENI')
        id_odstup = taz_typ_csv.fieldNameIndex('ODSTUP')
        id_drevina = taz_typ_csv.fieldNameIndex('DR')
        id_intenzita = taz_typ_csv.fieldNameIndex('INTENZITA')
        expr = QgsExpression("PSK_NUM ="+ str(ft.id()))
        suitable_taz_typ = taz_typ_csv.getFeatures(QgsFeatureRequest(expr))

        taz_typ_groups = {}
        for taz_typ in suitable_taz_typ:
            taz_typ_id = taz_typ.attributes()[-2]
            if taz_typ_id in taz_typ_groups.keys():
                taz_typ_groups[taz_typ_id].append(taz_typ)
            else:
                taz_typ_groups[taz_typ_id] = [taz_typ]

        for taz_typ_id in taz_typ_groups.keys():
            _dict = {'ID': str(taz_typ_id)}
            _dict['TYP'] = str(taz_typ_groups[taz_typ_id][0].attributes()[id_typ])
            _dict['PRIRAZENI'] = str(taz_typ_groups[taz_typ_id][0].attributes()[id_prirazeni])
            taz_typ = ET.SubElement(taz_prv, "TAZ_TYP", _dict)
            sec_groups = {}
            for sec in taz_typ_groups[taz_typ_id]:
                odstup = sec.attributes()[id_odstup]
                if odstup in sec_groups.keys():
                    sec_groups[odstup].append(sec)
                else:
                    sec_groups[odstup] = [sec]
            for sec in sec_groups.keys():
                sec_element = ET.SubElement(taz_typ, "SEC", ODSTUP=str(sec))
                for zasah in sec_groups[sec]:
                    _dict = {'DR': str(zasah.attributes()[id_drevina])}
                    _dict['INTENZITA'] = str(zasah.attributes()[id_intenzita])
                    ET.SubElement(sec_element, "ZASAH", _dict)

        self.process_etz(taz_prv, self.etzs[ft.attributes()[self.id_PSK]])

    def show_xml(self):
        self.out_xml.show()


    def get_int(self, value, name):
        if value.isdigit():
            return value
        else:
            text = "{0} musi byt cislo".format(name)
            QMessageBox.information(self.iface.mainWindow(),"Chyba",text)
            raise


    def parse_project_settings(self):
        vals = {}
        vals['planHor'] = self.get_int(self.out_xml.planHor.text(), 'Delka planovaciho horizontu')
        vals['pocetPer'] = self.get_int(self.out_xml.pocetPer.text(), 'Pocet period')
        vals['typPodmPlyn'] = str(self.out_xml.typPodmPlyn.currentText())
        vals['urokMira'] = self.get_int(self.out_xml.urokMira.text(), 'Urokova Mira')
        vals['procePlyn'] = self.get_int(self.out_xml.procePlyn.text(), 'Procento Plynulosti')
        if self.out_xml.globalni.isChecked():
            vals['typOptVych'] = "global"
        else:
            vals['typOptVych'] = "individual"

        cile = {'tezba': [self.out_xml.tezba, self.out_xml.tezbaval],
                'zasoba': [self.out_xml.zasoba, self.out_xml.zasobaval],
                'sdi': [self.out_xml.sdi, self.out_xml.sdival],
                'rekreace': [self.out_xml.rekreace, self.out_xml.rekreaceval],
                'biodiverzita': [self.out_xml.biodiverzita, self.out_xml.biodiverzitaval]}

        for ciel in cile.keys():
            if cile[ciel][0].isChecked():
                vals[ciel + "Vyber"] = "1"
                vals[ciel + "Vaha"] = self.get_int(cile[ciel][1].text(), ciel)
            else:
                vals[ciel + "Vyber"] = "0"
                vals[ciel + "Vaha"] = "0"

        return vals

    def export_xml(self):
        try:
            params = self.parse_project_settings()
        except:
            return
        root = ET.Element("Projekt", params)
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Lesne porasty":
                lyr = layer
        iface.messageBar().clearWidgets() 
        self.finished = 0#percento dokoncenia pre progressBar
        prg = iface.messageBar().createMessage('Exportujem')#pridam text konvertujem
        progress = QProgressBar()#vytvorim progressBar
        progress.setMaximum(lyr.featureCount())#maximum je pocet polygonov
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)#zarovnam ho vlavo
        prg.layout().addWidget(progress)#a pridam ho do hroenj listy
        iface.messageBar().pushWidget(prg,
                            iface.messageBar().INFO)

        self.generate_globals()
        progress.setValue(self.finished)
        self.progress = progress

        ODDs = {}
        lhc = ET.SubElement(root, "LHC", LHC_KOD="missing_data....")
        for ft in lyr.getFeatures():
            self.add_list_to_dict(ODDs, ft.attributes()[self.id_ODD], ft)
        for ODD_id in ODDs.keys():
            odd = ET.SubElement(lhc, "ODD", ODD=ODD_id)
            DILs = {}
            for ft in ODDs[ODD_id]:
                self.add_list_to_dict(DILs, ft.attributes()[self.id_DIL], ft)
            for DIL_id in DILs.keys():
                dil = ET.SubElement(odd, "DIL", DIL=DIL_id)
                PORs = {}
                for ft in DILs[DIL_id]:
                    self.add_list_to_dict(PORs, ft.attributes()[self.id_POR], ft)
                for POR_id in PORs.keys():
                    dict_ = self.fillup_attributes_dict(self.POR_items, self.POR_ids,
                                                        PORs[POR_id][0]
                                                        .attributes())
                    por = ET.SubElement(dil, "POR",  dict_)
                    self.process_psk(lyr, por, PORs[POR_id])
                    if PORs[POR_id][0].attributes()[self.id_PSK] in self.kats.keys():
                        for kat in self.kats[PORs[POR_id][0].attributes()[self.id_PSK]]:
                            dict_ = self.fillup_attributes_dict(self.KAT_items,
                                                                self.KAT_ids,
                                                                kat.
                                                                attributes())
                            ET.SubElement(por, "KAT", dict_)

        str_xml = ET.tostring(root, 'utf-8')

        with codecs.open(os.path.join(self.out_xml.address.text(), "output.xml"), "w", "utf-8") as f:
            res = self.prettify(str_xml)
            f.write(res)

        self.out_xml.close()
        iface.messageBar().clearWidgets()

    def set_nei(self):
        self.distance.show()

    def set_distance_to_nei(self):
        new_n = self.distance.number.text()
        lyr = iface.activeLayer()
        idx = lyr.fieldNameIndex('max_to_nei')
        fts = lyr.getFeatures()
        lyr.startEditing()
        for ft in fts:
            lyr.changeAttributeValue(ft.id(), idx, new_n, True)
        lyr.commitChanges()
        self.distance.close()


    def nei(self):
        self.select_neighbour()

   
    def sekvence(self):
        self.sekvencie.show()
        self.edit_sek = 1
        self.sekvencie.number.setText(str(self.num_of_sek))
        self.edit_new_sek()
        
    def end_sek(self):
        self.edit_sek = 0
        self.num_of_item = 0
        self.num_of_sek += 1
        self.sekvencie.close()
        self.colorize()

    def new_sek(self):
        self.sekvencie.number.setText(str(self.num_of_sek))
        self.num_of_sek += 1
        self.num_of_item = 0
        self.sekvencie.number.setText(str(self.num_of_sek))

    def edit_new_sek(self):
        self.num_of_item += 1
        lyr = iface.activeLayer()
        fts = lyr.selectedFeatures()
        if fts == []:
            return

        idx = lyr.fieldNameIndex('sekvencia')
        text = fts[0].attributes()[idx]
        if text == ";":
            text = str(self.num_of_sek)+','+str(self.num_of_item)+';'
        else:
            text = text+str(self.num_of_sek)+','+str(self.num_of_item)+';'
        lyr.startEditing()
        lyr.changeAttributeValue(fts[0].id(),idx,text)
        lyr.commitChanges()
        #lyr.setSelectedFeatures([fts[0].id()])
        fts = lyr.selectedFeatures()
        self.set_new_color(lyr,fts[0]) 
        

    #tu sa nastavuje parameter pre farbenie polygonov
    def get_color(self, obj, min_a, max_a, min_l, max_l):
        layerMap = QgsProject.instance().mapLayers()
        for name, lyr in layerMap.items():
            if lyr.name() == "Lesne porasty":
                layer = lyr
        COLOR = 'BW'
        if obj.geometry().area() <= max_a and obj.geometry().area() >= min_a:
            if self.isWideEnough(obj,min_l) and self.isntWider(obj, max_l):
                COLOR = 'BR'
            else:
                COLOR = 'LW'
        elif self.isWideEnough(obj, min_l) and self.isntWider(obj, max_l):
            COLOR = 'AW'
        sek = layer.fieldNameIndex('sekvencia')
        prio = layer.fieldNameIndex('priorita')
        if obj.attributes()[sek] != ';' and obj.attributes()[prio] != 0:
            COLOR = '!+-!'
        elif obj.attributes()[sek] != ';':
            COLOR = '+'
        elif obj.attributes()[prio] != 0:
            COLOR = '-'
        return COLOR
   

    def isntWider(self, ft, r):
        new_ft = ft.geometry().buffer(0,1)
        new_ft = new_ft.convexHull()
        new_ft = new_ft.buffer(-1*(r/2),1)
        if new_ft.isMultipart():
            for i in range(len(new_ft.asMultiPolygon())):
                Multi  = new_ft.asMultiPolygon()
                if Multi != []:
                    return False
        else:
            Poly = new_ft.asPolygon()
            if Poly != [[]]:
                return False
        return True



    def isWideEnough(self, ft, r):
        new_ft = ft.geometry().buffer(-1*(r/2),1)
        if new_ft.isMultipart():
            return False
        else:
            Poly = new_ft.asPolygon()
            if Poly == [[]]:
                return False
        return True




    #funkcia na delenie polygonov
    def cut_polygon(self):
        title = QtCore.QCoreApplication.translate("digitizingtools", "Splitter")
        splitterLayer = dtutils.dtChooseVectorLayer(self.iface,  1,  msg = QtCore.QCoreApplication.translate("digitizingtools", "splitter layer"))

        if splitterLayer == None:
            self.iface.messageBar().pushMessage(title,  QtCore.QCoreApplication.translate("digitizingtools", "Please provide a line layer to split with."))
        else:
            passiveLayer = self.iface.activeLayer()
            passiveLayer.startEditing()
            msgLst = dtutils.dtGetNoSelMessage()
            noSelMsg1 = msgLst[0]

            if splitterLayer.selectedFeatureCount() == 0:
                self.iface.messageBar().pushMessage(title, noSelMsg1 + " " + splitterLayer.name())
                return None
            elif splitterLayer.selectedFeatureCount() != 1:
                numSelSplitMsg = dtutils.dtGetManySelMessage(splitterLayer)
                self.iface.messageBar().pushMessage(title, numSelSplitMsg  + \
                    QtCore.QCoreApplication.translate("digitizingtools", " Please select only one feature to split with."))
            else:
                if passiveLayer.selectedFeatureCount() == 0:
                    self.iface.messageBar().pushMessage(title,  noSelMsg1  + " " + passiveLayer.name() + ".\n" + \
                        QtCore.QCoreApplication.translate("digitizingtools", " Please select the features to be splitted."))
                    return None

               # determine srs, we work in the project's srs
                splitterCRSSrsid = splitterLayer.crs().srsid()
                passiveCRSSrsid = passiveLayer.crs().srsid()
                mc = self.iface.mapCanvas()
                renderer = mc.mapRenderer()
                projectCRSSrsid = renderer.destinationCrs().srsid()
                passiveLayer.beginEditCommand(QtCore.QCoreApplication.translate("editcommand", "Split features"))
                featuresBeingSplit = 0
                featuresToAdd = []

                for feat in splitterLayer.selectedFeatures():
                    splitterGeom = feat.geometry()

                    if not splitterGeom.isGeosValid():
                        thisWarning = dtutils.dtGetInvalidGeomWarning(splitterLayer)
                        dtutils.dtShowWarning(self.iface, thisWarning)
                        continue

                    if splitterCRSSrsid != projectCRSSrsid:
                        splitterGeom.transform(QgsCoordinateTransform(splitterCRSSrsid,  projectCRSSrsid))
                    original_id = passiveLayer.fieldNameIndex('original')
                    
                    if passiveLayer.selectedFeatures()[0].attributes()[original_id] == -1:
                        self.create_copy_of_feature(passiveLayer.selectedFeatures()[0])
                        passiveLayer.startEditing()
                    
                    for selFeat in passiveLayer.selectedFeatures():
                        selGeom = selFeat.geometry()
                        if not selGeom.isGeosValid():
                            thisWarning = dtutils.dtGetInvalidGeomWarning(passiveLayer)
                            dtutils.dtShowWarning(self.iface, thisWarning)
                            continue

                        if passiveCRSSrsid != projectCRSSrsid:
                            selGeom.transform(QgsCoordinateTransform(passiveCRSSrsid,  projectCRSSrsid))

                        if splitterGeom.intersects(selGeom): # we have a candidate
                            splitterPList = dtutils.dtExtractPoints(splitterGeom)

                            try:
                                result,  newGeometries,  topoTestPoints = selGeom.splitGeometry(splitterPList,  False) #QgsProject.instance().topologicalEditing())
                            except:
                                self.iface.messageBar().pushMessage(title,
                                    dtutils.dtGetErrorMessage() + QtCore.QCoreApplication.translate("digitizingtools", "splitting of feature") + " " + str(selFeat.id()),
                                    level=QgsMessageBar.CRITICAL)
                                return None

                            if result == 0:
                                passiveLayer.startEditing()
                                selFeat.setGeometry(selGeom)
                                passiveLayer.updateFeature(selFeat)
                                self.set_new_color(passiveLayer, selFeat)

                                if len(newGeometries) > 0:
                                    featuresBeingSplit += 1
                                    newFeatures = dtutils.dtMakeFeaturesFromGeometries(passiveLayer,  selFeat,  newGeometries)

                                    for newFeat in newFeatures:
                                        newGeom = newFeat.geometry()

                                        if passiveCRSSrsid != projectCRSSrsid:
                                            newGeom.transform(QgsCoordinateTransform( projectCRSSrsid,  passiveCRSSrsid))
                                            newFeat.setGeometry(newGeom)

                                        featuresToAdd.append(newFeat)

                if featuresBeingSplit > 0:
                    #features = passiveLayer.selectedFeatures()
                    #self.set_new_color(passiveLayer, features[0])

                    #TU MAME FEATURE!
                    for item in featuresToAdd:
                        self.duplicate_attributes_from_selected(passiveLayer,
                                passiveLayer.selectedFeatures()[0], item)
                    passiveLayer.startEditing()
                    passiveLayer.addFeatures(featuresToAdd,  False)
                    passiveLayer.endEditCommand()
                    passiveLayer.commitChanges()
                    passiveLayer.removeSelection()
                else:
                    passiveLayer.destroyEditCommand()

    def duplicate_attributes_from_selected(self, lyr, from_item, to_item):
        id_C = lyr.fieldNameIndex('COLOR')
        id_A = lyr.fieldNameIndex('max_area')
        id_L = lyr.fieldNameIndex('max_len')
        id_MA = lyr.fieldNameIndex('min_area')
        id_ML = lyr.fieldNameIndex('min_len')
        id_PSK = lyr.fieldNameIndex('PSK_NUM')
        new_psk_num = len(list(lyr.getFeatures()))
        csv_drv = None
        csv_etz = None
        csv_zal = None
        layerMap = QgsProject.instance().mapLayers()
        for name, lyr in layerMap.items():
            if lyr.name() == "Dreviny":
                csv_drv = lyr
            elif lyr.name() == "Porast":
                csv_etz = lyr
            elif lyr.name() == "Zalozenie":
                csv_zal = lyr
            elif lyr.name() == "Poskodenia":
                csv_pos = lyr
            elif lyr.name() == "Kategorie":
                csv_kat = lyr
        
        lyr.setSelectedFeatures([from_item.id()])

        etzs = self.table_to_list(self.shower.etaz)
        drvs = self.table_to_list(self.shower.drevina)
        zals = self.table_to_list(self.shower.zalozene)
        poss = self.table_to_list(self.shower.pos)
        kats = self.table_to_list(self.shower.kategoria)

        drvs = [list(x) for x in zip(*drvs)]
        etzs = [list(x) for x in zip(*etzs)]
        zals = [list(x) for x in zip(*zals)]
        poss = [list(x) for x in zip(*poss)]
        kats = [list(x) for x in zip(*kats)]

        new_drv_start = len(list(csv_drv.getFeatures()))
        new_etz_start = len(list(csv_etz.getFeatures()))
        for i in range(len(etzs)):
            orig_etz = etzs[i][-1]
            etzs[i][-2] = new_psk_num
            etzs[i][-1] = new_etz_start
            for j in range(len(drvs)):
                if drvs[j][-2] == orig_etz:
                    drvs[j][-2] = new_etz_start
                orig_drv = drvs[j][-1]
                drvs[j][-1] = new_drv_start
                for k in range(len(poss)):
                    if poss[k][-1] == orig_drv:
                        poss[k][-1] = new_drv_start
                new_drv_start += 1
            for j in range(len(zals)):
                if zals[j][-1] == orig_etz:
                    zals[j][-1] = new_etz_start

            new_etz_start += 1
        for i in range(len(kats)):
            kats[i][-1] = new_psk_num

        for kat in kats:
            new_ft = QgsFeature(csv_kat.pendingFields())
            new_ft.setAttributes(kat)
            csv_kat.dataProvider().addFeatures([new_ft])

        for etz in etzs:
            new_ft = QgsFeature(csv_etz.pendingFields())
            new_ft.setAttributes(etz)
            csv_etz.dataProvider().addFeatures([new_ft])

        for drv in drvs:
            new_ft = QgsFeature(csv_drv.pendingFields())
            new_ft.setAttributes(drv)
            csv_drv.dataProvider().addFeatures([new_ft])

        for pos in poss:
            new_ft = QgsFeature(csv_pos.pendingFields())
            new_ft.setAttributes(pos)
            csv_pos.dataProvider().addFeatures([new_ft])

        for zal in zals:
            new_ft = QgsFeature(csv_zal.pendingFields())
            new_ft.setAttributes(zal)
            csv_zal.dataProvider().addFeatures([new_ft])

        atts = from_item.attributes()
        to_item.setAttributes(atts)

        maximum_area = from_item.attributes()[id_A]
        maximum_length = from_item.attributes()[id_L]
        minimum_area = from_item.attributes()[id_MA]
        minimum_length = from_item.attributes()[id_ML]
        COLOR = self.get_color(to_item, minimum_area,
                               maximum_area, minimum_length, maximum_length)

        atts[id_C] = COLOR
        atts[id_PSK] = new_psk_num
        to_item.setAttributes(atts)
        # lyr.changeAttributeValue(item.id(),id_C,COLOR,True)

    def create_copy_of_feature(self, oldFeature):
        lyr = self.iface.activeLayer()
        new_feature = QgsFeature()
        new_feature.setGeometry(oldFeature.geometry())
        # set all values
        self.duplicate_attributes_from_selected(lyr, oldFeature, new_feature)
        # change the is_original to -2
        idx = lyr.fieldNameIndex("original")
        lyr.startEditing()
        lyr.changeAttributeValue(oldFeature.id(), idx, -2, True)
        lyr.addFeatures([new_feature])
        lyr.changeAttributeValue(lyr.selectedFeatures()[0].id(), idx, oldFeature.id(), True)
        lyr.commitChanges()


    #Vracia list, kde index v liste je index feature a obsahuje list indexov
        #vsetkych susediacich
    def select_neighbour(self):
        lyr = iface.activeLayer()
        idx = lyr.fieldNameIndex('max_to_nei')
        id_N = lyr.fieldNameIndex('neighbours')
        orig_id = lyr.fieldNameIndex('original')
        features = list(lyr.getFeatures())
        c = lyr.getFeatures()
        lyr.startEditing()
        for c1 in c:
            r = c1.attributes()[idx]
            buffered = c1.geometry().buffer(r, 1)

            ids = []
            for ft in features:

                if buffered.intersects(ft.geometry()) and ft.attributes()[orig_id] != -2:
                    ids.append(ft.id())
            #remove itself from list
            if c1.id() in ids:
                ids.remove(c1.id())
            if (len(ids) >= 1):
                lyr.changeAttributeValue(c1.id(),id_N,";".join(str(x) for x in ids), True)
            else:
                lyr.changeAttributeValue(c1.id(),id_N,";", True)
        lyr.commitChanges()

    #Funkcia ktora zvyrazni dreviny ak sa klikne na etaz    
    def highlight_drv(self):
        self.shower.drevina.clearSelection()#najskor odznacim vsetky dreviny
        self.shower.drevina.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)#zvolim
            #ze budem vyberat viacero riadkov naraz
        drvs = self.table_to_list(self.shower.etaz)[-1]#ziskam cisla vsetkych
            #drevin
        list_for_drvs = []
        indexes = self.shower.etaz.selectionModel().selectedRows()#ziskam
            #vsetky vybrane riadky etazi
        for index in sorted(indexes):
            list_for_drvs.append(drvs[index.row()])#urobim si zoznam cisel
                #drevin, ktore odpovedaju vybranym etazam
        ids_of_rows = []

        drv_att = self.table_to_list(self.shower.drevina)
        drvs_atts = drv_att[-2]
        for i in range(len(drvs_atts)):
            if drvs_atts[i] in list_for_drvs:
                ids_of_rows.append(i)#a ak sa vyskytuje cislo dreviny  oboch
                    #zoznamoch, tak si ho ulozim
            
        for item in ids_of_rows:
            #for number in range(len(drv_att)):
                #self.shower.drevina.setItem(item,number,QtGui.QTableWidgetItem())
                #self.shower.drevina.item(item,number).setBackground(QtGui.QColor("green"))
            self.shower.drevina.selectRow(item)#q vsetky ulozene cisla vyberiem
        
    def set_new_color(self,lyr,ft):
        id_C = lyr.fieldNameIndex('COLOR')#ziskam indexy v poli atributov
        id_A = lyr.fieldNameIndex('max_area')
        id_L = lyr.fieldNameIndex('max_len')
        id_MA = lyr.fieldNameIndex('min_area')
        id_ML = lyr.fieldNameIndex('min_len')

        
        lyr.startEditing()
        maximum_length = ft.attributes()[id_L]
        maximum_area = ft.attributes()[id_A]
        minimum_length = ft.attributes()[id_ML]
        minimum_area = ft.attributes()[id_MA]

        COLOR = self.get_color(ft, minimum_area,\
                    maximum_area, minimum_length, maximum_length)
        
        lyr.changeAttributeValue(ft.id(),id_C,COLOR,True)
        
        lyr.commitChanges()
        self.colorize()               

    def Error_message(self, text):
        self.shower.showNormal()
        self.shower.showMinimized()
        QMessageBox.information(self.iface.mainWindow(),"Chyba",text)

    def edit_one_att(self,layer,LineEdit,name_of_field,multiply_by):
        if not LineEdit.isModified():
            return
        new_value = LineEdit.text()
        if  new_value == "":#testujem ci nie je to prazdny retazec
            self.Error_message("Nezadane udaje")
            return
        else:
            try:
                new_value = float(new_value)*multiply_by#testuje ci ej to int
            except:
                self.Error_message("Je potrebne zadat v nezapornych cislach")
                return
            if  new_value < 0:#testujem ci je kladne
                self.Error_message("Je potrebne zadat v nezapornych cislach")
                return

        idx = layer.fieldNameIndex(name_of_field)
        if idx == -1:
            return
        features = layer.selectedFeatures()
        layer.startEditing()
        layer.changeAttributeValue(features[0].id(),idx,new_value,True)
        layer.commitChanges()
        # HACK - wait while, until value is written into memory
        # Should be done with signal `committedAttributeValuesChanges`
        time.sleep(2)
        self.set_new_color(layer,features[0])
        self.colorize()

    #funkcia na editovanie maximalnej plochy
    def edit_area_max(self):
        self.edit_one_att(iface.activeLayer(),self.shower.area_max, "max_area", 10000)

    def edit_priorita(self):
        self.edit_one_att(iface.activeLayer(),self.shower.priorita, "priorita",1)

    def edit_area_min(self):
        self.edit_one_att(iface.activeLayer(),self.shower.area_min, "min_area", 10000)

    def edit_length_min(self):
        self.edit_one_att(iface.activeLayer(),self.shower.length_min, "min_len", 1)
    
    def edit_length_max(self):
        self.edit_one_att(iface.activeLayer(),self.shower.length_max, "max_len", 1)
        
    #funkcia, ktora nastavy vsetkym polozkam atribut COLOR
    def set_ranges_f(self):
        global maximum_length#hranicna hodnota
        global maximum_area#hranicna hodnota
        global minimum_length#hranicna hodnota
        global minimum_area#hranicna hodnota

        maximum_length = self.set_ranges.max_len.text().strip('"')
        maximum_area = self.set_ranges.max_area.text().strip('"')
        minimum_length = self.set_ranges.min_len.text().strip('"')
        minimum_area = self.set_ranges.min_area.text().strip('"')
        
        if  maximum_area == "" or maximum_length == "" or minimum_area == "" or\
            minimum_length == "" :
            self.Error_message("Nezadane udaje")
            self.set_ranges.close()
            return
        else:
            try:
                maximum_area = float(maximum_area)*10000
                maximum_length = float(maximum_length)
                minimum_area = float(minimum_area)*10000
                minimum_length = float(minimum_length)
            except:
                self.Error_message("Je potrebne zadat v desatinnych cislach")
                self.set_ranges.close()
                return
            if  maximum_area <= 0 or maximum_length <=0 or minimum_length < 0\
                or minimum_area < 0:
                self.Error_message("Je potrebne zadat v nezapornych cislach")
                self.set_ranges.close()
                return

        self.set_ranges.close()
        self.set_colorize_values()


        
        
    def open_ranges(self):
        self.set_ranges.show()


    def table_to_list(self, table):
        result = []
        num_rows, num_cols = table.rowCount(), table.columnCount()
        for col in range(num_cols):
            rows = []
            for row in range(num_rows):
                item = table.item(row, col)
                rows.append(item.text() if item else "")
            result.append(rows)
        return result

    def set_colorize_values(self):
        global maximum_length
        global maximum_area
        global minimum_length
        global minimum_area
        layerMap = QgsProject.instance().mapLayers()
        for name, lyr in layerMap.items():
            if lyr.name() == "Lesne porasty":
                layer = lyr

        id_C = layer.fieldNameIndex('COLOR')
        id_A = layer.fieldNameIndex('max_area')
        id_L = layer.fieldNameIndex('max_len')
        id_MA = layer.fieldNameIndex('min_area')
        id_ML = layer.fieldNameIndex('min_len')
        
        layer.startEditing()
        for feature in layer.getFeatures():
            COLOR = self.get_color(feature, minimum_area,\
                    maximum_area, minimum_length, maximum_length)
            layer.changeAttributeValue(feature.id(),id_C,str(COLOR))
            layer.changeAttributeValue(feature.id(),id_A,maximum_area)
            layer.changeAttributeValue(feature.id(),id_L,maximum_length)
            layer.changeAttributeValue(feature.id(),id_MA,minimum_area)
            layer.changeAttributeValue(feature.id(),id_ML,minimum_length)
        layer.commitChanges()
        self.colorize()

    def colorize(self):
        
        layerMap = QgsProject.instance().mapLayers()
        for name, lyr in layerMap.items():
            if lyr.name() == "Lesne porasty":
                layer = lyr
        correct = {
                'BR':(QColor(73,238,13),'Both right'),
                'AW':(QColor(230,238,13),'Area wrong'),
                'LW':(QColor(243,113,14),'Width wrong'),
                'BW':(QColor(198,18,18),'Both wrong'),
                '!+-!':(QColor(38,118,238),'Both set'),
                '+' :(QColor(50,9,213), 'Sequence set'),
                '-' :(QColor(153,0,204), 'Priority set')
                }
        categories = []
        for COLOR, (color, label) in correct.items():
            sym = QgsSymbolV2.defaultSymbol(layer.geometryType())
            sym.setColor(QColor(color))
            category = QgsRendererCategoryV2(COLOR, sym, label)
            categories.append(category)

        field = "COLOR"

        renderer = QgsCategorizedSymbolRendererV2(field, categories)

        layer.setRendererV2(renderer)

    def edit_list_by_types(self,new_list,lyr_pointer):
        list_of_fields = list(lyr_pointer.pendingFields()) 
        features = list(lyr_pointer.getFeatures())
        list_of_wrongs = []
        for i in range(len(new_list)):
            if new_list[i] == "":
                continue
            elif type(features[0][i]) is int:
                try:
                    new_list[i] = int(new_list[i])
                except:
                    list_of_wrongs.append(list_of_fields[i].name())
            elif type(features[0][i]) is float:
                try:
                    new_list[i] = float(new_list[i])
                except:
                    list_of_wrongs.append(list_of_fields[i].name())
        
        if list_of_wrongs != []:
            self.Error_message("Zle typy u poloziek "+str(list_of_wrongs))
         
        return new_list
    
    
    def save_new_etz(self):
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Porast":
                drv_csv = layer
        
        all_data =  self.table_to_list(self.add_etz.etz_table)

        new_list = [ item[0] for item in all_data]
        new_list = self.edit_list_by_types(new_list, drv_csv)
        
        new_ft = QgsFeature(drv_csv.pendingFields())
        new_ft.setAttributes(new_list)
        drv_csv.dataProvider().addFeatures([new_ft])

        self.show_atts()
        self.add_etz.close()

    def add_etz_f(self):
        self.add_etz.show()
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Porast":
                drv_csv = layer
        
        new_number =  len(list(drv_csv.getFeatures()))
        
        fields_drv = drv_csv.pendingFields()
        field_names_drv = [field.name() for field in fields_drv]
        
        default_list_drv = self.table_to_list(self.shower.etaz)
        if default_list_drv == []:
            default_list_drv = [["" for field in fields_drv]]
        else:
            default_list_drv = [[item[0] for item in default_list_drv]]
        default_list_drv[0][-1] = str(new_number)
        self.add_etz.set_data(field_names_drv,
                default_list_drv,self.add_etz.etz_table)

    def save_new_drv(self):
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Dreviny":
                drv_csv = layer
        
        all_data =  self.table_to_list(self.add_drv.drv_table)

        new_list = [ item[0] for item in all_data]
        new_list = self.edit_list_by_types(new_list, drv_csv)
        
        new_ft = QgsFeature(drv_csv.pendingFields())
        new_ft.setAttributes(new_list)
        drv_csv.dataProvider().addFeatures([new_ft])

        self.show_atts()
        self.add_drv.close()

    def add_drv_f(self):
        self.add_drv.show()
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Dreviny":
                drv_csv = layer
        
        new_number =  len(list(drv_csv.getFeatures()))
        etz_nums =  self.table_to_list(self.shower.etaz)[-1]
        
        fields_drv = drv_csv.pendingFields()
        field_names_drv = [field.name() for field in fields_drv]
         
        indexes = self.shower.etaz.selectionModel().selectedRows()
        if indexes == []:

            self.Error_message("Musite vybrat etaz, aby ste mohli pridat drevinu")
            self.add_drv.close()
            return
        
        
        default_list_drv = self.table_to_list(self.shower.drevina)
        if default_list_drv == []:
            default_list_drv = [["" for field in fields_drv]]
            default_list_drv[0][-2] = etz_nums[indexes[0].row()]
        else:
            default_list_drv = [[item[0] for item in default_list_drv]]
            default_list_drv[0][-2] = etz_nums[indexes[0].row()]
        default_list_drv[0][-1] = str(new_number)
        self.add_drv.set_data(field_names_drv,
                default_list_drv,self.add_drv.drv_table)



    def save_all_11(self):
        self.save_all.show()

    def open_layer(self, name, address, type_ft, empty=False):
        """Open layer from file."""
        new_ft = QgsVectorLayer(address, name, type_ft)
        if (new_ft.featureCount() < 1):
            if not empty:
                return
        QgsProject.instance().addMapLayer(new_ft)
        canvas = qgis.utils.iface.mapCanvas()
        canvas.setExtent(new_ft.extent())

    def toggle_holosec(self):
        if self.create_processes.holosec.isChecked():
            self.create_processes.etaz.setEnabled(False)
            self.create_processes.drevina.setEnabled(False)
            self.create_processes.intenzita.setEnabled(False)
            self.create_processes.odstup.setEnabled(False)
            self.create_processes.sec_id.setEnabled(False)
            self.create_processes.new_sec.setEnabled(False)
        else:
            self.create_processes.etaz.setEnabled(True)
            self.create_processes.drevina.setEnabled(True)
            self.create_processes.intenzita.setEnabled(True)
            self.create_processes.odstup.setEnabled(True)
            self.create_processes.sec_id.setEnabled(True)
            self.create_processes.new_sec.setEnabled(True)
            if not self.create_processes.sec_id.count():
                self.create_processes.sec_id.addItem('1')

    def toggle_sec(self):
        lyr = iface.activeLayer()
        fts = lyr.selectedFeatures()
        if fts == []:
            return

        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Tazobne typy":
                taz_typ_csv = layer

        id_psk = lyr.fieldNameIndex('PSK_NUM')
        id_odstup = taz_typ_csv.fieldNameIndex('ODSTUP')
        psk_id = fts[0].attributes()[id_psk]

        sec_id = self.create_processes.sec_id.currentText()
        expr_str = ""
        expr_str += "\"PSK_NUM\" = '{0}'".format(psk_id)
        expr_str += " AND \"SEC_ID\" = '{0}'".format(sec_id)
        expr = QgsExpression(expr_str)
        found = taz_typ_csv.getFeatures(QgsFeatureRequest(expr))
        for found_item in found:
            self.create_processes.odstup.setText(found_item.attributes()[id_odstup])
        self.create_processes.odstup.setEnabled(False)

    def toggle_typ(self):
        lyr = iface.activeLayer()
        fts = lyr.selectedFeatures()
        if fts == []:
            return

        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Tazobne typy":
                taz_typ_csv = layer

        id_psk = lyr.fieldNameIndex('PSK_NUM')
        id_prirazeni = taz_typ_csv.fieldNameIndex('PRIRAZENI')
        id_typ = taz_typ_csv.fieldNameIndex('TYP')
        psk_id = fts[0].attributes()[id_psk]

        typ_id = self.create_processes.typ_id.currentText()
        expr_str = ""
        expr_str += "\"PSK_NUM\" = '{0}'".format(psk_id)
        expr_str += " AND \"ID\" = '{0}'".format(typ_id)
        expr = QgsExpression(expr_str)
        found = taz_typ_csv.getFeatures(QgsFeatureRequest(expr))
        for found_item in found:
            if found_item.attributes()[id_typ] == 'holosec':
                self.create_processes.holosec.setChecked(True)
                self.create_processes.podrostne.setChecked(False)
            else:
                self.create_processes.holosec.setChecked(False)
                self.create_processes.podrostne.setChecked(True)
            self.create_processes.prirazeni.setText(found_item.attributes()[id_prirazeni])

    def toggle_definovane_zasahy(self):
        if self.create_processes.definovane.selectedItems():
            self.create_processes.remove.setEnabled(True)
        else:
            self.create_processes.remove.setEnabled(False)

    def remove_zasahy(self):
        lyr = iface.activeLayer()
        fts = lyr.selectedFeatures()
        if fts == []:
            return

        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Porast":
                etz_csv = layer
            if layer.name() == "Tazobne typy":
                taz_typ_csv = layer

        taz_typ_csv.startEditing()

        idx = lyr.fieldNameIndex('PSK_NUM')
        psk_id = fts[0].attributes()[idx]

        to_delete = self.create_processes.definovane.selectedItems()
        expr_str = ""
        for item in to_delete:
            fields = item.text().split(' ')
            expr_str += "\"PSK_NUM\" = '{0}'".format(psk_id)
            expr_str += " AND \"PRIRAZENI\" = '{0}'".format(fields[0])
            expr_str += " AND \"ID\" = '{0}'".format(fields[6])
            expr_str += " AND \"TYP\" = '{0}'".format(fields[1])
            if fields[7] == "NULL":
                expr_str += " AND \"SEC_ID\" IS NULL"
            else:
                expr_str += " AND \"SEC_ID\" = '{0}'".format(fields[7])
            if fields[2] == "NULL":
                expr_str += " AND \"ETAZ\" IS NULL"
            else:
                expr_str += " AND \"ETAZ\" = '{0}'".format(fields[2])

            if fields[3] == "NULL":
                expr_str += " AND \"DR\" IS NULL"
            else:
                expr_str += " AND \"DR\" = '{0}'".format(fields[3])

            if fields[4] == "NULL":
                expr_str += " AND \"INTENZITA\" IS NULL"
            else:
                expr_str += " AND \"INTENZITA\" = '{0}'".format(fields[4])
            if fields[5] == "NULL":
                expr_str += " AND \"ODSTUP\" IS NULL"
            else:
                expr_str += " AND \"ODSTUP\" = '{0}'".format(fields[5])
            expr = QgsExpression(expr_str)
            found = taz_typ_csv.getFeatures(QgsFeatureRequest(expr))
            for found_item in found:
                taz_typ_csv.deleteFeature(found_item.id())
        taz_typ_csv.commitChanges()
        self.open_processes()

    def open_processes(self):
        lyr = iface.activeLayer()
        fts = lyr.selectedFeatures()
        if fts == []:
            return

        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Porast":
                etz_csv = layer
            if layer.name() == "Tazobne typy":
                taz_typ_csv = layer

        idx = lyr.fieldNameIndex('PSK_NUM')
        psk_id = fts[0].attributes()[idx]

        self.create_processes.etaz.clear()
        self.toggle_holosec()

        expr = QgsExpression("PSK_NUM ="+ str(psk_id))
        selected_etzs = etz_csv.getFeatures(QgsFeatureRequest(expr))
        selected_taz_typ = taz_typ_csv.getFeatures(QgsFeatureRequest(expr))
        for etaz in selected_etzs:
            self.create_processes.etaz.addItem(etaz.attributes()[0],
                                               etaz.attributes()[-1])

        self.create_processes.definovane.clear()
        self.create_processes.typ_id.clear()
        self.create_processes.sec_id.clear()
        for taz_typ in selected_taz_typ:
            one_taz_typ = ""
            atts = taz_typ.attributes()
            one_taz_typ += "{0}".format(atts[6])
            for index in [5, 0, 1, 2, 3, 7, 4]:
                one_taz_typ += " {0}".format(atts[index])
            self.create_processes.definovane.addItem(one_taz_typ)
            self.create_processes.typ_id.addItem(atts[7])
            if atts[3]:
                self.create_processes.sec_id.addItem(atts[4])
        if self.create_processes.typ_id.count():
            self.create_processes.prirazeni.setEnabled(False)
            self.create_processes.holosec.setEnabled(False)
            self.create_processes.podrostne.setEnabled(False)
            self.create_processes.odstup.setEnabled(False)
        else:
            self.create_processes.prirazeni.setEnabled(True)
            self.create_processes.holosec.setEnabled(True)
            self.create_processes.podrostne.setEnabled(True)
            self.create_processes.odstup.setEnabled(True)
            self.create_processes.sec_id.setEnabled(False)
            self.create_processes.new_sec.setEnabled(False)
            self.create_processes.typ_id.addItem('1')
            self.create_processes.sec_id.addItem('1')

        self.create_processes.show()

    def new_sec_id(self):
        sec_id = self.create_processes.sec_id
        if self.create_processes.sec_id.count():
            biggest = max([int(sec_id.itemText(i)) for i in range(sec_id.count())])
            biggest += 1
            sec_id.addItem(str(biggest))
            sec_id.setCurrentIndex(sec_id.findText(str(biggest), QtCore.Qt.MatchFixedString))
        self.create_processes.odstup.setEnabled(True)

    def new_typ_id(self):
        typ_id = self.create_processes.typ_id
        if self.create_processes.typ_id.count():
            biggest = max([int(typ_id.itemText(i)) for i in range(typ_id.count())])
            biggest += 1
            typ_id.addItem(str(biggest))
            typ_id.setCurrentIndex(typ_id.findText(str(biggest), QtCore.Qt.MatchFixedString))
        self.create_processes.prirazeni.setEnabled(True)
        self.create_processes.holosec.setEnabled(True)
        self.create_processes.podrostne.setEnabled(True)

    def update_drv_in_processes(self, nth):
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Dreviny":
                drv_csv = layer

        self.create_processes.drevina.clear()

        expr = QgsExpression('ETZ_NUM =' + str(self.create_processes.etaz.itemData(nth)))
        drvs = drv_csv.getFeatures(QgsFeatureRequest(expr))
        for drevina in drvs:
            self.create_processes.drevina.addItem(drevina.attributes()[0])

    def add_new_process(self):
        lyr = iface.activeLayer()
        fts = lyr.selectedFeatures()
        if fts == []:
            return

        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Porast":
                etz_csv = layer
            if layer.name() == "Tazobne typy":
                taz_typ_csv = layer

        idx = lyr.fieldNameIndex('PSK_NUM')
        psk_id = fts[0].attributes()[idx]

        expr = QgsExpression("PSK_NUM ="+ str(psk_id))
        all_taz_typ = taz_typ_csv.getFeatures(QgsFeatureRequest(expr))

        prirazeni = self.create_processes.prirazeni.text()
        if self.create_processes.holosec.isChecked():
            typ = "holosec"
        else:
            typ = "podrostni"

        expr = QgsExpression("\"PRIRAZENI\" = '{0}' AND \"TYP\" = '{1}'".format(prirazeni, typ))

        new_taz_typ = []
        if typ == 'holosec':
            new_taz_typ = ["", "", "", "", ""]
        else:
            new_taz_typ.append(self.create_processes.etaz.currentText())
            new_taz_typ.append(self.create_processes.drevina.currentText())
            # TODO verify the following two, that they make sense
            new_taz_typ.append(self.create_processes.intenzita.text())
            new_taz_typ.append(self.create_processes.odstup.text())
            new_taz_typ.append(self.create_processes.sec_id.currentText())
        new_taz_typ.append(typ)
        new_taz_typ.append(prirazeni)
        new_taz_typ.append(self.create_processes.typ_id.currentText())
        new_taz_typ.append(psk_id)

        new_ft = QgsFeature(taz_typ_csv.pendingFields())
        new_ft.setAttributes(new_taz_typ)
        taz_typ_csv.dataProvider().addFeatures([new_ft])
        self.open_processes()

    def open_all_11(self):
        self.open_all.show()

    def open_all_1(self):

        self.open_layer("Porast", input_folder+'/etz.dbf',"ogr")
        self.open_layer("Tazobne typy", input_folder+'/taz_typ.dbf',"ogr", True)
        self.open_layer("Dreviny", input_folder+'/drv.dbf',"ogr")
        self.open_layer("Kategorie", input_folder+'/kat.dbf',"ogr")
        self.open_layer("Zalozenie", input_folder+'/zal.dbf',"ogr")
        self.open_layer("Poskodenia", input_folder+'/pos.dbf',"ogr")
        self.open_layer("VysledkyObnova", input_folder+'/vys_obn.dbf',"ogr", True)
        self.open_layer("VysledkyVychova", input_folder+'/vys_vych.dbf',"ogr", True)
        #self.open_layer("KTO",input_folder+'/KTO.shp',"ogr")
        #self.open_layer("Body",input_folder+'/KBO.shp',"ogr")
        self.open_layer("KLO",input_folder+'/KLO.shp',"ogr")
        self.open_layer("Bezlesie",input_folder+'/BZL.shp',"ogr")
        self.open_layer("Ine plochy",input_folder+'/JP.shp',"ogr")
        self.open_layer("KPO",input_folder+'/KPO.shp',"ogr")
        self.open_layer("Lesne porasty",input_folder+'/PSK.shp',"ogr")


        self.open_all.close()
    
    def save_layer(self,layer,address):
        error = QgsVectorFileWriter.writeAsVectorFormat(layer,
            address, "System", layer.crs(),"ESRI Shapefile")
        if error == QgsVectorFileWriter.NoError:
            return 0
        else:
            return 1
    
    
    def save_all_1(self):
        global pretty_folder
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Porast":
                self.save_layer(layer,pretty_folder+'/etz')
            elif layer.name() == "Tazobne typy":
                self.save_layer(layer,pretty_folder+'/taz_typ')
            elif layer.name() == "Dreviny":
                self.save_layer(layer,pretty_folder+'/drv')
            elif layer.name() == "Kategorie":
                self.save_layer(layer,pretty_folder+'/kat')
            elif layer.name() == "Zalozenie":
                self.save_layer(layer,pretty_folder+'/zal')
            elif layer.name() == "Poskodenia":
                self.save_layer(layer,pretty_folder+'/pos')
            elif layer.name() == "VysledkyObnova":
                self.save_layer(layer,pretty_folder+'/vys_obn')
            elif layer.name() == "VysledkyVychova":
                self.save_layer(layer,pretty_folder+'/vys_vych')
            #elif layer.name() == "KTO":
            #    self.save_layer(layer,pretty_folder+'/KTO')
            #elif layer.name() == "Body":
            #    self.save_layer(layer,pretty_folder+'/KBO')
            elif layer.name() == "KLO":
                self.save_layer(layer,pretty_folder+'/KLO')
            elif layer.name() == "Bezlesie":
                self.save_layer(layer,pretty_folder+'/BZL')
            elif layer.name() == "Ine plochy":
                self.save_layer(layer,pretty_folder+'/JP')
            elif layer.name() == "KPO":
                self.save_layer(layer,pretty_folder+'/KPO')
            elif layer.name() == "Lesne porasty":
                self.save_layer(layer,pretty_folder+'/PSK')

        self.save_all.close()

    def convert_to_strings(self,old_list):
        new_list_list = []
        new_list = []
        for each_list in old_list:
            new_list = []
            for item in each_list:
                try:
                    new_list.append(str(item))
                except:
                    new_list.append(item)
            new_list_list.append(new_list)
        return new_list_list

    
    
    def edit_main(self,item):
        global edit_pos
         
        if not edit_pos:
        
            lyr = iface.activeLayer()
            features = lyr.selectedFeatures()
            lyr.startEditing()
            lyr.changeAttributeValue(features[0].id(),item.column(),item.text(),True)
            lyr.commitChanges()
        
            
    def edit_attribute(self,lyr,item, list_of_ids):
        lyr.startEditing()
        features = list(lyr.getFeatures())
        type_T =  type(features[list_of_ids[item.row()]][item.column()])
        if type_T is int:
            try:
                lyr.changeAttributeValue(list_of_ids[item.row()],item.column(),int(item.text()),True)
            except:
                self.Error_message("Zly typ, ocakava sa cele cislo")
        elif type_T is float:
            try:
                lyr.changeAttributeValue(list_of_ids[item.row()],item.column(),float(item.text()),True)
            except:
                self.Error_message("Zly typ, ocakava sa desatinne cislo")
                
        else:
            try:
                lyr.changeAttributeValue(list_of_ids[item.row()],item.column(),str(item.text()),True)
            except:
                self.Error_message("Zly typ, ocakava sa retazec")
                #TYPE MOZE BYT NULL!!!
        lyr.commitChanges()
    
    
    def edit_kats(self,item):
        global edit_pos
        global list_of_kats_ids
        if not edit_pos:
            layerMap = QgsProject.instance().mapLayers()
            for name, layer in layerMap.items():
                if layer.name() == "Kategorie":
                    lyr = layer
            self.edit_attribute(lyr, item, list_of_kats_ids)
            
    def edit_etzs(self,item):
        global edit_pos
        global list_of_etzs_ids
        if not edit_pos:
            layerMap = QgsProject.instance().mapLayers()
            for name, layer in layerMap.items():
                if layer.name() == "Porast":
                    lyr = layer
            self.edit_attribute(lyr, item, list_of_etzs_ids)
   
    def edit_poss(self,item):
        global edit_pos
        global list_of_poss_ids
        if not edit_pos:
            layerMap = QgsProject.instance().mapLayers()
            for name, layer in layerMap.items():
                if layer.name() == "Poskodenia":
                    lyr = layer
            self.edit_attribute(lyr, item, list_of_poss_ids)
    
    def edit_drvs(self,item):
        global edit_pos
        global list_of_drvs_ids
        if not edit_pos:
            layerMap = QgsProject.instance().mapLayers()
            for name, layer in layerMap.items():
                if layer.name() == "Dreviny":
                    lyr = layer
            self.edit_attribute(lyr, item, list_of_drvs_ids)
    
    def edit_zals(self,item):
        global edit_pos
        global list_of_zals_ids
        if not edit_pos:
            layerMap = QgsProject.instance().mapLayers()
            for name, layer in layerMap.items():
                if layer.name() == "Zalozenie":
                    lyr = layer
            self.edit_attribute(lyr, item, list_of_zals_ids)

    def show_atts(self):
        if self.create_processes.isVisible():
            self.open_processes()
        if self.edit_sek:
            self.edit_new_sek()
        global edit_pos
        global list_of_kats_ids
        global list_of_etzs_ids
        global list_of_drvs_ids
        global list_of_poss_ids
        global list_of_zals_ids
        list_of_kats_ids = []
        list_of_etzs_ids = []
        list_of_drvs_ids = []
        list_of_poss_ids = []
        list_of_zals_ids = []
        edit_pos = 1
        area = 0
        length = 0
        etz_csv = None
        drv_csv = None
        kat_csv = None
        zal_csv = None
        pos_csv = None
        #vybrana vrstva
        lyr = self.iface.activeLayer()
        self.shower.drevina.clearSelection()
        self.shower.etaz.clearSelection()


        #Vyberieme si potrebne vrsty podla mena - pozor na zmeny!
        layerMap = QgsProject.instance().mapLayers()
        for name, layer in layerMap.items():
            if layer.name() == "Porast":
                etz_csv = layer
            elif layer.name() == "Dreviny":
                drv_csv = layer
            elif layer.name() == "Kategorie":
                kat_csv = layer
            elif layer.name() == "Zalozenie":
                zal_csv = layer
            elif layer.name() == "Poskodenia":
                pos_csv = layer
            elif layer.name() == "VysledkyVychova":
                vys_vych_csv = layer
            elif layer.name() == "VysledkyObnova":
                vys_obn_csv = layer
            elif layer.name() == "Tazobne typy":
                taz_typ_csv = layer
        if not lyr:
            self.Error_message("Ziadna vybrana vrstva")
        else: 
            fields = lyr.pendingFields()#vyberieme vsetky mena atributov
            features = lyr.selectedFeatures()#vyberieme vybrate prvky
            if features != []:

                field_names = [field.name() for field in fields]#vytvorim
                area =  features[0].geometry().area()
                #zahlavie
                #vytvorim tabulku vlastnosti
                features_list = [feature.attributes() for feature in features]
                features_list = self.convert_to_strings(features_list)

                id_area = lyr.fieldNameIndex("max_area") #index parametru PSK_NUM 
                id_len = lyr.fieldNameIndex("max_len") #index parametru PSK_NUM 
                id_Marea = lyr.fieldNameIndex("min_area") #index parametru PSK_NUM 
                id_Mlen = lyr.fieldNameIndex("min_len") #index parametru PSK_NUM 
                id_prio = lyr.fieldNameIndex("priorita") #index parametru PSK_NUM 

                try:
                    self.shower.area_max.setText(str("%.2f"%(float(features_list[0][id_area])/10000)))
                except:
                    self.shower.area_max.setText("0")

                try:
                    self.shower.area_min.setText(str("%.2f"%(float(features_list[0][id_Marea])/10000)))
                except:
                    self.shower.area_min.setText("0")

                self.shower.length_max.setText(features_list[0][id_len])
                self.shower.length_min.setText(features_list[0][id_Mlen])
                self.shower.priorita.setText(features_list[0][id_prio])

                idx = lyr.fieldNameIndex("PSK_NUM") #index parametru PSK_NUM 
                if idx == -1:
                    psk_numb = "xX!48p"
                else:
                    psk_numb = features_list[0][idx] 
            else:
                psk_numb = -1
                field_names = []
                features_list = []

            selected_etzs = []
            fields_etz = []

            expr = QgsExpression("PSK_NUM ="+ str(psk_numb))

            if etz_csv:
                selected_etzs = etz_csv.getFeatures(QgsFeatureRequest(expr))
                fields_etz = etz_csv.pendingFields()
                id_etz = etz_csv.fieldNameIndex('ETZ_NUM')

            selected_kats = []
            if kat_csv:
                selected_kats = kat_csv.getFeatures(QgsFeatureRequest(expr))

            selected_vys_obn = vys_obn_csv.getFeatures(QgsFeatureRequest(expr))
            selected_taz_typ = taz_typ_csv.getFeatures(QgsFeatureRequest(expr))
            selected_vys_vych = vys_vych_csv.getFeatures(QgsFeatureRequest(expr))

            field_names_etz = [field.name() for field in fields_etz]
            selected_etzs = list(selected_etzs)
            features_list_etz = [feature.attributes() for feature in selected_etzs]
            features_list_etz = self.convert_to_strings(features_list_etz)
            for fit in selected_etzs:
                list_of_etzs_ids.append(fit.id())

            fields_vys_vych = vys_vych_csv.pendingFields()
            field_names_vys_vych = [field.name() for field in fields_vys_vych]
            selected_vys_vych = list(selected_vys_vych)
            features_list_vys_vych = [feature.attributes() for feature in selected_vys_vych]
            features_list_vys_vych.sort(key=lambda x: x[0])
            features_list_vys_vych = self.convert_to_strings(features_list_vys_vych)
            for fit in selected_vys_vych:
                list_of_vys_vych_ids.append(fit.id())

            field_names_vys_obn = NAMES_TAZ_TYP[:-2] + ['ZAHAJENI', 'TEZBA_CELKEM']
            features_list_vys_obn = []
            id_taz_typ = vys_obn_csv.fieldNameIndex("ID_TAZ_TYP")
            taz_typ_id = taz_typ_csv.fieldNameIndex("ID")
            for feature in selected_vys_obn:
                for taz_typ in selected_taz_typ:
                    if taz_typ.attributes()[taz_typ_id] == feature.attributes()[id_taz_typ]:
                        features_list_vys_obn.append(taz_typ.attributes()[:-2] +
                                                     feature.attributes()[1:3])
            features_list_vys_obn = self.convert_to_strings(features_list_vys_obn)

            fields_kat = []
            if kat_csv:
                fields_kat = kat_csv.pendingFields()
            field_names_kat = [field.name() for field in fields_kat]
            selected_kats =list(selected_kats)
            features_list_kat = [feature.attributes() for feature in
                    selected_kats]
            features_list_kat = self.convert_to_strings(features_list_kat)
            for fit in selected_kats:
                list_of_kats_ids.append(fit.id())

            etz_numbers = []
            for item in features_list_etz:
                etz_numbers.append(item[id_etz])

            features_list_drv = []
            for index in etz_numbers:
                expr = QgsExpression('ETZ_NUM ='+str(index))
                one_list = []
                if drv_csv:
                    one_list = drv_csv.getFeatures(QgsFeatureRequest(expr))

                one_list = list(one_list)
                another_list = [feature.attributes() for feature in one_list]
                for one_ft in another_list:
                    features_list_drv.append(one_ft)
                for each_item in one_list:
                    list_of_drvs_ids.append(each_item.id())

            features_list_drv = self.convert_to_strings(features_list_drv)
            fields_drv = []
            if drv_csv:
                fields_drv = drv_csv.pendingFields()
            field_names_drv = [field.name() for field in fields_drv]

            drv_numbers = []
            if drv_csv:
                idx = drv_csv.fieldNameIndex('DRV_NUM')
            for item in features_list_drv:
                drv_numbers.append(item[idx])

            features_list_pos = []
            for index in drv_numbers:
                expr = QgsExpression('DRV_NUM ='+str(index))
                one_list = []
                if pos_csv:
                    one_list = pos_csv.getFeatures(QgsFeatureRequest(expr))
                one_list = list(one_list)
                another_list = [feature.attributes() for feature in one_list]
                for one_ft in another_list:
                    features_list_pos.append(one_ft)
                for each_item in one_list:
                    list_of_poss_ids.append(each_item.id())

            features_list_pos = self.convert_to_strings(features_list_pos)
            fields_pos = []
            if pos_csv:
                fields_pos = pos_csv.pendingFields()
            field_names_pos = [field.name() for field in fields_pos]

            features_list_zal = []
            for index in etz_numbers:
                expr = QgsExpression('ETZ_NUM ='+str(index))
                one_list = []
                if zal_csv:
                    one_list = zal_csv.getFeatures(QgsFeatureRequest(expr))
                one_list = list(one_list)
                another_list = [feature.attributes() for feature in one_list]
                for one_ft in another_list:
                    features_list_zal.append(one_ft)
                for each_item in one_list:
                    list_of_zals_ids.append(each_item.id())

            features_list_zal = self.convert_to_strings(features_list_zal)
            fields_zal = []
            if zal_csv:
                fields_zal = zal_csv.pendingFields()
            field_names_zal = [field.name() for field in fields_zal]

            self.shower.show()
            self.shower.set_data(field_names, features_list,self.shower.tableWidget)
            self.shower.set_data(field_names_etz,
                    features_list_etz,self.shower.etaz)

            self.shower.set_data(field_names_drv,
                    features_list_drv,self.shower.drevina)
            self.shower.set_data(field_names_kat,
                    features_list_kat,self.shower.kategoria)
            self.shower.set_data(field_names_zal,
                    features_list_zal,self.shower.zalozene)
            self.shower.set_data(field_names_pos,
                    features_list_pos,self.shower.pos)
            self.shower.set_data(field_names_vys_vych,
                    features_list_vys_vych,self.shower.vychova)
            self.shower.set_data(field_names_vys_obn,
                    features_list_vys_obn,self.shower.obnova)
            self.shower.area.setText(str("%.2f" % (area/10000)))
            #self.shower.length.setText(str(round(length*2)/2))
        edit_pos = 0

    def select_output_folder_c(self):
        global pretty_folder
        pretty_folder = QFileDialog.getExistingDirectory(self.dlg, "Vyberte\
                 vystupny priecinok")
        self.dlg.lineEdit_2.setText(pretty_folder)
    
    def select_output_folder(self):
        global pretty_folder
        pretty_folder = QFileDialog.getExistingDirectory(self.save_all, "Vyberte\
                 vystupny priecinok")
        self.save_all.address.setText(pretty_folder)
        self.out_xml.address.setText(pretty_folder)
    
    def select_input_file(self):
        global pretty_name
        pretty_name = QFileDialog.getOpenFileName(self.dlg, "Vyberte vstupny\
        subor","","*.xml")[0]
        self.dlg.lineEdit.setText(pretty_name)

    def select_input_folder(self):
        global input_folder
        input_folder = QFileDialog.getExistingDirectory(self.open_all, "Vyberte vstupny\
        pricinok")
        self.open_all.address.setText(input_folder)
    

    def run(self):
        #if jedno je empty, tam Qmessage ze bug
        global pretty_name
        global pretty_folder
        
        """Run method that performs all the real work"""
        self.dlg.show()
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            if pretty_name != "" and pretty_folder != "":        


                res = convert_to_shp(pretty_name,pretty_folder)
                if res == 2:
                    self.Error_message("Nepodarilo sa otvorit subor")
                elif res == 3:
                    self.Error_message("Subor neobsahuje topograficke udaje")
                elif res == 0:
                    pass
                else:
                    self.Error_message("Ina chyba")

                    
                #podla return napise vysledok...
            else:
                self.Error_message("Nevybrane umiestnenie")


