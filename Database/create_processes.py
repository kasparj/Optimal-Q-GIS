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

from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow
from PyQt5.QtCore import Qt

FORM_CLASS_11, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'create_processes.ui'))
class CreateProcesses(QMainWindow, FORM_CLASS_11):
    def __init__(self, parent=None):
        """Constructor."""
        super(CreateProcesses, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.setWindowFlags(Qt.WindowStaysOnTopHint)
