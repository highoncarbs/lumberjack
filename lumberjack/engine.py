import os
import sys 
# import redis
# from celery import Celery
# from celery.result import AsyncResult
from pyspark import SparkContext
from pyspark.sql import SparkSession , SQLContext
import json 

# celery = Celery("lumberjack" , broker = 'redis://localhost:6379/0')

sc = SparkContext()
sc.setLogLevel("WARN")
sqlcontext = SQLContext(sc)

# Celery Task

# @celery.task(bind=True)
def log_process(data_file_path , result_file_path):

	print("Inside the log procress")
	# task_id = self.request.id 
	filepath = data_file_path 
	resultpath =   result_file_path
	log_file = sqlcontext.read.text(filepath)

	# Data Clean , Later refactor the code for Celery

	from pyspark.sql.functions import split, regexp_extract
	split_df = log_file.select(regexp_extract('value', r'^([^\s]+\s)', 1).alias('host'),
                        regexp_extract('value', r'^.*\[(\d\d/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} -\d{4})]', 1).alias('timestamp'),
                        regexp_extract('value', r'^.*"\w+\s+([^\s]+)\s+HTTP.*"', 1).alias('path'),
                        regexp_extract('value', r'^.*"\s+([^\s]+)', 1).cast('integer').alias('status'),
                        regexp_extract('value', r'^.*\s+(\d+)$', 1).cast('integer').alias('content_size'))

	# NUll COntent Values
	null_content = (split_df.filter(split_df["content_size"].isNull())
						.groupby( "status").count()).show(10)

	# Further cleanning of Null values
	cleaned_df = split_df.na.fill( 0 )
	cleaned_df.cache()

	from pyspark.sql.functions import desc

	# Getting the Error Log lines 

	# Top Accessed files 

	top_files = cleaned_df.groupby("path").count().sort(desc("count")).take(10)

	# Frequently Accessed html pages

	top_pages = cleaned_df.filter(cleaned_df["path"].rlike('html'))
	top_10_pages = top_pages.groupby('path').count().sort(desc('count')).take(1)
     

	# Top IP hits
	top_ip = cleaned_df.groupby("host").count().sort(desc('count')).take(10)
	# JSON File template

	data = {}
	data['top_10_pages'] = []
	for row in top_10_pages:
		data['top_10_pages'].append({
		'name' : row['path'],
		'value' : row['count']
		})

	data['top_files'] = []
	for row in top_files:
		data['top_files'].append({
		'name' : row['path'],
		'value' : row['count']
		})

		data['top_ip'] = []
	for row in top_ip:
		data['top_ip'].append({
		'name' : row['host'],
		'value' : row['count']
		})
    

	with open(resultpath, 'w') as outfile:  
		json.dump(data, outfile)
		print('Success')

	return('Success')

if __name__ == "__main__":
	log_process()