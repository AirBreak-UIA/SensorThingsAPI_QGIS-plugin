# -*- coding: utf-8 -*-
"""SensorThingsWebView class

Description
-----------

This is QWebView customized subclass.

Libraries/Modules
-----------------

- None.
    
Notes
-----

- None.

Author(s)
---------

- Created by Sandro Moretti on 06/06/2022.
  Dedagroup Spa.

Members
-------
"""
import json

from qgis.core import QgsApplication, QgsNetworkAccessManager
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, Qt, QUrl, QVariant, QEventLoop, QObject
from qgis.PyQt.QtWebKit import QWebSettings
from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
# pylint: disable=no-name-in-module
from qgis.PyQt.QtWebKitWidgets import QWebView, QWebPage
# plugin modules
from SensorThingsAPI import __QGIS_PLUGIN_NAME__, __PLG_DEBUG__
from SensorThingsAPI.log.logger import QgisLogger as logger



# 
#-----------------------------------------------------------
class SensorThingsRequestError(Exception):
    """Base class for other exceptions"""

# 
#-----------------------------------------------------------
class SensorThingsNetworkReplyPromise(QObject):
    """
    Class to create an asynchronous network reply 
    with signal resolved, rejected to mimic
    javascript promose
    """
    
    # signals 
    resolved = pyqtSignal(QVariant)
    rejected = pyqtSignal(str)
    
    def __init__(self, nam: QgsNetworkAccessManager, parent: QObject=None):
        """Constructor"""
        super().__init__(parent=parent)
        
        # init
        self._nam = nam or QgsNetworkAccessManager.instance()
        self._options = {}
        
    @pyqtSlot(str, QVariant)
    def get(self, url, options):
        """Send a get request"""
        
        # init
        self._options = options if isinstance(options, dict) else {}
        url = str(url).strip()
        
        # request
        request = QNetworkRequest(QUrl(url))
        request.setPriority(QNetworkRequest.HighPriority)
        request.setAttribute(QNetworkRequest.HttpPipeliningAllowedAttribute, True)
        
        # no cache
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        request.setAttribute(QNetworkRequest.CacheSaveControlAttribute, False)
        
        # send request 
        reply = self._nam.get(request)
        reply.readyRead.connect(lambda: QgsApplication.processEvents( QEventLoop.ExcludeUserInputEvents ))
        reply.finished.connect(self.onFinishedRequest)
        
        # debug
        if __PLG_DEBUG__:
            logger.log(logger.Level.Info, "{}: {}".format(self.tr('Request url'), url))
        
        #
        QgsApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
    
    def onFinishedRequest(self):
        """finished request slot"""
        reply = None
        try:
            # init
            reply = self._nam.sender()
            if reply is None:
                raise SensorThingsRequestError(self.tr('No data returned'))
            
            # check if reply object
            if not hasattr(reply, 'error'):
                raise SensorThingsRequestError(self.tr('Request timeout'))
                
            # check if error
            if reply.error() != QNetworkReply.NoError:
                raise SensorThingsRequestError(reply.errorString())
                
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            if status_code != 200:
                raise SensorThingsRequestError("{}: {}".format(self.tr('HTTP status code'), status_code))
                
            # return data
            if hasattr(reply, 'readAll'):
                result = json.loads(str( reply.readAll().data(), 'utf-8' ))
            else:
                result = json.loads(str( reply.content(), 'utf-8' ))
                
            # get source data
            dataSrc = str(self._options.get('dataSrc', '')).strip()
            if dataSrc and isinstance(result, dict):
                result = result.get(dataSrc, result)
                
            # return data
            self.resolved.emit(result)
               
        except Exception as ex:
            self.rejected.emit(str(ex))
            
        finally:
            if reply is not None:
                reply.deleteLater()

