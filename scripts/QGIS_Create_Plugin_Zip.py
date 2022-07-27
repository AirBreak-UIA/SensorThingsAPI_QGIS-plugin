"""An utility clas to pack a QGIS plugin as a ZIP archive.

Sandro Moretti - Dedagroup - 2022
"""

# imports
import os
from os.path import basename #, dirname
from os.path import normpath
import configparser
import zipfile
import glob

# constants
PLUGIN_NAME = 'SensorThingsAPI'
PLUGIN_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PLUGIN_FOLDER = os.path.basename(PLUGIN_PATH)
PLUGIN_DIST_PATH = os.path.join(PLUGIN_PATH, 'dist')
    
#
#-----------------------------------------------------------
class QgisPluginPacker:
    """Utility class to create a QGIS plugin archive"""
    
    def __init__(self):
        """Constructor"""
        self._exclude_dirs = set([
            normpath('.git'), 
            normpath('.settings'),
            normpath('__pycache__'),
            normpath(f'{PLUGIN_FOLDER}/dist'),
            normpath(f'{PLUGIN_FOLDER}/scripts'),
        ])
        
        self._exclude_files = set([
            normpath(f'{PLUGIN_FOLDER}/.gitignore'),
            normpath(f'{PLUGIN_FOLDER}/.project'),
            normpath(f'{PLUGIN_FOLDER}/.pydevproject'),
        ])
        
        self._replace_files = {
        }
        

    def get_metadata(self, plgDirName):
        """Return plugin metadata"""
        filePath = os.path.join(plgDirName, 'metadata.txt')

        metadata = configparser.ConfigParser()
        with open(filePath) as f:
            metadata.read_file(f)
            
        result = {}
        result['name'] = metadata.get('general', 'name')
        result['version'] = metadata.get('general', 'version')
        result['description'] = metadata.get('general', 'description')
        result['homepage'] = metadata.get('general', 'homepage')
        result['qgis_minimum_version'] = metadata.get('general', 'qgisMinimumVersion')
        result['author'] = metadata.get('general', 'author').replace('&', '&amp;')
        
        return result

    def pack_pre_checks(self, plgFolder):
        """Pre checks"""
        return True

    def pack(self, plgFolder, destFolder, plgName=None):
        """Create plugin archive"""
        # init
        plgPath = os.path.join( plgFolder, '..' )
        #empty_dirs = []
        
        print(self._exclude_dirs)
        print(self._exclude_files)
        
        # pre checks (if some file exist, etc.)
        if not self.pack_pre_checks(plgFolder):
            print( "Preliminary packing checks not passed!!!!" )
            return False
        
        # get plugin metadata
        plg_metadata = self.get_metadata( plgFolder )
        plg_name = plgName if plgName else plg_metadata.get( 'name' )
        plg_version = plg_metadata.get( 'version' )
        
        
        # create dest folder if not exists
        if not os.path.exists(destFolder):
            os.makedirs(destFolder)
        
        # compose zip file name
        zipfilePath = os.path.join(
            destFolder, 
            "{}.{}.zip".format( plg_name, plg_version ))
        
        ##print(zipfilePath)
        ##print(plg_metadata)
        
        # create a ZipFile object
        with zipfile.ZipFile(zipfilePath, 'w', zipfile.ZIP_DEFLATED) as zipObj:
            # loop plugin folder
            for folderName, subfolders, filenames in os.walk(plgFolder, topdown=True):
                # exclude folder
                folderRelName = os.path.relpath( folderName, plgPath )
                print(folderRelName)
                if normpath(folderRelName) in self._exclude_dirs:
                    subfolders[:] = []
                    continue
                    
                # exclude sub folder    
                subfolders[:] = [d for d in subfolders if normpath(d) not in self._exclude_dirs]
                
                print(folderRelName)
                
                # write files
                n_file = 0
                for filename in filenames:
                    # count files
                    n_file += 1
                    
                    #create complete filepath of file in directory
                    filePath = os.path.join( folderName, filename )
                    fileRelPath = os.path.relpath( filePath, plgPath )
                    
                    # exclude file
                    print(fileRelPath)
                    if normpath(fileRelPath) in self._exclude_files:
                        continue
                    ###print(fileRelPath)
                    
                    # add file to zip
                    zipObj.write( filePath, fileRelPath )
                    
                # write folder
                if not n_file:
                    zfi = zipfile.ZipInfo( folderRelName + "\\" )
                    zfi.external_attr = 16
                    zipObj.writestr( zfi, '' )
                    
            # add replaced files
            for fileToPath, fileFromPath in self._replace_files.items():
                # add file to zip
                fileFromFullPath = os.path.join( plgPath, fileFromPath )
                zipObj.write( fileFromFullPath, fileToPath )
                print( "==> Substitute file '{}' con '{}'".format( fileToPath, fileFromPath ) )
                
        # exit successfully
        print( "Created archive: {}".format( zipfilePath ) )
        return True
    
    def pack_files(self, 
                   plgFolder: str, 
                   destFolder: str, 
                   fileRelNames: list, 
                   plgName: str=None, 
                   postFixName:str ='extra') -> bool :
        """Create plugin archive"""
        # init
        #plgPath = os.path.join( plgFolder, '..' )
        #empty_dirs = []
        
        # get plugin metadata
        plg_metadata = self.get_metadata( plgFolder )
        plg_name = plgName if plgName else plg_metadata.get( 'name' )
        plg_version = plg_metadata.get( 'version' )
        
        # compose zip file name
        zipfilePath = os.path.join(
            destFolder, 
            "{}.{}___{}.zip".format( plg_name, plg_version, postFixName ))
        
        # create a ZipFile object
        with zipfile.ZipFile( zipfilePath, 'w', zipfile.ZIP_DEFLATED ) as zipObj:
            # write files
            for fileRelPath in fileRelNames:
                # add file to zip
                filePath = os.path.join( plgFolder, fileRelPath )
                zipObj.write( filePath, basename(fileRelPath) )
                print( fileRelPath )
                
        # exit successfully
        print( "Created archive: {}".format( zipfilePath ) )
        return True
 
######################################################################## 
plg_packer = QgisPluginPacker()

print( os.linesep.join([
    "------------------------------",
    "       PACK QGIS PLUGIN       ",
    "------------------------------",
]))

res = plg_packer.pack( PLUGIN_PATH, PLUGIN_DIST_PATH, plgName=PLUGIN_NAME )
print( "Result: {}".format(res))
