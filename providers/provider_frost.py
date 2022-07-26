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
from json import JSONDecodeError
import traceback

from qgis.core import (
    Qgis,
    QgsField,
    QgsFields,
    #QgsPointXY,
    QgsFeatureRequest,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsWkbTypes,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsRectangle,
    QgsVectorDataProvider,
    QgsAbstractFeatureSource,
    QgsAbstractFeatureIterator,
    QgsFeatureIterator,
    QgsProviderRegistry,
    QgsProviderMetadata,
    QgsSpatialIndex,
    QgsCsException,
    QgsMessageLog,
    QgsNetworkAccessManager,
    QgsDataSourceUri
)

from qgis.PyQt.QtCore import QVariant, QUrl, QUrlQuery, QCoreApplication
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import QgsJsonUtils


#: Constant for provider name  
__FROST_PROVIDER_NAME__ = 'frost'

#: Constant for provider description  
__FROST_PROVIDER_DESCRIPTION__ = 'Frost server Provider'

#: Constant for provider defautl geometry type
__FROST_DEFAULT_GEOM_TYPE__ = QgsWkbTypes.Point

#: Constant for provider geometry type url parameter
__FROST_PARAMETER_GEOM_TYPE__ = '__providerGeomType'

# 
#-----------------------------------------------------------
class FrostFeatureIteratorImpl(QgsAbstractFeatureIterator):
    """Internal feature iterator for Frost data provider"""
    
    def __init__(self, source, request):
        """Constructor"""
        super().__init__(request)
        
        # init
        self._feature_id_list = None
        self._source = source
        self._index = 0
        self._transform = QgsCoordinateTransform()
        self._request = request if request is not None else QgsFeatureRequest()
        self._filter_rect = self.filterRectToSourceCrs(self._transform)
        self._select_rect_engine = None
        self._select_rect_geom = None
        self._select_distance_within_geom = None
        self._select_distance_within_engine = None
        
        self._transform = QgsCoordinateTransform()
        if self._request.destinationCrs().isValid() and self._request.destinationCrs() != self._source._provider.crs():
            self._transform = QgsCoordinateTransform(self._source._provider.crs(), self._request.destinationCrs(), self._request.transformContext())
        
        try:
            self._filter_rect = self.filterRectToSourceCrs(self._transform)
        except QgsCsException:
            self.close()
            return
        
        self._filter_rect = self.filterRectToSourceCrs(self._transform)
        if not self._filter_rect.isNull():
            self._select_rect_geom = QgsGeometry.fromRect(self._filter_rect)
            self._select_rect_engine = QgsGeometry.createGeometryEngine(self._select_rect_geom.constGet())
            self._select_rect_engine.prepareGeometry()
        else:
            self._select_rect_engine = None
            self._select_rect_geom = None

        if Qgis.QGIS_VERSION_INT >= 32200:
            if self._request.spatialFilterType() == Qgis.SpatialFilterType.DistanceWithin and not self._request.referenceGeometry().isEmpty():
                self._select_distance_within_geom = self._request.referenceGeometry()
                self._select_distance_within_engine = QgsGeometry.createGeometryEngine(self._select_distance_within_geom.constGet())
                self._select_distance_within_engine.prepareGeometry()
            else:
                self._select_distance_within_geom = None
                self._select_distance_within_engine = None

        self._feature_id_list = None
        if self._filter_rect is not None and self._source._provider._spatialindex is not None:
            self._feature_id_list = self._source._provider._spatialindex.intersects(self._filter_rect)

        if self._request.filterType() == QgsFeatureRequest.FilterFid or self._request.filterType() == QgsFeatureRequest.FilterFids:
            fids = [self._request.filterFid()] if self._request.filterType() == QgsFeatureRequest.FilterFid else self._request.filterFids()
            self._feature_id_list = list(set(self._feature_id_list).intersection(set(fids))) if self._feature_id_list else fids
        
        
    def __del__(self):
        """Destructor"""
        pass
        
    def __iter__(self):
        """Returns self as an iterator object"""
        self._index = 0
        return self

    def __next__(self):
        """Returns the next value till current is lower than high"""
        f = QgsFeature()
        if not self.nextFeature(f):
            raise StopIteration
        else:
            return f
        
    def rewind(self):
        """Reset the iterator to the starting position"""
        # virtual bool rewind() = 0;
        if self._index < 0:
            return False
        self._index = 0
        return True

    def close(self):
        """End of iterating: free the resources / lock"""
        self._index = -1
        return True

    def fetchFeature(self, f):
        """Fetch next feature, return true on success"""
        if self._index < 0:
            f.setValid(False)
            return False
        try:
            found = False
            while not found:
                _feats = self._source.requestProviderFeatures()
                _f = _feats[list(_feats.keys())[self._index]]
                self._index += 1
                
                if self._feature_id_list and _f.id() not in self._feature_id_list:
                    continue

                if not self._filter_rect.isNull():
                    if not _f.hasGeometry():
                        continue
                    if self._request.flags() & QgsFeatureRequest.ExactIntersect:
                        # do exact check in case we're doing intersection
                        if not self._select_rect_engine.intersects(_f.geometry().constGet()):
                            continue
                    else:
                        if not _f.geometry().boundingBox().intersects(self._filter_rect):
                            continue

                self._source._expression_context.setFeature(_f)
                if self._request.filterType() == QgsFeatureRequest.FilterExpression:
                    if not self._request.filterExpression().evaluate(self._source._expression_context):
                        continue
                if self._source._subset_expression:
                    if not self._source._subset_expression.evaluate(self._source._expression_context):
                        continue
                elif self._request.filterType() == QgsFeatureRequest.FilterFids:
                    if not _f.id() in self._request.filterFids():
                        continue
                elif self._request.filterType() == QgsFeatureRequest.FilterFid:
                    if _f.id() != self._request.filterFid():
                        continue
                        
                f.setGeometry(_f.geometry())
                self.geometryToDestinationCrs(f, self._transform)

                if self._select_distance_within_engine and self._select_distance_within_engine.distance(f.geometry().constGet()) > self._request.distanceWithin():
                    continue

                f.setFields(_f.fields())
                f.setAttributes(_f.attributes())
                f.setValid(_f.isValid())
                f.setId(_f.id())
                return True
        except IndexError:
            f.setValid(False)
            return False

