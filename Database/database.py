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

#!!!!!!
#pyrcc4 -o resources_rc.py resources.qrc

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QMessageBox
from PyQt4.QtGui import QTableWidgetItem 
from PyQt4.QtCore import SIGNAL,QPyNullVariant
from PyQt4 import QtGui, QtCore
from qgis.utils import iface
from qgis.core import QgsFeatureRequest
import resources_rc
from database_dialog import DatabaseDialog
from show_atts import ShowAtts
import os.path
from converter import convert_to_shp
import sys 

from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
pretty_name = ""
pretty_folder = ""



class Database:

    def __init__(self, iface):
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
        self.shower = ShowAtts()
        self.shower.refresh.clicked.connect(self.show_atts)       

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Optimal')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Database')
        self.toolbar.setObjectName(u'Database')

        self.dlg.lineEdit.clear()
        self.dlg.pushButton.clicked.connect(self.select_input_file)

        self.dlg.lineEdit_2.clear()
        self.dlg.pushButton_2.clicked.connect(self.select_output_folder)

        
        

        
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

        icon_path = ':/plugins/Database/icon_convert.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Convert format'),
            callback=self.run,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/Database/icon_tables.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Show attributes'),
            callback=self.show_atts,
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

    
    
    def show_atts(self):
        #vybrana vrstva
        lyr = iface.activeLayer()


        #Vyberieme si potrebne vrsty podla mena - pozor na zmeny!
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layerMap.iteritems():
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

#kontorla ci naslo vsetky co treba
#kontorla ci je aj vybrata feature
        if not lyr:
            QMessageBox.information(self.iface.mainWindow(),"Chyba",
            "Ziadna vybrana vrstva")
        else: 
            fields = lyr.pendingFields()#vyberieme vsetky mena atributov
            features = lyr.selectedFeatures()#vyberieme vybrate prvky
            if features != []:

                field_names = [field.name() for field in fields]#vytvorim
                #zahlavie
                #vytvorim tabulku vlastnosti
                features_list = [feature.attributes() for feature in features]
            
                idx = lyr.fieldNameIndex("PSK_NUM") #index parametru PSK_NUM 
                if idx == -1:
                    psk_numb = "xX!48p"
                else:
                    psk_numb = features_list[0][idx] 
            else:
                psk_numb = -1
                field_names = []
                features_list = []
            
            
            expr = QgsExpression("PSK_NUM ="+ str(psk_numb))
            selected_etzs = etz_csv.getFeatures(QgsFeatureRequest(expr))
            selected_kats = kat_csv.getFeatures(QgsFeatureRequest(expr))
            

            fields_etz = etz_csv.pendingFields()
            field_names_etz = [field.name() for field in fields_etz]
            features_list_etz = [feature.attributes() for feature in selected_etzs]
            
            
            fields_kat = kat_csv.pendingFields()
            field_names_kat = [field.name() for field in fields_kat]
            features_list_kat = [feature.attributes() for feature in
                    selected_kats]
            
            
            etz_numbers = []
            idx = etz_csv.fieldNameIndex('ETZ_NUM')
            for item in features_list_etz:
                etz_numbers.append(item[idx])
           
            
            features_list_drv = []
            for index in etz_numbers:
                expr = QgsExpression('ETZ_NUM ='+str(index))
                one_list = drv_csv.getFeatures(QgsFeatureRequest(expr))
                another_list = [feature.attributes() for feature in one_list]
                for one_ft in another_list:
                    features_list_drv.append(one_ft)
            
            fields_drv = drv_csv.pendingFields()
            field_names_drv = [field.name() for field in fields_drv]
            
                
            drv_numbers = []
            idx = drv_csv.fieldNameIndex('DRV_NUM')
            for item in features_list_drv:
                drv_numbers.append(item[idx])
            
            
            features_list_pos = []
            for index in drv_numbers:
                expr = QgsExpression('DRV_NUM ='+str(index))
                one_list = pos_csv.getFeatures(QgsFeatureRequest(expr))
                another_list = [feature.attributes() for feature in one_list]
                for one_ft in another_list:
                    features_list_pos.append(one_ft)
            
            fields_pos = pos_csv.pendingFields()
            field_names_pos = [field.name() for field in fields_pos]
            
            
            
            features_list_zal = []
            for index in etz_numbers:
                expr = QgsExpression('ETZ_NUM ='+str(index))
                one_list = zal_csv.getFeatures(QgsFeatureRequest(expr))
                another_list = [feature.attributes() for feature in one_list]
                for one_ft in another_list:
                    features_list_zal.append(one_ft)
            
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
        #result = self.shower.exec_()

    
    def select_output_folder(self):
        global pretty_folder
        pretty_folder = QFileDialog.getExistingDirectory(self.dlg, "Vyberte\
                 vystupny priecinok")
        self.dlg.lineEdit_2.setText(pretty_folder)
    
    
    def select_input_file(self):
        global pretty_name
        pretty_name = QFileDialog.getOpenFileName(self.dlg, "Vyberte vstupny\
        subor","","*.xml")
        self.dlg.lineEdit.setText(pretty_name)

    

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
                if res == 0:
                    QMessageBox.information(self.iface.mainWindow(),"Vysledok",
                    "Uspesne doslo")
                elif res == 2:
                    QMessageBox.information(self.iface.mainWindow(),"Vysledok",
                    "Nepodarilo sa otvorit subor")
                elif res == 3:
                    QMessageBox.information(self.iface.mainWindow(),"Vysledok",
                    "Subor neobsahuje topograficke udaje")
                else:
                    QMessageBox.information(self.iface.mainWindow(),"Vysledok",
                    "Ina chyba")

                    
                #podla return napise vysledok...
            else:
                QMessageBox.information(self.iface.mainWindow(),"Vysledok",
                    "Navybrane umiestnenia")
                #new_window = My_App()
        #new_window.show


