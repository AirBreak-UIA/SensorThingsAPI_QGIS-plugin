# -*- coding: utf-8 -*-
"""QgisLogger class

Description
-----------

QGIS logger class.

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
import time

from qgis.utils import iface
from qgis.core import Qgis, QgsMessageLog, QgsApplication
from qgis.PyQt.QtWidgets import QProgressBar
from PyQt5.QtCore import Qt, QEventLoop
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QTextBrowser

# 
#-----------------------------------------------------------
class debugTimer:
    
    # --------------------------------------
    # 
    # -------------------------------------- 
    def __init__(self):
        """Constructor""" 
        self.__message = None
        self.__startTime = None
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    def __del__(self):
        """Destructor""" 
        if self.__startTime is not None:
            self.stop()
            
    # --------------------------------------
    # 
    # -------------------------------------- 
    def _log(self, msg):
        QgisLogger.log( Qgis.Info, msg )
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    def start(self, msg=None):
        """Start timer"""
        self.__message = str(msg) if msg else "???"
        self.__startTime = time.time()
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    def stop(self, msg=None):
        """Stop timer"""
        msg = msg if msg else self.__message
        if self.__startTime is not None:
            elapsed = round( ( time.time() - self.__startTime ) * 1000.0, 2 )
            self.__startTime = None
            self._log( "{0} [ {1} ms ]".format( msg , elapsed )  )
        
        

# 
#-----------------------------------------------------------
class QgisLogger:
    """ Plugin logger class. """  
      
    ##Level = Qgis.MessageLevel
    class Level:
        Info = Qgis.Info
        Warning = Qgis.Warning
        Critical = Qgis.Critical
        Success = Qgis.Success
    
    
    name = 'SensorThings API'
    suspendMsgbar = False 
    
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def setOverrideCursor(cursor=Qt.WaitCursor):
        """ Sets override application cursor """
        QgsApplication.setOverrideCursor(cursor)
        QgsApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
        
         
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def restoreOverrideCursor():
        """ Restores override application cursor """
        QgsApplication.restoreOverrideCursor()
        QgsApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
    
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def createDebugTimer():
        return debugTimer()
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def log(level, msg, tag=None):
        msg = str(msg)
        tag = QgisLogger.name#if tag is None: tag = QgisLogger.name
        QgsMessageLog.logMessage( msg, tag, level )
        
    # --------------------------------------
    # 
    # --------------------------------------   
    @staticmethod
    def msgbox(level, msg, title=None, tag=None):
        if msg is None: msg = '???'
        if tag is None: tag = QgisLogger.name
        if title is not None: tag = "{0}: {1}".format(tag, title)
        QgisLogger.log(level, msg, tag)
      
        QgisLogger.restoreOverrideCursor()
        if level == Qgis.Critical:
            QMessageBox.critical(iface.mainWindow(), tag, msg)     
        elif level == Qgis.Warning:
            QMessageBox.warning(iface.mainWindow(), tag, msg)    
        else:
            QMessageBox.information(iface.mainWindow(), tag, msg)
            
    # --------------------------------------
    # 
    # --------------------------------------   
    @staticmethod
    def htmlMsgbox(level, msg, title=None, tag=None, standardButtons=QMessageBox.NoButton):
        if msg is None: msg = '???'
        if tag is None: tag = QgisLogger.name
        if title is not None: tag = "{0}: {1}".format(tag, title)
        QgisLogger.log(level, msg, tag)
      
        QgisLogger.restoreOverrideCursor()
        
        icon = QMessageBox.NoIcon
        if level == Qgis.Critical:
            icon = QMessageBox.Critical     
        elif level == Qgis.Warning:
            icon = QMessageBox.Warning   
        else:
            icon = QMessageBox.Information
        
        msgBox = QMessageBox( iface.mainWindow() )
        msgBox.setWindowTitle( tag )
        msgBox.setIcon( icon )
        msgBox.setTextFormat( Qt.RichText )
        msgBox.setText( msg )
        if standardButtons == QMessageBox.NoButton:
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.setDefaultButton(QMessageBox.Ok)
            msgBox.setEscapeButton(QMessageBox.Ok)
        else:
            msgBox.setStandardButtons( standardButtons )
        return msgBox.exec_()
            
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def suspend_msgbar(suspend=True):
        QgisLogger.suspendMsgbar = suspend
    
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def msgbar(level, msg, title=None, tag=None, duration=5, clear=False):
        if QgisLogger.suspendMsgbar:
            return
        
        msg = str(msg)
        if tag is None: tag = QgisLogger.name
        title = QgisLogger.name if title is None else title
        QgisLogger.log(level, msg, tag)
        
        # clear message bar
        if clear:
            iface.messageBar().clearWidgets()
        # push message to message bar
        iface.messageBar().pushMessage(title, msg, level, duration)
        iface.messageBar().repaint()

    
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def msgbar_ext(level, msg, title=None, tag=None, duration=5, clear=False, height=None, icon_path=None):
        if QgisLogger.suspendMsgbar:
            return
        
        msg = str(msg)
        if tag is None: tag = QgisLogger.name
        title = QgisLogger.name if title is None else title
        QgisLogger.log(level, msg, tag)
        
        # clear message bar
        if clear:
            iface.messageBar().clearWidgets()
            
        # create message bar item
        message_bar_item = iface.messageBar().createMessage( title, msg )
        
        # add icon
        if icon_path:
            icon = QIcon( icon_path )
            message_bar_item.setIcon( icon )
        
        # add message bar item
        message_bar_item = iface.messageBar().pushWidget( message_bar_item, level, duration )
        
        # adjust height
        if height:
            layout = message_bar_item.layout()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if isinstance( item.widget(), QTextBrowser ):
                    textBrowser = item.widget()
                    textBrowser.setFixedHeight( height )
        
        # repaint
        message_bar_item.repaint()
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def clear_msgbar():
        # remove widget from message bar
        iface.messageBar().clearWidgets()
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def log_critical(msg, tag=None):
        QgisLogger.log(Qgis.Critical, msg, tag)
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def log_warning(msg, tag=None):
        QgisLogger.log(Qgis.Warning, msg, tag)
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def log_info(msg, tag=None):
        QgisLogger.log(Qgis.Info, msg, tag)
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def msgbox_critical(msg, tag=None):
        QgisLogger.msgbox(Qgis.Critical, msg, tag)
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def msgbox_warning(msg, tag=None):
        QgisLogger.msgbox(Qgis.Warning, msg, tag)
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def msgbox_info(msg, tag=None):
        QgisLogger.msgbox(Qgis.Info, msg, tag)
        
    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def add_progressbar(msg, title=None, level=None, only_message=False):
        if QgisLogger.suspendMsgbar:
            return
        
        # format params
        title = QgisLogger.name if title is None else title
        level = Qgis.Info if level is None else level
        
        # create custom message bar
        progress_message_bar = iface.messageBar().createMessage(title, msg)
        if not only_message:
            progress_bar = QProgressBar()
            progress_bar.setAlignment(Qt.AlignLeft|Qt.AlignVCenter) 
            progress_bar.setRange(0,0) 
            progress_message_bar.layout().addWidget(progress_bar)
        iface.messageBar().pushWidget(progress_message_bar, level)
        progress_message_bar.repaint()
        
        # override cursor 
        QgisLogger.setOverrideCursor(Qt.WaitCursor)
        
    # --------------------------------------
    # 
    # --------------------------------------     
    @staticmethod
    def remove_progressbar():
        # restore cursor
        QgisLogger.restoreOverrideCursor()
        # remove widget from message bar
        iface.messageBar().clearWidgets()
        