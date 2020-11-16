#!/usr/bin/env python3
import csv, os
#pip install python-slugify
from slugify import slugify
import json

origem = '/home/phakawat/thailand.csv'
destino = 'file.sql'
arquivo = os.path.abspath(origem)
# d = open(destino,'w')
with open(origem,'r') as f:
    header = f.readline().split(',')
    head_cells = []
    for cell in header:
        value = slugify(cell,separator="_")
        if value in head_cells:
            value = value+'_2'
        head_cells.append(value)
    #cabecalho = "{}\n".format(';'.join(campos))

    #print(cabecalho)
    fields= []
    data_types=[
        "text", # system:index
        "float", # cloud cover
        "float", # cloud cover land
        "float", # earth sun distance
        "text", # espa version
        "float", # geometric_rmse_model
        "float", # GEOMETRIC_RMSE_MODEL_X
        "float", # GEOMETRIC_RMSE_MODEL_Y
        "float", # IMAGE_QUALITY_OLI
        "float", # IMAGE_QUALITY_TIRS
        "text", # LANDSAT_ID
        "text", # LEVEL1_PRODUCTION_DATE
        "text", # PIXEL_QA_VERSION
        "text", # SATELLITE
        "timestamp", # SENSING_TIME
        "float", # SOLAR_AZIMUTH_ANGLE
        "float", # SOLAR_ZENITH_ANGLE
        "text", # SR_APP_VERSION
        "float", # WRS_PATH
        "float", # WRS_ROW
        "int", # system:asset_size
        "text", # system:band_names
        "text", # system:bands
        "text", # system:footprint
        "text", # system:id
        "text", # system:time_start
        "text", # system:version,
        "json" # geo

    ]
    for i,cell in enumerate(head_cells):
        print(cell , data_types[i])
        fields.append(" {} {}".format(cell,data_types[i]))
    table = origem.split('.')[0]
    sql = "create table {} ( \n {} \n);".format(origem.split('.')[0],",\n".join(fields))
    sql += "\n COPY {} FROM '{}' DELIMITER ',' CSV HEADER;".format(table,arquivo)
    # print(sql)
    # d.write(sql)