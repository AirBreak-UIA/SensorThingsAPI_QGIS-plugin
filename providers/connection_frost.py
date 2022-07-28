# -*- coding: utf-8 -*-
"""SensorThings API Plugin

Description
-----------

Derived class to implement a Frost Provider.

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
import json
import traceback
import urllib.parse
import pandas as pd

from qgis.utils import iface
from qgis.core import (Qgis, 
                       QgsWkbTypes, 
                       QgsApplication, 
                       QgsProject,
                       QgsMessageLog,  
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform) 
from qgis.PyQt.QtCore import Qt, QObject, QEventLoop, QUrl, QUrlQuery
from qgis.PyQt.QtWidgets import QMessageBox

from SensorThingsAPI.providers.provider_frost import __FROST_PROVIDER_NAME__, FrostProvider

# 
#-----------------------------------------------------------
class FrostConnectionError(Exception):
    """Frost connection exception"""

# 
#-----------------------------------------------------------
class FrostConnection(QObject):
    """ Class to manage connection to Frost server """
    
    def __init__(self, name: str, url: str, parent: QObject=None):
        """Constructor"""
        super().__init__(parent)
        # connection data
        self._name = str(name or '')
        self._url = str(url or '').strip()
        self._url_ext = ''
        self._loc_data = []
        self._connected = False
        self._map_extent = False
        # grouping
        self._group_properties = {}
        self._group_rows = []
        # geometry types
        self._geom_types = {}
    
    @property
    def name(self):
        """ Returns the connection name """
        return self._name
    
    @property
    def url(self):
        """ Returns the connection url """
        return self._url
    
    @property
    def connected(self):
        """ Returns if connected """
        return self._connected
        
    @property
    def properties(self):
        """ Returns the list of grouping properties """
        return self._group_properties
    
    @property
    def geometry_types(self):
        """ Returns geometry types found """
        return self._geom_types
    
    def disconnect(self):
        """Disconnect"""
        self._connected = False
        self._loc_data = []
        self._geom_types = {}
        
    def modify(self, name: str=None, url: str=None):
        """Modify data"""
        if name:
            self._name = name
        if url:
            self._url = url
        
    def setAllowedGroupProperties(self, prop_list: list):
        """Set the allowed properties for location grouping"""
        prop_list = prop_list or []
        for prop_name, prop in self._group_properties.items():
            prop['skip'] = prop_name not in prop_list
    
    def connect(self, callback=None, map_extent=False):
        """Connect to server Frost"""
        try:
            # init
            self._connected = False
            self._map_extent = map_extent
            self._loc_data = []
            self._group_properties = {}
            
            # format url
            if not self._url:
                return False
                
            url_obj = urllib.parse.urlparse(self._url)
            url = url_obj._replace(query='', fragment='').geturl()
            if not url:
                return False
            self._url = url
            
            # add extent filter
            if map_extent:
                self._url_ext = self._addExtentFilter(self._url_ext)
            else:
                self._url_ext = self._url
        
            # set wait cursor
            QgsApplication.setOverrideCursor(Qt.WaitCursor)
            QgsApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            
            # get data
            self._loc_data = FrostProvider.requestData(self._url_ext, callback=callback)        
            self._connected = True
            
            # get geometry types
            self._getGeomTypes()
            
            return True
            
        except Exception as ex:
            QgsMessageLog.logMessage(traceback.format_exc(), __FROST_PROVIDER_NAME__, Qgis.Critical)
            QMessageBox.critical(iface.mainWindow(), self.tr("Connection"), str(ex))
            return False
        
        finally:
            # restore cursor
            QgsApplication.restoreOverrideCursor()
    
    def uniqueGroup(self, prop_text=None):
        """Creates an unique group with all locations"""
        # init
        self._group_rows = []
        
        if self._loc_data:
            prop_text = prop_text or ''
            
            self._group_rows = [{
                'name': self.tr('Locations'),
                'properties': prop_text,
                'count': "{0}/{0}".format(len(self._loc_data)),
                'url': self._url_ext
            }]
            
        # return groups
        return self._group_rows
            
    def groupLocations(self):
        """Groups loacation by properties attributes"""
        # init
        self._group_rows = []
        if not self._loc_data:
            return []
        
        try:
            # crate list od record readable for dataframe
            data = [{**i.get('properties',{}), '__data': i}  for i in self._loc_data]
            
            # create a Pandas dataframe
            loc_df = pd.DataFrame.from_records(data)
            
            # convert columns to best possible Pandas dtypes
            loc_df = loc_df.convert_dtypes()
            
            if not self._group_properties:
                # get valid columns for groping
                for col_name, col_type in loc_df.dtypes.items():
                    col_type = str(col_type)
                    if col_type.lower() in ['string', 'int64', 'bool']: # ['string', 'int64', 'float64', 'bool']
                        self._group_properties[col_name] = {
                            "dtypes": col_type,
                            "skip": False
                        }
            
            # get properties list
            properties = [n for n,p in self._group_properties.items() if not p.get('skip',False)]
            if not properties:
                return self.uniqueGroup(prop_text=self.tr("-- No filter property selected --"))
                    
            # convert column type to include NA values
            for col_name in properties:
                loc_df[col_name] = loc_df[col_name].astype(str)
                
            # get groups
            self._group_rows = []
            groups = loc_df.groupby(properties).groups
            for grp_values, grp_items in groups.items():
                row = self._createGroupInfo(properties, grp_values, grp_items)
                if row is not None:
                    self._group_rows.append(row)
            
        except Exception as ex:
            QgsMessageLog.logMessage(traceback.format_exc(), __FROST_PROVIDER_NAME__, Qgis.Critical)
            QMessageBox.critical(iface.mainWindow(), self.tr("Connection"), str(ex))
            return []
        
        # return groups
        return self._group_rows
            
            
    def _createGroupInfo(self, properties, group_values, group_items):
        """Create a group info dict"""
        # create list of grouping column values
        group_values = [group_values] if isinstance(group_values, str) else list(group_values)
        
        # collect properties for naming and filtering 
        prop_values = []
        prop_filters = []
        prop_list = []
        for index, prop_value in enumerate(group_values):
            prop_name = properties[index]
            prop_value = str(prop_value)
            # include only valorized values 
            # TODO: ask if IS NULL operation is supported <====
            if prop_value.upper() != '<NA>':
                prop_list.append(prop_name)
                prop_values.append(prop_value)
                prop_value_quoted = self._quoteString(prop_value)
                prop_filters.append(f"properties/{prop_name} eq {prop_value_quoted}")
        
        # check if valid
        if not prop_list:
            return None
        
        # compose group name        
        grp_name = '_'.join(prop_values)
        
        # compose group url
        filter_param = ' and '.join(prop_filters)
        grp_url = QUrl(self._url_ext)
        query = QUrlQuery(grp_url.query())
        if query.hasQueryItem('$filter'):
            filter_param = "{} and {} ".format(query.queryItemValue('$filter'), filter_param)   
        
        query.removeAllQueryItems('$filter')
        query.addQueryItem('$filter', filter_param)
        grp_url.setQuery(query)
        grp_url = grp_url.toString()
        
        """
        url_param = "$filter={}".format(' and '.join(prop_filters))
        url_obj = urllib.parse.urlparse(self._url_ext)
        grp_url = url_obj._replace(query=urllib.parse.quote(url_param), fragment='').geturl()
        """
        
        # return group Info
        return {
            'name': grp_name,
            'properties': ','.join(prop_list),
            'count': "{}/{}".format(len(group_items), len(self._loc_data)),
            'url':grp_url
        }
        
    def _quoteString(self, value):
        """Quote a string with single quotation"""
        return f"'{value}'" if isinstance(value, str) else value
    
    def _getGeomTypes(self):
        """Collects geometry types"""
        # init 
        self._geom_types = {}
         
        # loop rows
        for row in self._loc_data:
            # get geometry type
            location = row.get('location', {})
            geometry = location.get('geometry', {})
            if not geometry:
                geometry = location
            geom_type = str(geometry.get('type') or '')
            geom_type = QgsWkbTypes.displayString(QgsWkbTypes.parseType(geom_type))
            if geom_type not in self._geom_types:
                self._geom_types[geom_type] = 0
            self._geom_types[geom_type] += 1
            
    def _addExtentFilter(self, url):
        """ """
        # get extent
        canvas = iface.mapCanvas()
        canvasCrs = canvas.mapSettings().destinationCrs()
        destCrs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        transform = QgsCoordinateTransform(canvasCrs, destCrs, QgsProject.instance())
        extent = transform.transform(canvas.extent())
        # add filter parameter
        url = QUrl(str(url))
        query = QUrlQuery(url.query())
        query.addQueryItem('$filter', f"st_intersects(location, geography'{extent.asWktPolygon()}')")
        url.setQuery(query)
        return url.toString()
        