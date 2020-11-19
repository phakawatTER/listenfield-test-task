import time
from flask import Flask,Response,request,jsonify
import ee
import json
import sys
# import os


FEATURE_COLLECTION = 'USDOS/LSIB_SIMPLE/2017'
IMAGE_COLLECTION = 'LANDSAT/LC08/C01/T1_SR'
VIS_PARAMS = {
  "bands": ['B4', 'B3', 'B2'],
  "min": 0,
  "max": 3000,
  "gamma": 1.4,
};

"""
CLOUD_COVER	INT
Percentage cloud cover, -1 = not calculated. (Obtained from raw Landsat metadata)
CLOUD_COVER_LAND	INT
Percentage cloud cover over land, -1 = not calculated. (Obtained from raw Landsat metadata)
EARTH_SUN_DISTANCE	DOUBLE
Earth-Sun distance (AU)
ESPA_VERSION	STRING
Internal ESPA image version used to compute SR
GEOMETRIC_RMSE_MODEL	DOUBLE
Combined RMSE (Root Mean Square Error) of the geometric residuals (meters) in both across-track and along-track directions. (Obtained from raw Landsat metadata)
GEOMETRIC_RMSE_MODEL_X	DOUBLE
RMSE (Root Mean Square Error) of the geometric residuals (meters) measured on the GCPs (Ground Control Points) used in geometric precision correction in the across-track direction. (Obtained from raw Landsat metadata)
GEOMETRIC_RMSE_MODEL_Y	DOUBLE
RMSE (Root Mean Square Error) of the geometric residuals (meters) measured on the GCPs (Ground Control Points) used in geometric precision correction in the along-track direction. (Obtained from raw Landsat metadata)
IMAGE_QUALITY	INT
Image quality, 0 = worst, 9 = best, -1 = quality not calculated. (Obtained from raw Landsat metadata)
LANDSAT_ID	STRING
Landsat Product Identifier (Collection 1)
LEVEL1_PRODUCTION_DATE	INT
Date of production for raw Level 1 data as ms since epoch
PIXEL_QA_VERSION	STRING
Version of the software used to produce the 'pixel_qa' band
SATELLITE	STRING
Name of satellite
SENSING_TIME	STRING
Time of the observations as in ISO 8601 string. (Obtained from raw Landsat metadata)
SOLAR_AZIMUTH_ANGLE	DOUBLE
Solar azimuth angle
SR_APP_VERSION	STRING
LaSRC version used to process surface reflectance
WRS_PATH	INT
WRS path number of scene
WRS_ROW	INT
WRS row number of scene
"""

def map_landsat_properties(img):
    property_names = ee.Image(img).propertyNames()
    properties_val = property_names.map(lambda prop: ee.Image(img).get(prop))
    properties_dict = ee.Dictionary.fromLists(property_names,properties_val)
    removed_keys_list = ee.List(["system:bands","system:band_names","system:footprint"])
    properties_dict = properties_dict.remove(removed_keys_list) # remove keys
    return ee.Feature(None,properties_dict)

def check_thailand_intersect_polygon(feature,geometry):
    contain = feature.contains(geometry)
    return ee.Feature(None,{"contain":contain})


def init_ggee():
    try:
        ee.Initialize()
        print("Google Earth Engine has successfully initialized!")
    except ee.EEException:
        ee.Authenticate()
        print("Google Earth Engine has failed to initialize!")
    except:
        print("Unexpected eror:{}".format(sys.exc_info()[0]))
        raise

"""
RESPONSE CODE
200 - OK
500 - INTERNAL ERROR
422 - INVALID INPUT
"""


if __name__ == "__main__":
    app = Flask(__name__)
    init_ggee() # try to initialize earth engine
    THAILAND_GEOM = ee.FeatureCollection(FEATURE_COLLECTION).filterMetadata('country_co', 'equals', 'TH') # geometry of THAILAND_GEOM
    @app.route("/api/v1/th/get/landsatData",methods=["POST"])
    def get_data_from_sat():
        try:
            if request.json is not None: # if data is sent as json data
                data = request.json
            else:
                data = request.form.to_dict()
                data["geo_json"] = json.loads(data["geo_json"])
            geo_json = data.get("geo_json")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            geom_type = geo_json.get("type") # type of geojson
            coordinates = geo_json.get("coordinates") # list of polygon coodinates
            geoJSON_polygon = ee.Geometry.Polygon(coordinates) # Create polygon from geoJSON
            # Check if the polygon is in Thailand or not
            # if not return code 422 and raise error
            features = THAILAND_GEOM.map(lambda feature:check_thailand_intersect_polygon(feature,geoJSON_polygon))
            features_size = features.size()
            features = features.toList(features_size)
            features_list = features.getInfo()
            polygon_in_thailand = True
            # print(features_list)
            for r in features_list:
                contain = r["properties"]["contain"]
                polygon_in_thailand &= contain
            if not polygon_in_thailand:
                print("POLYGON IS NOT IN THAILAND")
                return jsonify({"message":"Your Input polygon is not in thailand.Please try again."}), 422
            print("POLYGON IS IN THAILAND")
            dataset = ee.ImageCollection(IMAGE_COLLECTION)\
                    .filterBounds(geoJSON_polygon)\
                  .filterDate(start_date, end_date)
            results = dataset.map(lambda img: map_landsat_properties(img))  # map data from each sensing time
            collection_size = results.size()  # get collection size
            collection_size = collection_size.toInt().getInfo() # convert server variable to python int
            if collection_size == 0 : # "given date interval does not exist in the dataset"
                return jsonify({"error":"Given date interval does not exist in the dataset.Please try again."}),422
            plist = results.toList(collection_size) # convert to ee.List
            plist = plist.getInfo() # convert to python list
            sorted(plist,key=lambda d: d["properties"]["SENSING_TIME"],reverse=True) # sort from sensing time by ascending order
            response_data = {"message":"success","data":plist}
            return jsonify(response_data), 200
        except Exception as e:
            response_data = {"errors":str(e)}
            return jsonify(response_data),500


#    app.run(host=IP,port=PORT,debug=True,threaded=True,use_reloader=False)
    app.run(host="127.0.0.1",port=3000,debug=True,threaded=True,use_reloader=False)
