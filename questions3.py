import time
from flask import Flask,Response,request,jsonify
import ee
# from constants import THAILAND_BOUNDS,COLLECTION_NAME
import sys

FEARURE_COLLECTION = 'USDOS/LSIB_SIMPLE/2017'
IMAGE_COLLECTION = ""
VIS_PARAMS = {
  "bands": ['B4', 'B3', 'B2'],
  "min": 0,
  "max": 3000,
  "gamma": 1.4,
};

# def maskL8sr(image):
#     cloudShadowBitMask = (1 << 3);
#     cloudsBitMask = (1 << 5);
#     qa = image.select('pixel_qa');
#     mask = qa.bitwiseAnd(cloudShadowBitMask)
#     return image.updateMask(mask);

def init_ggee():
    try:
        ee.Initialize()
        print("Google Earth Engine has successfully initialized!")
    except ee.EEException:
        print("Google Earth Engine has failed to initialize!")
    except:
        print("Unexpected eror:{}".format(sys.exc_info()[0]))
        raise

"""
#CLOUD_COVER	INT
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
    # ee_img = ee.Image(img)
    CLOUD_COVER = ee.Image(img).get("CLOUD_COVER")
    CLOUD_COVER_LAND = ee.Image(img).get("CLOUD_COVER_LAND")
    EARTH_SUN_DISTANCE = ee.Image(img).get("EARTH_SUN_DISTANCE")
    LANDSAT_ID = ee.Image(img).get("LANDSAT_ID")
    PIXEL_QA_VERSION = ee.Image(img).get("PIXEL_QA_VERSION")
    SENSING_TIME = ee.Image(img).get("SENSING_TIME")
    return ee.Feature(None, {
        "CLOUD_COVER":CLOUD_COVER,
        "CLOUD_COVER_LAND":CLOUD_COVER_LAND,
        "EARTH_SUN_DISTANCE":EARTH_SUN_DISTANCE,
        "LANDSAT_ID":LANDSAT_ID,
        "PIXEL_QA_VERSION":PIXEL_QA_VERSION,
        "SENSING_TIME":SENSING_TIME
    })

if __name__ == "__main__":
    app = Flask(__name__)
    init_ggee() # try to initialize earth engine
    THAILAND_GEOM = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'TH') # geometry of THAILAND_GEOM
    @app.route("/api/v1/get/landsat/data",methods=["POST"])
    def get_data_from_sat():
        try:
            geo_json = request.form.get("geo_json")
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")
            try:
                geom_type,coordinates = geo_json["type"] ,geo_json["coordinates"]
            except:
                geom_type,coordinates = "polygon",[ [104.16229248046878,15.234660503970465],
                        [103.96453857421878,14.945606703561904],
                        [104.08538818359378,14.746489691641484],
                        [104.59899902343753,14.746489691641484],
                        [105.01373291015628,15.025201961847722],
                        [104.80499267578128,15.32739214993129],
                        [104.65942382812503,15.369770078523104],
                        [104.16229248046878,15.234660503970465]]
            polygon_region = ee.Geometry.Polygon(coordinates) #
            dataset = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')\
                  .filterBounds(polygon_region)\
                  .filterDate(start_date, end_date)
            results = dataset.map(lambda img: map_landsat_properties(img))
            collection_size = results.size()
            plist = results.toList(collection_size)
            plist = plist.getInfo()
            sorted(plist,key=lambda d: d["properties"]["SENSING_TIME"],reverse=True) # sort from sensing time by ascending order
            response_data = {"message":"success","data":plist}
            return jsonify(response_data), 200
        except Exception as e:
            response_data = {"errors":str(e)}
            return jsonify(response_data),500


    app.run(host="172.17.1.56",port=9999,debug=True,threaded=True,use_reloader=False)