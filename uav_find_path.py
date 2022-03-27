# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UAVFindPath
                                 A QGIS plugin
 -
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-06-14
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Vladimir Voronin
        email                : vladimirvoron7@gmail.com
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
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
import qgis
from PyQt5.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMainWindow, QDialog
from qgis.core import *
from qgis.gui import *
import os.path
import copy

from ModuleInstruments.Converter import Converter

import PyQt5
# Initialize Qt resources from file resources.py
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData, check_if_FindPathData_is_ok
from .resources import *
# Import the code for the dialog
from .uav_find_path_dialog import UAVFindPathDialog

import time

from algorithms import RandomizedRoadmapMethod, RandomizedRoadmapGridMethod, RRTDirectMethod, DijkstraMethod, \
    AStarMethod, DStarMethod, APFMethod, BugMethod, FormerMethod


class UAVFindPath:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An abstract instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS abstract
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'UAVFindPath_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&UAVFindPath')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        # parametrs
        self.project = None
        self.obstacle_layer = None
        self.start_point = None
        self.target_point = None
        self.path_to_save_layers = None
        self.algorithm_dict = {}

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
        return QCoreApplication.translate('UAVFindPath', message)

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
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/uav_find_path/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Find path'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&UAVFindPath'),
                action)
            self.iface.removeToolBarIcon(action)

    def choose_directory(self):
        self.path_to_save_layers = QFileDialog.getExistingDirectory(self.dlg, caption='Select folder')
        self.dlg.textEdit_save_folder.setText(self.path_to_save_layers)

    def set_obstacle_layer(self):
        layers = self.project.layerTreeRoot().children()
        selected_layer_index = self.dlg.comboBox_select_obstacles.currentIndex() - 1
        if selected_layer_index >= 0:
            self.obstacle_layer = layers[selected_layer_index].layer()

    def point_button_clicked(self, number_of_point):
        dial = QDialog(None)
        dial.show()
        dial.setModal(True)
        if number_of_point == 1:
            text_x = self.dlg.textEdit_start_point_x
            text_y = self.dlg.textEdit_start_point_y
        elif number_of_point == 2:
            text_x = self.dlg.textEdit_target_point_x
            text_y = self.dlg.textEdit_target_point_y
        canvas = QgsMapCanvas()
        canvas.show()
        layer = self.obstacle_layer
        canvas.setCanvasColor(Qt.white)
        canvas.enableAntiAliasing(True)
        canvas.setLayers([layer])
        canvas.setExtent(layer.extent())

        emit_point = QgsMapToolEmitPoint(canvas)
        canvas.setMapTool(emit_point)

        def display(pt):
            text_x.setText(str(pt.x()))
            text_y.setText(str(pt.y()))
            canvas.destroy()
            dial.done(1)

        emit_point.canvasClicked.connect(display)

        result = dial.exec()
        if result:
            pass

    def update_combo_box_layers(self):
        layers = self.project.layerTreeRoot().children()
        self.dlg.comboBox_select_obstacles.clear()
        self.dlg.comboBox_select_obstacles.addItem("")
        self.dlg.comboBox_select_obstacles.addItems([layer.name() for layer in layers])

    def press_run(self):
        debug_log = DebugLog()
        debug_log.info("Button 'Run' was pressed")

        # Reading data from interface
        self.start_point = QgsGeometry.fromPointXY(
            QgsPointXY(float(self.dlg.textEdit_start_point_x.toPlainText()),
                       float(self.dlg.textEdit_start_point_y.toPlainText())))
        self.target_point = QgsGeometry.fromPointXY(
            QgsPointXY(float(self.dlg.textEdit_target_point_x.toPlainText()),
                       float(self.dlg.textEdit_target_point_y.toPlainText())))

        debug_log.info(f"start_point x = {float(self.dlg.textEdit_start_point_x.toPlainText())}")
        debug_log.info(f"start_point y = {float(self.dlg.textEdit_start_point_y.toPlainText())}")
        debug_log.info(f"target_point x = {float(self.dlg.textEdit_target_point_x.toPlainText())}")
        debug_log.info(f"target_point y = {float(self.dlg.textEdit_target_point_y.toPlainText())}")

        self.path_to_save_layers = self.dlg.textEdit_save_folder.toPlainText()

        debug_log.info(f"path to save layers = {self.path_to_save_layers}")

        layer_to_algortithm = QgsVectorLayer(self.obstacle_layer.source(), self.obstacle_layer.name(),
                                             self.obstacle_layer.providerType())
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(layer_to_algortithm, self.project)

        debug_log.info(f"len of source_list_of_geometry_obstacles = {len(source_list_of_geometry_obstacles)}")

        find_path_data = FindPathData(self.project, self.start_point, self.target_point,
                                      layer_to_algortithm,
                                      self.path_to_save_layers, self.dlg.checkBox_create_debug_layers.isChecked(),
                                      source_list_of_geometry_obstacles)

        if check_if_FindPathData_is_ok(find_path_data):
            debug_log.info("FindPathData is ok!")
            my_algorithm = self.algorithm_dict[self.dlg.comboBox_select_search_method.currentText()]

            current_algorithm = my_algorithm(find_path_data, debug_log)
            current_algorithm.run()
            current_algorithm.visualize()
            self.dlg.textEdit_debug_info.setText(current_algorithm.debuglog.get_info())
            # clean resources
            self.update_combo_box_layers()
            self.dlg.comboBox_select_obstacles.setCurrentIndex(0)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start:
            self.first_start = False
            self.dlg = UAVFindPathDialog()
            # button logic
            self.dlg.pushButton_start_point.clicked.connect(lambda: self.point_button_clicked(1))
            self.dlg.pushButton_target_point.clicked.connect(lambda: self.point_button_clicked(2))
            self.dlg.comboBox_select_obstacles.currentIndexChanged.connect(lambda: self.set_obstacle_layer())
            self.dlg.pushButton_save_folder.clicked.connect(lambda: self.choose_directory())
            self.dlg.pushButton_run.clicked.connect(lambda: self.press_run())

        self.project = QgsProject.instance()

        # dict of algorithms
        self.algorithm_dict = {
            'Randomized Roadmap Grid Method': RandomizedRoadmapGridMethod.RandomizedRoadmapGridMethod,
            'RRT method': RRTDirectMethod.RRTDirectMethod,
            'A* Method': AStarMethod.AStarMethod,
            'D* Method': DStarMethod.DStarMethod,
            'APF Method': APFMethod.APFMethod,
            'Dijkstra method': DijkstraMethod.DijkstraMethod,
            'Bug Method': BugMethod.BugMethod,
            'Former Method': FormerMethod.FormerMethod}
        # add layers to "select layer"
        self.update_combo_box_layers()

        # add search methods to "select search methods
        self.dlg.comboBox_select_search_method.clear()
        self.dlg.comboBox_select_search_method.addItems(self.algorithm_dict.keys())
        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
            pass