# 
#-----------------------------------------------------------
class SensorThingsNetworkAccessManager(QNetworkAccessManager):
    """QNetworkAccessManager subclass.

    This subclass is used to deny external resources.
    """

    def __init__(self, deny_external_links, parent=None):
        self._deny_external_links = deny_external_links
        super().__init__(parent)
    
    def createRequest(self, op, request, outgoingData=None):
        strURL = str(request.url().toString())
        if __PLG_DEBUG__:
            logger.log(logger.Level.Info, "{}: {}".format(self.tr("Request url"), strURL))
            
        if self._deny_external_links and\
           not request.url().isLocalFile():
            request.setUrl(QUrl('file:///web/denied.resouce'))
            
        return super().createRequest(op, request, outgoingData)
    
    @staticmethod
    def requestExternalData(url: str, options: dict=None, nam: QgsNetworkAccessManager=None):
        """Method to request external data synchronously"""
        
        # init
        nam = nam or QgsNetworkAccessManager.instance()
        url = str(url).strip()
        options = options if isinstance(options, dict) else {}
        
        # request
        request = QNetworkRequest(QUrl(url))
        request.setPriority(QNetworkRequest.HighPriority)
        request.setAttribute(QNetworkRequest.HttpPipeliningAllowedAttribute, True)
        
        # no cache
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        request.setAttribute(QNetworkRequest.CacheSaveControlAttribute, False)
        
        # debug
        if __PLG_DEBUG__:
            logger.log(logger.Level.Info, "{}: {}".format(SensorThingsNetworkAccessManager.tr("Request url"), url))
        
        # send request 
        reply = nam.blockingGet(request)
        
        # check if error
        if reply.error() != QNetworkReply.NoError:
            raise SensorThingsRequestError(reply.errorString())
        
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            raise SensorThingsRequestError(reply.errorString())
        
        # return data
        if hasattr( reply, 'readAll' ):
            result = json.loads(str( reply.readAll().data(), 'utf-8' ))
        else:
            result = json.loads(str( reply.content(), 'utf-8' ))
    
        # get source data
        dataSrc = str(options.get('dataSrc', '')).strip()
        if dataSrc and isinstance(result, dict):
            result = result.get(dataSrc, result)
            
        # return data
        return result  
    
    @staticmethod
    def requestExternalDataAsync(nam: QgsNetworkAccessManager=None, parent=None):
        """Method to request external data asynchronously"""
        return SensorThingsNetworkReplyPromise(nam, parent)
# 
#-----------------------------------------------------------
class SensorThingsWebPage(QWebPage):
    """QWebPage subclass that opens links in system browser

    This subclass is used to deny external resources.
    """
    
    def __init__(self, deny_external_urls, parent=None):
        super().__init__(parent)
        self._deny_external_urls = deny_external_urls

    def acceptNavigationRequest(self, frame, request, navigationType):
        strURL = str(request.url().toString())
        if __PLG_DEBUG__:
            logger.log(logger.Level.Info, "{}: {}".format(self.tr("Webview request"), strURL))
        
        if self._deny_external_urls and\
           not request.url().isLocalFile():
            return False
        
        return super().acceptNavigationRequest(frame, request, navigationType)

# 
#-----------------------------------------------------------    
class SensorThingsWebView(QWebView):
    """Derived QWebView class to deny external resources"""
    
    def __init__(self, parent=None):
        # init
        QWebView.__init__(self, parent=parent)
        
        # Create widgets
        nam = SensorThingsNetworkAccessManager(deny_external_links=True)
        webPage = SensorThingsWebPage(deny_external_urls=True)
        webPage.setNetworkAccessManager(nam)
        webPage.networkAccessManager().sslErrors.connect(self._handleSslErrors)
        self.setPage(webPage)
        #super().connect(self.ui.webView,QtCore.SIGNAL("titleChanged (const QString&amp;)"), self.adjustTitle)
        settings = self.settings()
        ##settings.setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, False)
        ##settings.setAttribute(QWebSettings.LocalContentCanAccessFileUrls, False)
        ##settings.setAttribute(QWebSettings.XSSAuditingEnabled, True)
        settings.setDefaultTextEncoding('utf-8')
        
        if __PLG_DEBUG__:
            settings.setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        else:
            self.setContextMenuPolicy(Qt.NoContextMenu)
   
    def _handleSslErrors(self, reply, errors):
        """Handle SSL errors"""
        
        logger.log(
                logger.Level.Critical, 
                "{}: {}".format(self.tr("SSL error"), errors), 
                tag=__QGIS_PLUGIN_NAME__)
        
        reply.ignoreSslErrors()
        
    def _injectPyToJs(self, obj, js_objname='pyjsapi'):
        """Add pyapi to javascript window object"""
        
        self.page().mainFrame().addToJavaScriptWindowObject(js_objname, obj)
        
    def injectPyToJs(self, obj, js_objname='pyjsapi'):
        """Add pyapi to javascript window object"""
        
        # add Python object to js
        self._injectPyToJs(obj, js_objname)
        
        # add Python object to js on document loaded 
        self.page().mainFrame().javaScriptWindowObjectCleared.connect(
            lambda o=obj, n=js_objname, self=self: self._injectPyToJs(o, n))
            
    