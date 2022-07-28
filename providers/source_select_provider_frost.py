# -*- coding: utf-8 -*-
"""SensorThings API Plugin

Description
-----------

Derived class to select a Frost Source Provider.

Libraries/Modules
-----------------

- None.
    
Notes
-----

- None.


Author(s)
---------

- Created by Sandro Moretti on 09/02/2022.
  Dedagroup Spa.

Members
-------
"""

import os.path

from qgis.utils import iface

from qgis.gui import (QgsGui, 
                      QgsSourceSelectProvider, 
                      QgsAbstractDataSourceWidget)

from qgis.core import (Qgis,
                       QgsWkbTypes,
                       QgsSettings,
                       QgsProject, 
                       QgsApplication, 
                       QgsMessageLog, 
                       QgsVectorLayer,
                       QgsFeatureSource)


from qgis.PyQt import uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import pyqtSignal, Qt, QEventLoop, QTimer, QUrl, QUrlQuery
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog, QMenu, QToolButton

from SensorThingsAPI.providers.provider_frost import (__FROST_PROVIDER_NAME__, 
                                                      __FROST_DEFAULT_GEOM_TYPE__,
                                                      __FROST_PARAMETER_GEOM_TYPE__)

from SensorThingsAPI.providers.connection_frost import FrostConnection
from SensorThingsAPI.providers.connection_frost_dlg import FrostConnectionDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/datasource_dialog.ui'))
 
# 
#-----------------------------------------------------------
class FrostDataSourceOptionMenu(QMenu):
    
    actionTriggered = pyqtSignal(QAction)
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        action = self.actionAt(event.pos())
        if action:
            self.actionTriggered.emit(action)
        
    
    def setVisible(self, visible):
        # Don't hide the menu if action choosen
        if not visible and self.activeAction():
            return
        super().setVisible(visible) 
    