# 
#-----------------------------------------------------------
class FrostFeatureIterator(QgsFeatureIterator):
    """This is a workaround to keep references to iterator classes
       so they are not removed when the variable gets out of scope."""
    _kept_refs = []
    
    def __init__(self, it):
        super().__init__(it)
        FrostFeatureIterator._kept_refs.append(it)
# 
#-----------------------------------------------------------
class FrostFeatureSource(QgsAbstractFeatureSource):
    """Derived class to return Frost features"""

    def __init__(self, provider):
        """Constructor"""
        super().__init__()
        self._provider = provider
        self._expression_context = QgsExpressionContext()
        self._expression_context.appendScope(QgsExpressionContextUtils.globalScope())
        self._expression_context.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
        self._expression_context.setFields(self._provider.fields())
        if self._provider.subsetString():
            self._subset_expression = QgsExpression(self._provider.subsetString())
            self._subset_expression.prepare(self._expression_context)
        else:
            self._subset_expression = None
        
    def requestProviderFeatures(self):
        """Returns provided features"""
        return self._provider.requestFeatures()

    def getFeatures(self, request):
        """Gets an iterator for features matching the specified request"""
        return FrostFeatureIterator(FrostFeatureIteratorImpl(self, request))

# 
#-----------------------------------------------------------
class FrostProvider(QgsVectorDataProvider):
    """Derived class for Frost vector data provider"""
    
    next_feature_id = 1

    @classmethod
    def providerKey(cls):
        """Returns the memory provider key"""
        return __FROST_PROVIDER_NAME__
    
    @classmethod
    def providerDescription(cls):
        """Returns the provider description"""
        return __FROST_PROVIDER_DESCRIPTION__

    @classmethod
    def createProvider(cls, uri, *args, **kwargs):
        """Creates a new Frost provider object"""
        return FrostProvider(uri, *args, **kwargs)
    
    @staticmethod
    def correctQurlParams(url):
        """Correct/complete url query parameters"""
        url = QUrl(url)
        query = QUrlQuery(url.query())
        if not query.hasQueryItem('$top'):
            query.addQueryItem('$top', '2147483647')
        if not query.hasQueryItem('$orderby'):
            query.addQueryItem('$orderby', '@iot.id+asc')
        url.setQuery(query)
        return url
    
    @staticmethod
    def getDataCount(url):
        """Get total rows of data"""
        # compose url
        url = QUrl(url)
        query = QUrlQuery(url.query())
        query.addQueryItem('$count', 'true')
        query.addQueryItem('$top', '1')
        url.setQuery(query)
        # create request
        nam = QgsNetworkAccessManager.instance()
        request = QNetworkRequest(QUrl(url))
        request.setPriority(QNetworkRequest.HighPriority)
        request.setAttribute(QNetworkRequest.HttpPipeliningAllowedAttribute, True)
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        request.setAttribute(QNetworkRequest.CacheSaveControlAttribute, False)
        reply = nam.blockingGet(request)
            
        # check if error
        if reply.error() != QNetworkReply.NoError:
            return '????'
            
        # get data
        response = json.loads(str(reply.content(), 'utf-8')) or {}
        return response.get("@iot.count", '????')
        
    
    @staticmethod
    def requestData(url, callback=None):
        """Load data from Frost server"""
        
        # init
        rows = []
        
        try:
            # get total rows of data
            num_rows = 0
            total_rows = FrostProvider.getDataCount(url)
            
            # create request
            # https://ogc-demo.k8s.ilt-dmz.iosb.fraunhofer.de/v1.1/Locations?$top=2147483647
            url = FrostProvider.correctQurlParams(url)
            nam = QgsNetworkAccessManager.instance()
            next_url = url.toString()
            while next_url:
                print("Next URL: ", next_url)
                
                # create request
                request = QNetworkRequest(QUrl(next_url))
                request.setPriority(QNetworkRequest.HighPriority)
                request.setAttribute(QNetworkRequest.HttpPipeliningAllowedAttribute, True)
                # no cache
                request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
                request.setAttribute(QNetworkRequest.CacheSaveControlAttribute, False)
            
                # send request 
                reply = nam.blockingGet(request)
                    
                # check if error
                if reply.error() != QNetworkReply.NoError:
                    raise Exception(reply.errorString())
                    
                status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
                if status_code != 200:
                    msg = QCoreApplication.translate(__FROST_PROVIDER_NAME__, "HTTP request failed; response code")
                    raise Exception("{}: {}".format(msg, status_code))
                    
                # get data
                response = json.loads(str(reply.content(), 'utf-8')) or {}
                read_rows = response.get('value', []) or []
                rows.extend(read_rows)
                
                # get next data page
                next_url = response.get("@iot.nextLink")
                
                # get count
                if callback:
                    num_rows += len(read_rows)
                    callback(num_rows, total_rows)
                
            # return data
            return rows
            
        except (UnicodeDecodeError, JSONDecodeError, ValueError) as ex:
            QgsMessageLog.logMessage(str(ex), __FROST_PROVIDER_NAME__, Qgis.Critical)
            QgsMessageLog.logMessage(traceback.format_exc(), __FROST_PROVIDER_NAME__, Qgis.Critical)
            
        # return internal feature dict    
        return rows

    # Implementation of functions from QgsVectorDataProvider
    def __init__(self, uri, providerOptions=None, flags=None):
        """Constructor"""
        uri = str(uri)
        super().__init__(uri)
        
        # geometry type
        self._wkbType = __FROST_DEFAULT_GEOM_TYPE__
        self._defWkbType = True
        
        # uri
        src_url = QUrl(uri)
        query = QUrlQuery(src_url.query())
        if query.hasQueryItem(__FROST_PARAMETER_GEOM_TYPE__):
            # get geometry type
            geom_type = query.queryItemValue(__FROST_PARAMETER_GEOM_TYPE__)
            self._wkbType = QgsWkbTypes.parseType(geom_type)
            self._defWkbType = False
            
            # remove provider geometry type parameter
            query.removeAllQueryItems(__FROST_PARAMETER_GEOM_TYPE__)
            src_url.setQuery(query)
            self._uri = src_url.toString() # QUrl.EncodeSpaces ?
            
        else:
            self._uri = uri
        
        # crs
        self._crs = QgsCoordinateReferenceSystem.fromEpsgId(4326) 
        
        # define fields
        fields = QgsFields()
        fields.append(QgsField('id', QVariant.String)) #, '', 254, 0))
        fields.append(QgsField('name', QVariant.String)) #, '', 254, 0))
        fields.append(QgsField('description', QVariant.String)) #, '', 254, 0))
        ##fields.append(QgsField('organization', QVariant.String, '', 254, 0)) REMOVED
        
        self.setNativeTypes([
            QgsVectorDataProvider.NativeType(self.tr("Whole number (integer)"), "integer", QVariant.Int, 0, 10),
            QgsVectorDataProvider.NativeType(self.tr("Decimal number (real)"), "double", QVariant.Double, 0, 32, 0, 30),
            QgsVectorDataProvider.NativeType(self.tr("Text (string)"), "string", QVariant.String, 0, 255),
            QgsVectorDataProvider.NativeType(self.tr("Date"), "date", QVariant.Date, -1, -1, -1, -1),
            QgsVectorDataProvider.NativeType(self.tr("Time"), "time", QVariant.Time, -1, -1, -1, -1),
            QgsVectorDataProvider.NativeType(self.tr("Date & Time"), "datetime", QVariant.DateTime, -1, -1, -1, -1),
            QgsVectorDataProvider.NativeType(self.tr("Whole number (smallint - 16bit)"), "int2", QVariant.Int, -1, -1, 0, 0),
            QgsVectorDataProvider.NativeType(self.tr("Whole number (integer - 32bit)"), "int4", QVariant.Int, -1, -1, 0, 0),
            QgsVectorDataProvider.NativeType(self.tr("Whole number (integer - 64bit)"), "int8", QVariant.LongLong, -1, -1, 0, 0),
            QgsVectorDataProvider.NativeType(self.tr("Decimal number (numeric)"), "numeric", QVariant.Double, 1, 20, 0, 20),
            QgsVectorDataProvider.NativeType(self.tr("Decimal number (decimal)"), "decimal", QVariant.Double, 1, 20, 0, 20),
            QgsVectorDataProvider.NativeType(self.tr("Decimal number (real)"), "real", QVariant.Double, -1, -1, -1, -1),
            QgsVectorDataProvider.NativeType(self.tr("Decimal number (double)"), "double precision", QVariant.Double, -1, -1, -1, -1),
            QgsVectorDataProvider.NativeType(self.tr("Text, unlimited length (text)"), "text", QVariant.String, -1, -1, -1, -1),
            QgsVectorDataProvider.NativeType(self.tr("Boolean"), "bool", QVariant.Bool),
            QgsVectorDataProvider.NativeType(self.tr("Binary object (BLOB)"), "binary", QVariant.ByteArray)
        ])
        self._fields = fields
        self._features = None
        self._extent = QgsRectangle()
        self._extent.setMinimal()
        self._subset_string = ''
        
        self._spatialindex = None
        self._provider_options = providerOptions
        self._flags = flags
        
    def featureSource(self):
        """Returns feature source object"""
        return FrostFeatureSource(self)

    def dataSourceUri(self, expandAuthConfig=False):
        """Gets the data source specification"""  
        if expandAuthConfig and 'authcfg' in self._uri:
            uri = QgsDataSourceUri(self._uri)
            return uri.uri(expandAuthConfig)
        else:
            return self._uri
       

    def storageType(self):
        """Returns a friendly display name for the source"""
        return "Frost memory storage"

    def getFeatures(self, request=QgsFeatureRequest()):
        """Query the provider for features specified in request"""
        return FrostFeatureIterator(FrostFeatureIteratorImpl(FrostFeatureSource(self), request))

    def uniqueValues(self, fieldIndex, limit=1):
        results = set()
        if fieldIndex >= 0 and fieldIndex < self.fields().count():
            req = QgsFeatureRequest()
            req.setFlags(QgsFeatureRequest.NoGeometry)
            req.setSubsetOfAttributes([fieldIndex])
            for f in self.getFeatures(req):
                results.add(f.attributes()[fieldIndex])
        return results

    def wkbType(self):
        """Returns number of provided features"""
        return self._wkbType

    def featureCount(self):
        """Returns number of provided features"""
        if not self.subsetString():
            return len(self.requestFeatures())
        else:
            req = QgsFeatureRequest()
            req.setFlags(QgsFeatureRequest.NoGeometry)
            req.setSubsetOfAttributes([])
            return len([f for f in self.getFeatures(req)])

    def fields(self):
        """Returns fields list"""
        return self._fields
    
    
        
    def requestFeatures(self, recreate: bool=False):
        """Load feature from Frost server"""
        
        # init
        if self._features is not None and not recreate:
            return self._features
            
        self._features = {}
        
        
        try:
            # get data
            rows = FrostProvider.requestData(self._uri)
            
            # loop rows
            for row in rows:
                # get id
                iot_id = row.get('@iot.id', None)
                
                #properties = row.get('properties', {})
                
                # get location feature
                feat_list = self._createFeature(iot_id, row)
                if not feat_list:
                    continue
                    
                # read attributes
                attrs = []
                attrs.append(self._quoteString(iot_id))
                attrs.append(row.get('name', None))
                attrs.append(row.get('description', None))
                #attrs.append(properties.get('organization', None)) REMOVED
                    
                # create feature
                for feat in feat_list:
                    feat.setAttributes(attrs)
                    feat.setId(self.next_feature_id)
                    self._features[self.next_feature_id] = feat
                    self.next_feature_id += 1
            
            
            # create spatial index
            self.createSpatialIndex()
            
        except (UnicodeDecodeError, JSONDecodeError, ValueError) as ex:
            QgsMessageLog.logMessage(str(ex), __FROST_PROVIDER_NAME__, Qgis.Critical)
            QgsMessageLog.logMessage(traceback.format_exc(), __FROST_PROVIDER_NAME__, Qgis.Critical)
            
        # return internal feature dict    
        return self._features
    
    
    
    def addFeatures(self, flist, flags=None):
        """Add new feature method"""
        return False, []

    def deleteFeatures(self, ids):
        """Delete features method"""
        return 0
        
    def addAttributes(self, attrs):
        """Add new attributes method"""
        return False
        
    def renameAttributes(self, renamedAttributes):
        """Rename attributes method"""
        return False
        
    def deleteAttributes(self, attributes):
        """Delete attributes method"""
        return False
        
    def changeAttributeValues(self, attr_map):
        """Change attribute values method"""
        return False
        
    def changeGeometryValues(self, geometry_map):
        """Change geometries values method"""
        return False
        
    def allFeatureIds(self):
        """Returns id list of all provided features"""
        return list(self.requestFeatures().keys())

    def subsetString(self):
        """Returns the subset definition string currently in use by 
           the layer and used by the provider to limit the feature set"""
        return self._subset_string

    def setSubsetString(self, subsetString, updateFeatureCount):
        """Set the subset string used to create a subset of features in the layer"""
        if subsetString == self._subset_string:
            return True
        self._subset_string = subsetString
        self.updateExtents()
        self.clearMinMaxCache()
        self.dataChanged.emit()
        return True

    def supportsSubsetString(self):
        """Returnsif the provider supports setting of subset strings"""
        return True

    def createSpatialIndex(self):
        """Creates spatial index for requested featurs"""
        if self._spatialindex is None:
            self._spatialindex = QgsSpatialIndex()
            for f in self.requestFeatures().values():
                self._spatialindex.addFeature(f)
        return True

    def capabilities(self):
        """Returns flags containing the supported capabilities"""
        return QgsVectorDataProvider.CreateSpatialIndex | QgsVectorDataProvider.SelectAtId | QgsVectorDataProvider.CircularGeometries
        #return QgsVectorDataProvider.AddFeatures | QgsVectorDataProvider.DeleteFeatures | QgsVectorDataProvider.CreateSpatialIndex | QgsVectorDataProvider.ChangeGeometries | QgsVectorDataProvider.ChangeAttributeValues | QgsVectorDataProvider.AddAttributes | QgsVectorDataProvider.DeleteAttributes | QgsVectorDataProvider.RenameAttributes | QgsVectorDataProvider.SelectAtId | QgsVectorDataProvider. CircularGeometries
        

    def name(self):
        """Returns the provider name"""
        return self.providerKey()
    
    def description(self):
        """Returns the provider description"""
        return __FROST_PROVIDER_DESCRIPTION__

    def extent(self):
        """Returns the extent of all providedfeatures"""
        if self._extent.isEmpty() and self.requestFeatures():
            self._extent.setMinimal()
            if not self._subset_string:
                # fast way - iterate through all features
                for feat in self.requestFeatures().values():
                    if feat.hasGeometry():
                        self._extent.combineExtentWith(feat.geometry().boundingBox())
            else:
                for f in self.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([])):
                    if f.hasGeometry():
                        self._extent.combineExtentWith(f.geometry().boundingBox())

        elif not self.requestFeatures():
            self._extent.setMinimal()
            
        return QgsRectangle(self._extent)

    def updateExtents(self):
        """Update the extent of all provided features"""
        self._extent.setMinimal()

    def isValid(self):
        """Returns if valid provider"""
        return True

    def crs(self):
        """Returns crs of provier data"""
        return self._crs

    def handlePostCloneOperations(self, source):
        """Handles any post-clone operations required after this 
           vector data provider was cloned from the source provider"""
        self._features = source.requestProviderFeatures()
        
        
    def _quoteString(self, value):
        """Quote a string with single quotation"""
        return f"'{value}'" if isinstance(value, str) else value
    
    def _createFeature(self, iot_id, row):
        """ """
        try:
            # try to create feature from json
            json_location = row.get('location', {})
            json_geom = json.dumps(json_location)
            feat_list = QgsJsonUtils.stringToFeatureList(json_geom)
            
            # filter feature
            res_feat_list = []
            for feat in feat_list:
                # check if valid geometry
                geom = feat.geometry()
                if geom.wkbType() == self._wkbType:
                    res_feat_list.append(feat)
                    
                elif self._defWkbType:
                    # log message
                    geom_type = QgsWkbTypes.displayString(geom.wkbType())
                    QgsMessageLog.logMessage(
                        "{} (@iot.id: {}): {}".format(
                            self.tr("Geometry type not allowed"), iot_id, geom_type),
                        __FROST_PROVIDER_NAME__, 
                        Qgis.Warning)
            
            # return list of features
            return res_feat_list
            
        except Exception as ex:
            # emit log
            QgsMessageLog.logMessage(
                "{} (@iot.id: {}): {}".format(self.tr("Skipped invalid location"), iot_id, str(ex)),
                __FROST_PROVIDER_NAME__, 
                Qgis.Warning)
            return [] 
    
    """        
    def _createFeature(self, iot_id, row):
        """ """
        try:
            # try to create feature from json
            location = row.get('location', {})
            geometry = location.get('geometry', {})
            if not geometry:
                geometry = location
                
            geom_type = str(geometry.get('type') or '').strip().lower()
            if geom_type != 'point':
                raise ValueError("{} '{}'".format(self.tr("Geometry type not allowed"), geom_type))
                
            coordinates = geometry.get('coordinates', [])
            x = float(coordinates[0])
            y = float(coordinates[1])
            
            geom = QgsGeometry.fromPointXY(QgsPointXY(x,y))
            feat = QgsFeature(self.fields())
            feat.setGeometry(geom)
            
            return [feat]
            
        except (TypeError, AttributeError, IndexError, ValueError) as ex:
            # emit log
            QgsMessageLog.logMessage(
                "{} (@iot.id: {}): {}".format(self.tr("Skipped invalid location"), iot_id, str(ex)),
                __FROST_PROVIDER_NAME__, 
                Qgis.Warning)
            return [] 
    """


def register_frost_data_provider() -> bool:
    """Register Frost provider"""
    registry = QgsProviderRegistry.instance()
    if __FROST_PROVIDER_NAME__ not in registry.providerList():  
        metadata = QgsProviderMetadata(
            FrostProvider.providerKey(),
            FrostProvider.providerDescription(),
            FrostProvider.createProvider)
        return registry.registerProvider(metadata)
    return True
        

def unregister_frost_data_provider() -> bool:
    """Unregister Frost provider: do nothing"""
    return False
