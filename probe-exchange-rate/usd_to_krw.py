import logging
import json
from datetime import datetime
from decimal import Decimal

import boto3
from botocore.vendored import requests

yahoo_usd_to_krw_url = 'http://query.yahooapis.com/v1/public/yql?q=select%20%2a%20from%20yahoo.finance.xchange%20where%20pair%20in%20%28%22USDKRW%22%29&format=json&env=store://datatables.org/alltableswithkeys'

def getExchangeRate():
	try:
		response = requests.get(yahoo_usd_to_krw_url)
		response_json = response.json()

		utc_timestamp = datetime.utcnow().replace(microsecond=0).timestamp()
		rate = response_json['query']['results']['rate']['Rate']
		return (utc_timestamp, rate)
	except Error as error:
		logger.error('Fail to get exchange rate from yahoo: %s', error)

def lambda_handler(event=None, context=None):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    isTest = None
    try:
    	isTest = event["isTest"]
    except KeyError:
        logger.info("isTest:{}".format(isTest))

    if isTest:
        logger.addHandler(logging.StreamHandler())

    utc_timestamp, rate = getExchangeRate()

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('exchange_rate')
    logger.info('Rate: "%s", at: "%s"', rate, utc_timestamp)
    
    if isTest is not True:
    	table.put_item(
    		Item = {
    			'usd_to_krw': rate,
    			'timestamp': Decimal(utc_timestamp)
    		}
    	)
