import boto3
from botocore.vendored import requests
from datetime import datetime, timedelta
import __main__ as main
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
isTest = main.__file__.endswith(".test.py")

if isTest:
    logger.addHandler(logging.StreamHandler())

API_TICKER = "https://api.coinone.co.kr/ticker?currency=all"
COINS = ["btc", "eth", "etc", "xrp"]

def lambda_handler(event, context):
    r = requests.get(API_TICKER)
    ticker = r.json()

    if ticker["result"] != "success":
        raise Exception("invalid response in coinone ticker api. errorcode is " + ticker['errorCode'])

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_ticker")

    utcnow = datetime.utcnow()
    time_gap = timedelta(hours=9)
    kor_time = utcnow + time_gap
    date = kor_time.strftime('%Y-%m-%d')

    for coin in COINS:
        timestamp = int(ticker["timestamp"])
        price_krw = ticker[coin]["last"]

        if isTest is not True:
            table.put_item(
                Item={
                    "coin": coin,
                    "timestamp": timestamp,
                    "date": date,
                    "price_krw": price_krw,
                }
            )

        logger.info("coin:{} date:{} timestamp:{}, price_krw:{}".format(
            coin, date, timestamp, price_krw
        ))
