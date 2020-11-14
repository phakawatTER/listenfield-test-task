import pandas as pd
import numpy as np
import os

abs_path = os.path.dirname(os.path.abspath(__file__)) # absolute path to project directory
chunk_path = os.path.join(abs_path,"data_chunks")
if not os.path.exists(chunk_path):
    os.mkdir(chunk_path) # create directory if not exits
dataset_path = os.path.join(abs_path,"583201.WTD") # path to dataset
chunk_size = 1000 # chunk size
"""TODO:load data into chunks of size 1000 rows each"""
for batch_no,chunk in enumerate(pd.read_table(dataset_path,chunksize=chunk_size)):
    chunk_name = "chunk{}.csv".format(batch_no)
    chunk.to_csv(os.path.join(chunk_path,chunk_name),index=False)

