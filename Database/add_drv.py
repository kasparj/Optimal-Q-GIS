# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DatabaseDialog
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

import os

from PyQt4 import QtGui, uic
from PyQt4.QtGui import QTableWidgetItem 
from PyQt4.QtCore import SIGNAL,QPyNullVariant,Qt

FORM_CLASS_5, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'add_drv.ui'))
class Add_drv(QtGui.QMainWindow, FORM_CLASS_5):
    def __init__(self, parent=None):
        """Constructor."""
        super(Add_drv, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def set_data(self,head,lines,where):
        horHeaders = []
        where.setRowCount(len(lines))
        where.setColumnCount(len(head))
        col = -1
        row = -1
        for i in lines:
            row+= 1
            col = -1
            for item in i:
                col += 1
                if isinstance(item,QPyNullVariant):
                    item = ""
                newitem = QTableWidgetItem(item)
                where.setItem(row,col,newitem)
        where.setHorizontalHeaderLabels(head)
        where.resizeColumnsToContents()
        where.resizeRowsToContents()
