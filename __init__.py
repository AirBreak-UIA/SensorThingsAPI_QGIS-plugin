# -*- coding: utf-8 -*-
from PyQt5.QtCore import QCoreApplication

#: Constant name of plugin
__QGIS_PLUGIN_NAME__ = 'SensorThings API'

#: Constant to enable debug messages in plugin log.
__PLG_DEBUG__ = True

#: Global instance of configuration class
plgConfig = None

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Instantiates SensorThings API Plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    # Instance global configuration class
    from SensorThingsAPI.sensor_things_config import SensorThingsConfig
    global plgConfig # pylint: disable=W0603
    plgConfig = SensorThingsConfig()

    # start
    from SensorThingsAPI.sensor_things import SensorThingsPlugin
    return SensorThingsPlugin(iface)
