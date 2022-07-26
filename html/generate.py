# -*- coding: utf-8 -*-
"""htmlUtil

Description
-----------

Utility class to manage HTML templates.

Libraries/Modules
-----------------

- None.
    
Notes
-----

- None.


Author(s)
---------

- Created by Sandro Moretti on 09/02/2022.

Copyright (c) Dedagroup Spa.

Members
-------
"""
from jinja2 import Environment, FileSystemLoader
import os
 
from PyQt5.QtCore import QUrl, QByteArray, QBuffer 
from PyQt5.QtGui import QPixmap, QImage 
 
# 
#-----------------------------------------------------------
class htmlUtil:

    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def getBaseUrl():
        # return base URL for HTML templates
        root = os.path.dirname(os.path.abspath(__file__))
        root_url = QUrl.fromLocalFile(root).toString()
        return f"{root_url}/"

    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def imgToBase64(img_path):
        pixmap = QPixmap(img_path)
        image = QImage( pixmap.toImage() )
        #icon = QIcon( img_path )
        #image = QImage( icon.pixmap(20,20).toImage() )
        data = QByteArray()
        buf = QBuffer( data )
        image.save( buf, 'png' )
        return "data:image/png;base64,{}".format( data.toBase64().data().decode('utf-8') )

    # --------------------------------------
    # 
    # -------------------------------------- 
    @staticmethod
    def generateTemplate(template_file): 
        def filter_supress_none(val):
            if not val is None:
                return val
            else:
                return ''
        
        root = os.path.dirname( os.path.abspath(__file__) )
        templates_dir = os.path.join(root, 'templates')
        env = Environment( loader = FileSystemLoader(templates_dir) )
        env.filters['sn'] = filter_supress_none
        template = env.get_template(template_file)
        return template
