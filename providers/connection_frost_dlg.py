# -*- coding: utf-8 -*-
"""Modulo per la visualizzazione delle informazioni di una postazione.

Descrizione
-----------

Librerie/Moduli
-----------------
    
Notes
-----

- None.

Autore
-------

- Creato da Sandro Moretti il 09/02/2022.
  Dedagroup spa.

Membri
-------
"""
import os.path

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt import uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/connection_dialog.ui'))

# 
#-----------------------------------------------------------
class FrostConnectionDialog(QDialog, FORM_CLASS):

    def __init__(self, parent):
        """ Constructor """
        super().__init__(parent)
        
        # internal member
        self._orig_name = ''
        self._name = ''
        self._url = ''
        self._conn_names = []
        
        # setup widget
        self.setupUi(self)
        #QgsGui.enableAutoGeometryRestore(self)
        
        # setup line edit
        self.edtName.textEdited.connect(self.onNameChanged)
        self.edtURL.textEdited.connect(self.onUrlChanged)
        
        # setup buttons
        self.buttonBox.button(QDialogButtonBox.Ok).setDisabled(True)
        self.buttonBox.clicked.connect(self.onButtonBoxClicked)
        
    @property
    def name(self):
        """ Returns the connection url """
        return self._name
        
    @property
    def url(self):
        """ Returns the connection url """
        return self._url
    
    def onValuesChanged(self):
        """On values changed"""
        # store data
        self._name = self.edtName.text()
        self._url = self.edtURL.text()
        # enable \ disable Accept button
        acceptable = True if self._name and self._url else False
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(acceptable)
    
    def onNameChanged(self, text):
        """On name line edit changed slot"""
        self.onValuesChanged()
        
    def onUrlChanged(self, text):
        """On URL line edit changed slot"""
        self.onValuesChanged()
    
    def onButtonBoxClicked(self, button):
        """On buttonbox clicked slot"""
        if button == self.buttonBox.button(QDialogButtonBox.Ok):
            # check if connection name already exists
            if self._name in self._conn_names and\
               self.name != self._orig_name:
                # ask if overwrite
                ret = QMessageBox.question(
                    self, 
                    self.tr("Save connection"), 
                    "{} '{}'?".format(self.tr('Overwrite the existing connection'), self._name), 
                    QMessageBox.Yes, QMessageBox.No
                )
                if ret != QMessageBox.Yes:
                    return
                    
            #Sovrascrivo la connessione xxx esistente?
            # accept
            self.accept()
            
        else:
            # reject
            self.reject()
            
    def showExec(self, loaded_conn_names: list, name: str='', url: str=''):
        """ Show dialog and execute its event loop """
        
        # init
        self._orig_name = str(name or '')
        self._name = str(name or '')
        self._url = str(url or '')
        self._conn_names = loaded_conn_names
        
        # set edit boxes
        self.edtName.setText(self._name)
        self.edtURL.setText(self._url)
        self.edtName.setFocus()
        
        # check if valid values
        self.onValuesChanged()
        
        # start dialog event loop
        return self.exec_()

