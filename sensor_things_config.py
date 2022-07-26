# -*- coding: utf-8 -*-
"""SensorThings API config class

Description
-----------

Utility class for the plugin configuration.

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
import os
import yaml

from qgis.PyQt.QtCore import QObject

# 
#-----------------------------------------------------------
class SensorThingsConfig(QObject):
    """ Plugin configuration class. """
    
    CFG_PLUGIN_FILE_NAME = 'config.yaml'
    
    def __init__(self, cfg_file: str=None, parent: QObject=None):
        """Constructor"""
        super().__init__(parent=parent)
        self.__config = {}
        self.__config_file = None
        # read config file
        self.__initialize(cfg_file)
        
            
    def __initialize(self, cfg_file: str=None):
        """Initialization method to import YAML config file"""
        
        # init
        cfg_file = cfg_file or self.plugin_config_file
        
        # load yaml file
        with open(cfg_file, 'r') as stream:
            self.__config = yaml.load( stream, Loader=yaml.loader.Loader )
        
        # set internal members
        self.__config_file = cfg_file
        
    @property
    def initialized(self) -> bool:
        """Returns true if inizialized """
        return self.__config_file is not None
    
    @property
    def plugin_config_file(self) -> bool:
        """Returns config file path"""
        return os.path.join(os.path.dirname(__file__), 'conf', self.CFG_PLUGIN_FILE_NAME)
        
    def get_value(self, cfg_path: str, default=None):
        """Returns a config value by a key path, with slash as separator"""
        
        # find value from path
        cfg_path = cfg_path or ''
        value = None
        dt = self.__config
        for key in cfg_path.split( '/' ):
            if dt is None:
                break
            value = dt = dt.get(key)
       
        # check if found value     
        if value is not None:
            # return found value
            return value
        
        elif default is not None:
            # return default value
            return default
        
        # raise exception if value not found
        raise KeyError( "{0}: '{1}'".format(
            self.tr( "Key path not found in the configuration file" ),
            cfg_path ) )
        