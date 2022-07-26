# -*- coding: utf-8 -*-
"""UrlHelper class

Description
-----------

Utility class for URL.

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
from urllib.parse import urljoin

# 
#-----------------------------------------------------------
class UrlHelper:
    """Utility class for URL"""
    
    @staticmethod
    def join(base, url, allow_fragments=True):
        base = str(base).strip().rstrip('\\/') + '/'
        return urljoin(base, url, allow_fragments)
    