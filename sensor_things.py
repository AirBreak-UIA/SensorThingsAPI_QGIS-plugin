# -*- coding: utf-8 -*-
"""SensorThings API Plugin class

Description
-----------

The main working code of the plugin. Contains all the initialization
of the plugin interfaces and commands.

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

from qgis.PyQt.QtCore import qVersion, Qt, QObject, QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.PyQt.QtGui import QIcon

# import plugin modules
from SensorThingsAPI import __QGIS_PLUGIN_NAME__
from SensorThingsAPI.log.logger import QgisLogger as logger
from SensorThingsAPI.sensor_things_location_dlg import SensorThingsLocationDialog
from SensorThingsAPI.feature_selection_tool import FeatureSelectionTool
from SensorThingsAPI.sensor_things_select_provider import SensorThingsFrostSourceSelectProvider

from SensorThingsAPI.icons.resources import * #@UnusedWildImport

# import Server Frost data provider 
from SensorThingsAPI.providers.provider_frost import (
    register_frost_data_provider, 
    unregister_frost_data_provider,
    __FROST_PROVIDER_NAME__
)

# import Server Frost provider selector
from SensorThingsAPI.providers.source_select_provider_frost import (
    register_frost_sourceselect_provider, 
    unregister_frost_sourceselect_provider
)


# 
#-----------------------------------------------------------
class SensorThingsPlugin(QObject):
    """QGIS Air Brek Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # call parent cunstructor
        QObject.__init__(self)
        
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # initialite logger
        logger.name = __QGIS_PLUGIN_NAME__

        # initialize locale
        self.locale = QSettings().value('locale/userLocale')
        if self.locale:
            self.locale = self.locale[0:2]
            locale_path = os.path.join(
                self.plugin_dir,
                'i18n',
                'SensorThingsAPI_{}.qm'.format(self.locale))
    
            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)
                if qVersion() > '4.3.3':
                    QCoreApplication.installTranslator(self.translator)
        else:
            self.locale = ''

        self.menu_name_plugin = "{} Plugin".format(__QGIS_PLUGIN_NAME__)
        
        # menu
        self.menu = None
        
        # toolbar
        self.toolbar = None
        
        # actions
        self.frost_datasource_action = None
        self.frost_identify_action = None
        
        # map tool
        self.featureSelectionTool =  None
        
        # dialogs
        self.frostDataSourceDlg = None
        self.postazionedlg = None
        
        # Create and register Frost Server providers
        if register_frost_data_provider():
            logger.log(logger.Level.Info, self.tr("Registered 'Frost' provider"))
            
        select_provider = SensorThingsFrostSourceSelectProvider()
        if register_frost_sourceselect_provider(select_provider):
            logger.log(logger.Level.Info, self.tr("Registered data source selector for 'Frost' provider"))
    

    def initGui(self):
        """Initialize plugin resources"""
        
        # create Frost Data Source Dialog
        self.frostDataSourceDlg =\
            SensorThingsFrostSourceSelectProvider().createDataSourceWidget(
                self.iface.mainWindow(), fl=Qt.WindowFlags(), widgetMode=0)
        self.frostDataSourceDlg.setModal(True)
        
        # create Postazione info dialog
        self.postazionedlg = SensorThingsLocationDialog(self, parent=self.iface.mainWindow())
        #########self.postazionedlg.setModal(True)
        
        # create action to show Frost data source dialog
        icon_path = ':/plugins/SensorThingsAPI/icons/frost-layer-icon.png'
        self.frost_datasource_action = QAction(
            QIcon(icon_path), self.tr("Upload layer from remote server"), self.iface.mainWindow())
        
        # connect the action handler
        self.frost_datasource_action.triggered.connect(lambda: self.frostDataSourceDlg.show())
        self.iface.insertAddLayerAction(self.frost_datasource_action)
        
        # add action to toolbar
        self.iface.dataSourceManagerToolBar().addAction(self.frost_datasource_action)
        
        # Create action to show a postazione info
        icon_path = ':/plugins/SensorThingsAPI/icons/action-identify-icon.png'
        self.frost_identify_action = QAction(
            QIcon(icon_path), self.tr("Show location information"), self.iface.mainWindow())
        
        # connect the action handler
        self.frost_identify_action.triggered.connect(self.onSelectPostazioneFeature)
        
        # create plugin menu
        menu_bar = self.iface.mainWindow().menuBar()
        self.menu = QMenu(__QGIS_PLUGIN_NAME__, menu_bar)
        menu_bar.insertMenu(menu_bar.actions()[-1], self.menu)
        
        self.menu.addAction(self.frost_datasource_action)
        self.menu.addSeparator()
        self.menu.addAction(self.frost_identify_action)
        
        # create plugin toolbar
        self.toolbar = self.iface.addToolBar(__QGIS_PLUGIN_NAME__)
        self.toolbar.setToolTip(self.tr('SensorThings API plugin command toolbar'))
        self.toolbar.addAction(self.frost_datasource_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.frost_identify_action)
        
        
    def unload(self):
        """Unload plugin resources"""
        
        # deselect map tool
        canvas = self.iface.mapCanvas()
        if self.featureSelectionTool:
            canvas.unsetMapTool(self.featureSelectionTool)
        
        # Unregister Frost Server providers
        if unregister_frost_sourceselect_provider():
            logger.log(logger.Level.Info, self.tr("Unregistered data source selector for 'Frost' provider"))
        
        if unregister_frost_data_provider():
            logger.log(logger.Level.Info, self.tr("Unregistered 'Frost' provider"))
            
        # Remove dialogs
        self.frostDataSourceDlg.close()
        self.frostDataSourceDlg.deleteLater()
        self.frostDataSourceDlg = None
        
        self.postazionedlg.close()
        self.postazionedlg.deleteLater()
        self.postazionedlg = None
        
        
        # Remove the plugin menu item and icon
        self.iface.removeAddLayerAction(self.frost_datasource_action)
        self.iface.dataSourceManagerToolBar().removeAction(self.frost_datasource_action)
        
        if self.menu:
            self.menu.deleteLater()
        self.menu = None
        
        del self.toolbar
        self.toolbar = None
        
        self.frost_identify_action = None
        self.frost_datasource_action = None
          
        
    def onSelectPostazioneFeature(self, checked):
        """Callback method on selected location feature"""
        
        # create and set map tool
        canvas = self.iface.mapCanvas()
        self.featureSelectionTool = FeatureSelectionTool(canvas)
        self.featureSelectionTool.featuresIdentified.connect(self.postazioniShow)
        canvas.setMapTool(self.featureSelectionTool)
        logger.msgbar(
            logger.Level.Info, 
            self.tr("Select a location"), 
            title=__QGIS_PLUGIN_NAME__,
            clear=True)
        
    def postazioniShow(self, layer, fids):
        """Slot to show Postazioni dialog"""
        
        # check if Frost layer
        provider = layer.dataProvider()
        if provider.name() != __FROST_PROVIDER_NAME__:
            logger.msgbar(
                logger.Level.Warning, 
                "{}, <b>{}</b>".format(
                    self.tr("Selected entity has an illegal data source"),
                    self.tr("use a 'SensorThing' vector layer")
                ),
                title=__QGIS_PLUGIN_NAME__)
            return
        
        # check if features sellected
        fids = fids or []
        if len(fids) == 0:
            return
        fid = fids[0]
        
        # show Postazione dialog 
        self.postazionedlg.show(layer, fid, fids)
        
    