# 
#-----------------------------------------------------------
class FrostDataSourceWidget(QgsAbstractDataSourceWidget, FORM_CLASS):
    """UI widget class for load a Frost layer"""
    
    def __init__(self, parent, fl=Qt.WindowFlags(), widgetMode=0, options=None):
        """ Constructor """
        super().__init__(parent, fl, widgetMode)
        
        # setup widget
        self.setupUi(self)
        QgsGui.enableAutoGeometryRestore(self)
        
        # internal member
        self._options = options or {}
        self._connections = {}
        self._geomfilter = {}
        self._menuFilterProperties = None
        self._menuFilterGeometries = None
        
        # messages
        self._messages = {
            'Group': self.tr("Group"), 
            'Properties': self.tr("Properties"),
            'Count': self.tr("Count"),
            'HttpError': self.tr("HTTP request failed; response code"),
            'Loading': self.tr("Loading layer"),
            'Loaded': self.tr("Loaded layer"),
            'ConfirmRemove': self.tr("Confirm deletion"),
            'ConnRemove': self.tr('Are you sure you want to remove connection'),
            'Connecting': self.tr('Connecting endpoint'),
            'ReadRecords': self.tr("Read endpoint records")
        }
        self._messages = {**self._messages, **self._customizeInternalMessages()}
        
        # connection dalog
        self._conn_dlg = FrostConnectionDialog(self)
        self._conn_dlg.setModal(True)
        
        # set url combo
        self.cmbConnection.setEditable(False)
        self.cmbConnection.currentIndexChanged.connect(self.onConnectionChanged)
        
        
        # set table model
        model = QStandardItemModel(0, 3)
        model.setHeaderData(0, Qt.Horizontal, self._messages.get('Group'), Qt.DisplayRole)
        model.setHeaderData(1, Qt.Horizontal, self._messages.get('Properties'), Qt.DisplayRole)
        model.setHeaderData(2, Qt.Horizontal, self._messages.get('Count'), Qt.DisplayRole)
        self.tblLayes.setModel(model)
        self.tblLayes.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.tblLayes.setColumnWidth(0, 300)
        self.tblLayes.setColumnWidth(1, 300)
        sel_model = self.tblLayes.selectionModel()
        sel_model.selectionChanged.connect(self.onSelectionChanged)
        
        
        # set buttuns
        self.btnConnect.setDisabled(True)
        self.btnNew.setDisabled(False)
        self.btnModify.setDisabled(True)
        self.btnRemove.setDisabled(True)
        self.btnAdd.setDisabled(True)
        self.btnAddAll.setDisabled(True)
        self.btnFilterProperties.setDisabled(True)
        self.btnFilterGeometries.setDisabled(True)
        self.chkUniqueLayer.setDisabled(True)
        self.chkUniqueLayer.setChecked(False)
        self.chkOnMapExtent.setDisabled(False)
        self.chkOnMapExtent.setChecked(False)
        
        # signal connections
        self.btnConnect.clicked.connect(self.onConnect)
        self.btnNew.clicked.connect(self.onNewConnection)
        self.btnModify.clicked.connect(self.onModifyConnection)
        self.btnRemove.clicked.connect(self.onRemoveConnection)
        self.btnClose.clicked.connect(self.onClose)
        self.btnAdd.clicked.connect(self.onAdd)
        self.btnAddAll.clicked.connect(self.onAddAll)
        self.tblLayes.doubleClicked.connect(self.onTableViewDoubleClicked)
        self.chkUniqueLayer.stateChanged.connect(self._populateTableView)
        
        # load user defined connections
        self.loadConnections()
    
    def loadConnections(self):
        """Loads user defined connections"""
        # init
        s = QgsSettings()
        
        # read connection names
        self._connections = {}
        conn_name_list = str(s.value( f"{__FROST_PROVIDER_NAME__}/connections", '')).split(',')
        for conn_name in conn_name_list:
            # connection url
            url = str(s.value(f"{__FROST_PROVIDER_NAME__}/connection\\{conn_name}\\url", ''))
            # create new connection object 
            self._connections[conn_name] = FrostConnection(conn_name, url, parent=self)
    
        # read current connection and populate combo
        conn_name = str(s.value(f"{__FROST_PROVIDER_NAME__}/connection-selected", ''))
        self._setCurrentConnection(conn_name)
        
    def saveConnections(self):
        """Saves user defined connections"""
        # init
        s = QgsSettings()
        
        # save connection names
        s.setValue(f"{__FROST_PROVIDER_NAME__}/connections", ','.join(self._connections.keys()))
        
        # save connection properties
        for conn_name, conn in self._connections.items():
            # connection url
            s.setValue(f"{__FROST_PROVIDER_NAME__}/connection\\{conn_name}\\url", conn.url)
            
        # save current connection
        conn_name = self.cmbConnection.currentText() or ''
        s.setValue(f"{__FROST_PROVIDER_NAME__}/connection-selected", conn_name)
        
    def removeConnectionFromSettings(self, conn_name: str):
        """Remove a user defined connections from settings"""
        # init
        conn_name = conn_name or ''
        # Remove connection setting
        s = QgsSettings()
        s.remove(f"{__FROST_PROVIDER_NAME__}/connection\\{conn_name}\\url")
    
    def onClose(self):
        """On close dialog slot"""
        # save user defined connections
        self.saveConnections()
        # close window
        self.close()
    
    def onConnectionChanged(self, index):
        """On connectio changhed slot"""
        
        # init
        conn_enabled = index != -1
        
        # clear structures
        self._geomfilter = {}
        
        # disconnect connection
        conn_name = self.cmbConnection.itemText(index)
        if conn_name:
            conn_obj = self._connections[conn_name]
            if conn_obj:
                conn_obj.disconnect()
        
        # enable\disable connection buttons
        self.btnConnect.setEnabled(conn_enabled)
        self.btnModify.setEnabled(conn_enabled)
        self.btnRemove.setEnabled(conn_enabled)
        
        # clear table view
        model = self.tblLayes.model()
        model.removeRows(0, model.rowCount())
        
        self._menuFilterProperties = None
        self._menuFilterGeometries = None 
        
        self.chkUniqueLayer.setDisabled(True)
        self.chkUniqueLayer.setChecked(False)
        self.chkOnMapExtent.setChecked(False)
        self.btnFilterProperties.setDisabled(True)
        self.btnFilterGeometries.setDisabled(True)
        
    def onConnect(self, button):
        """On Connection slot"""
        # get current connection
        combo = self.cmbConnection
        index = combo.currentIndex()
        if index == -1:
            return
        conn_name = combo.itemText(index)
        conn_obj = self._connections[conn_name]
        if not conn_obj:
            return
            
        # clear table view
        model = self.tblLayes.model()
        model.removeRows(0, model.rowCount())
        
        try:    
            self._showProgressbar(
                    "{} ...".format(self._messages.get('Connecting')), 
                    '', Qgis.Info, wait_cursor=True)
                
            # connect
            map_extent = self.chkOnMapExtent.isChecked()
            if not conn_obj.connect(callback=self._showConnection, map_extent=map_extent):
                return
            
            #
            self._geomfilter = { geom: True for geom in conn_obj.geometry_types.keys() }
                
            # populate location layer table view
            self._populateTableView()
                
            # sort
            self.tblLayes.sortByColumn(0, Qt.AscendingOrder)
            
            # enable widgets
            enabled = model.rowCount() > 0
            self.chkUniqueLayer.setEnabled(enabled)
            self.btnAddAll.setEnabled(enabled)
        
        finally:
            # show result
            self._removeProgressbar()

    def onNewConnection(self):
        """On new connection slot"""
        # show connection detail dialog
        dlg = self._conn_dlg
        ret = dlg.showExec(loaded_conn_names=self._connections.keys())
        if ret == QDialog.Accepted:
            # add new connection
            self._connections[dlg.name] = FrostConnection(dlg.name, dlg.url, parent=self)
            self._setCurrentConnection(dlg.name)
            # save user defined connections
            self.saveConnections()
            
    def onModifyConnection(self):
        """On modify connection slot"""
        # get current connection
        combo = self.cmbConnection
        index = combo.currentIndex()
        if index == -1:
            return
            
        conn_name = combo.itemText(index)
        conn_obj = self._connections[conn_name]
        if not conn_obj:
            return
        
        # show connection detail dialog
        dlg = self._conn_dlg
        ret = dlg.showExec(loaded_conn_names= self._connections.keys(),
                           name=conn_obj.name, 
                           url=conn_obj.url)
        if ret == QDialog.Accepted:
            # modify connection
            conn_obj.modify(dlg.name, dlg.url)
            del self._connections[conn_name]
            self._connections[dlg.name] = conn_obj
            self._setCurrentConnection(dlg.name)
            # save user defined connections
            self.removeConnectionFromSettings(conn_name)
            self.saveConnections()
            
            
    def onRemoveConnection(self):
        """On remove connection slot"""
        # get current connection
        combo = self.cmbConnection
        index = combo.currentIndex()
        if index == -1:
            return
          
        # ask if remove
        conn_name = combo.itemText(index)
        ret = QMessageBox.question(
            self, 
            self._messages.get('ConfirmRemove'),
            "{} '{}'?".format(self._messages.get('ConnRemove'), conn_name), 
            QMessageBox.Yes, QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return
        
        # remove connection 
        del self._connections[conn_name]
        combo.removeItem(index)    
        combo.setCurrentIndex(combo.count() - 1)
        # save user defined connections
        self.removeConnectionFromSettings(conn_name)
        self.saveConnections()
    
    def onSelectionChanged(self, selected, _):
        """On table change selection slot"""
        # get item data
        indexes = selected.indexes()
        self.btnAdd.setDisabled(not indexes)
        
    def onTableViewDoubleClicked(self, index):
        """On table double click slot"""
        self.onAdd( )
      
      
    def onAdd(self):
        # get selection model
        selection = self.tblLayes.selectionModel()
        if selection is None:
            return
        
        # get selected row
        indexes = selection.selectedRows()
        if not indexes:
            return
        index = indexes[0]
        
        # get location group data
        model = self.tblLayes.model()
        grp_data = model.data(index, Qt.UserRole)
        if not grp_data:
            return
        
        grp_name = grp_data.get('name', 'unknown')
        grp_url = grp_data.get('url', '')
        
        try:
            # show message
            self._showProgressbar(
                "{} {} ...".format(self._messages.get('Loading'), grp_name), 
                '', Qgis.Info, wait_cursor=True)
      
            # close dialog
            self.onClose()
        
            # create new layer
            self._createLayer(grp_url, grp_name)
            
        finally:
            # show result
            self._removeProgressbar()
            
            QTimer.singleShot(500, lambda self=self: self._showProgressbar(
                self._messages.get('Loaded'), '', Qgis.Success, duration=2))
            
            # repaint canvas
            QTimer.singleShot(500, lambda: iface.mapCanvas().refreshAllLayers())
    
    
    def onAddAll(self):
        """Add new layer slot"""
         
        try:
            # show message
            self._showProgressbar(
                "{} ...".format(self._messages.get('Loading')), '', Qgis.Info, wait_cursor=True)
            
            # close dialog
            self.onClose()
        
            # loop table items
            model = self.tblLayes.model()
            for row in range(model.rowCount()):
                index = model.index(row, 0)
                
                # get location group data
                grp_data = model.data(index, Qt.UserRole)
                if not grp_data:
                    continue
                grp_name = grp_data.get('name', 'unknown')
                grp_url = grp_data.get('url', '')
                
                # show message
                self._showProgressbar(
                    "{} {} ...".format(self._messages.get('Loading'), grp_name), '', Qgis.Info, wait_cursor=True)
                
                # create new layer
                self._createLayer(grp_url, grp_name)
                
                #
                self._removeProgressbar()
                QgsApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            
        finally:
            # show result
            self._removeProgressbar()
            
            QTimer.singleShot(500, lambda self=self: self._showProgressbar(
                self._messages.get('Loaded'), '', Qgis.Success, duration=2))
            
            # repaint canvas
            QTimer.singleShot(500, lambda: iface.mapCanvas().refreshAllLayers())
            
    
    def _showConnection(self, num, count):
        """Show connection status"""
        # clear message bar
        msgBar = iface.messageBar()
        msgBar.clearWidgets()
        msgBar.pushMessage('', "{}: {}\\{}".format(self._messages.get('ReadRecords'), num, count), Qgis.Info)
        msgBar.repaint()
    
    def _showProgressbar(self, msg, title, level, wait_cursor=False, duration=0):
        """Show message progress bar"""
        title = str(title)
        
        # clear message bar
        iface.messageBar().clearWidgets()
        
        # set message bar
        iface.messageBar().pushMessage(title, msg, level, duration)
        iface.messageBar().repaint()
        
        # override cursor 
        if wait_cursor:
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            QgsApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
    
        
    def _removeProgressbar(self):
        """Remove message progress bar"""
        # restore cursor
        QgsApplication.restoreOverrideCursor()
        # remove widget from message bar
        iface.messageBar().clearWidgets()
    
    def _setCurrentConnection(self, conn_name: str):
        """Set current conection by name"""
        #get connection object
        conn = self._connections.get(conn_name, None)
        if conn is None:
            return
            
        # set connection combo
        combo = self.cmbConnection
        try:
            combo.setUpdatesEnabled(False)
            combo.clear()
            combo.addItems(self._connections.keys())
            combo.model().sort(0, Qt.AscendingOrder)
        finally:
            combo.setUpdatesEnabled(True)
               
        index = combo.findText(conn_name)
        if index != -1:
            combo.setCurrentIndex(index)

    def _populateTableView(self):
        """Populate location layer table group by 
           properties or as unique layer"""
        # get current connection
        conn_name = str(self.cmbConnection.currentText())
        conn_obj = self._connections[conn_name]
        if not conn_obj:
            return
        
        # check if connected
        if not conn_obj.connected:
            return
        
        # create properties filter menu
        group_list = []
        if self.chkUniqueLayer.isChecked():
            # unique layer for all locations
            group_list = conn_obj.uniqueGroup()
            # disable filter properties button
            self.btnFilterProperties.setEnabled(False)
            
        else:
            # group location by properties
            group_list = conn_obj.groupLocations()
            
            # populate filter property menu
            self.btnFilterProperties.setEnabled(True)
            self._menuFilterProperties = FrostDataSourceOptionMenu(self)
            self._menuFilterProperties.actionTriggered.connect(self.onMenuFilterProperties)
            for index, (prop_name, prop) in enumerate(conn_obj.properties.items()):
                action = self._menuFilterProperties.addAction(prop_name)
                action.setData(index)
                action.setCheckable(True)
                action.setChecked(not prop.get('skip', False))
                
            self.btnFilterProperties.setMenu(self._menuFilterProperties)
            self.btnFilterProperties.setPopupMode(QToolButton.InstantPopup)
            
        # create geometry filter menu
        if len(self._geomfilter) > 1:
            def_geom_type = QgsWkbTypes.displayString(__FROST_DEFAULT_GEOM_TYPE__)
            self.btnFilterGeometries.setEnabled(True)
            self._menuFilterGeometries = FrostDataSourceOptionMenu(self)
            self._menuFilterGeometries.actionTriggered.connect(self.onMenuFilterGeometries)
            for geom_type, checked in self._geomfilter.items():
                action_text = f"{geom_type} (default)" if geom_type == def_geom_type else geom_type
                action = self._menuFilterGeometries.addAction(action_text)
                action.setData(geom_type)
                action.setCheckable(True)
                action.setChecked(checked)
                
            self.btnFilterGeometries.setMenu(self._menuFilterGeometries)
            self.btnFilterGeometries.setPopupMode(QToolButton.InstantPopup)
            
        # populate table view
        model = self.tblLayes.model()
        model.removeRows(0, model.rowCount())
        for group in group_list:
            itemName = QStandardItem(group.get('name', '???'))
            itemName.setData(group, Qt.UserRole)
            itemProps = QStandardItem(group.get('properties', ''))
            itemCount = QStandardItem()
            itemCount.setData(group.get('count', 0), Qt.EditRole)
            model.appendRow([ itemName, itemProps, itemCount ])
            
        # selection
        if model.rowCount() == 1:
            self.tblLayes.selectRow(0)
            
    def onMenuFilterProperties(self, action):
        """Filter properties"""
        # init
        if not self._menuFilterProperties:
            return
            
        # get current connection
        conn_name = str(self.cmbConnection.currentText())
        conn_obj = self._connections[conn_name]
        if not conn_obj:
            return
            
        # loop filter menu actions
        prop_list = []
        for a in self._menuFilterProperties.actions():
            if action.data() == a.data():
                # correct action state
                a.setChecked(action.isChecked())
            if a.isChecked():
                prop_list.append(a.text())
                
        # repopulate table view
        conn_obj.setAllowedGroupProperties(prop_list)
        self._populateTableView()
        
        
    def onMenuFilterGeometries(self, action):
        """Filter geometries"""
        if not self._menuFilterGeometries:
            return
        # check / uncheck geom type
        geom_type = action.data()
        self._geomfilter[geom_type] = action.isChecked()
        
        
    def _createLayer(self, url, lay_name):
        """Creates new layer"""
        # init
        geom_type_list = []
        def_geom_type = QgsWkbTypes.displayString(__FROST_DEFAULT_GEOM_TYPE__)
        
        # get geometry types to filter
        for geom_type, checked in self._geomfilter.items():
            if checked:
                geom_type_list.append(geom_type)
        
        if not geom_type_list:
            geom_type_list = [def_geom_type]
        
        # loop geometry types
        for geom_type in geom_type_list:
            # compose url
            url_with_geom = QUrl(url)
            query = QUrlQuery(url_with_geom.query())
            query.addQueryItem(__FROST_PARAMETER_GEOM_TYPE__, geom_type)
            url_with_geom.setQuery(query)
            
            # create new layer
            if geom_type != def_geom_type:
                lay_name_ext = f"{lay_name}__{geom_type}"
                layer = QgsVectorLayer(url_with_geom.toString(), lay_name_ext, 'frost')
                # check if empty
                if layer.hasFeatures() == QgsFeatureSource.NoFeaturesAvailable:
                    continue
            else:
                layer = QgsVectorLayer(url_with_geom.toString(), lay_name, 'frost')
            
            # add the layer to the Layers panel
            QgsProject.instance().addMapLayer(layer) 
            
            # set layer style
            self._applyLayerStyle(layer)
            
            # log message
            QgsMessageLog.logMessage(
                "{}: {}".format(self._messages.get('Loaded'), lay_name),
                __FROST_PROVIDER_NAME__,
                Qgis.Info)
        
    def _applyLayerStyle(self, layer):
        """Apply style to Frost layer"""
        return

    
    def _customizeInternalMessages(self):
        """Customize internal messages"""
        return {} 
    
    
# 
#-----------------------------------------------------------
class FrostSourceSelectProvider(QgsSourceSelectProvider):
    """Frost Source Select Provider"""
    
    def providerKey(self):
        return __FROST_PROVIDER_NAME__

    def text(self):
        return "Layer Frost"

    def icon(self):
        icon_path = ':/plugins/SensorThingsAPI/icons/frost-layer-icon.png'
        return QIcon(icon_path)

    def createDataSourceWidget(self, parent, fl, widgetMode):
        return FrostDataSourceWidget(parent, fl, widgetMode)

    def ordering(self):
        return QgsSourceSelectProvider.OrderLocalProvider + 9000;



# 
#-----------------------------------------------------------
def register_frost_sourceselect_provider(select_provider=None) -> bool:
    """Register Frost source selector"""
    registry = QgsGui.sourceSelectProviderRegistry()
    if registry.providerByName(__FROST_PROVIDER_NAME__) is None:
        if select_provider is None:
            select_provider = FrostSourceSelectProvider()
        registry.addProvider(select_provider)
    return registry.providerByName(__FROST_PROVIDER_NAME__) is not None

    
def unregister_frost_sourceselect_provider():
    """Unregister Frost source selector"""
    registry = QgsGui.sourceSelectProviderRegistry()
    provider = registry.providerByName(__FROST_PROVIDER_NAME__)
    if provider:
        return registry.removeProvider(provider)
    return False
    
    