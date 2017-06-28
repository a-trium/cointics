import logging
import json
from datetime import datetime
from decimal import Decimal

import boto3
from botocore.vendored import requests

yahoo_usd_to_krw_url = 'http://query.yahooapis.com/v1/public/yql?q=select%20%2a%20from%20yahoo.finance.xchange%20where%20pair%20in%20%28%22USDKRW%22%29&format=json&env=store://datatables.org/alltableswithkeys'


def get_exchange_rate(logger):
    try:
        response = requests.get(yahoo_usd_to_krw_url).json()
        rate = response['query']['results']['rate']['Rate']
        return rate
    except Exception as e:
        logger.error("Failed to get response from yahoo currency api", e)
        logger.info("response:{}".format(response))
        exit(1)

def lambda_handler(event=None, context=None):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    is_test = None

    try:
        is_test = event["isTest"]
    except KeyError:
        logger.info("isTest:{}".format(is_test))

    if is_test:
        logger.addHandler(logging.StreamHandler())

    timestamp = int(datetime.utcnow().replace(microsecond=0).timestamp())
    rate = get_exchange_rate(logger)

    logger.info("timestamp:%s rate:%s", timestamp, rate)
    
    if is_test is not True:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('exchange_rate')
        table.put_item(
            Item={
                'usd_to_krw': rate,
                'timestamp': Decimal(timestamp)
            }
        )
