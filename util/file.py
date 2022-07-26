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
import pathlib

# 
#-----------------------------------------------------------
class FileUtil:
    """Utility class for system file"""
    
    @staticmethod
    def getPrefixFileName(file_name):
        # init
        p = pathlib.Path(file_name)
        f_dir = p.parents[0]
        f_basename = p.stem
        f_ext = p.suffix
        l = len(f_basename)
        # get files 
        postfix_set = set([f.stem[l:] for f in f_dir.glob(f"{f_basename}*{f_ext}")])
        # propose next file name with postfix
        for i in range(1, 1000001):
            postfix = f" ({i})"
            if not postfix in postfix_set:
                return str(pathlib.Path(f_dir, f"{f_basename}{postfix}").with_suffix(f_ext)), postfix_set
            
    