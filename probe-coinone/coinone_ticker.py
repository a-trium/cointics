import boto3
from botocore.vendored import requests
from datetime import datetime, timezone
from dateutil import tz
from decimal import *
import logging

API_TICKER = "https://api.coinone.co.kr/ticker?currency=all"
COINS = ["btc", "eth", "etc", "xrp"]


def get_datetime_kst_now():
    return datetime.now(timezone.utc).astimezone(tz.gettz("Asia/Seoul"))


def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    isTest = None
    try:
        isTest = event["isTest"]
    except KeyError:
        logger.info("isTest:{}".format(isTest))

    if isTest:
        logger.addHandler(logging.StreamHandler())

    dtKstNow = get_datetime_kst_now()
    dKst = dtKstNow.strftime('%Y-%m-%d')
    logger.info("dtKstNow:{} dKst:{}".format(dtKstNow, dKst))

    r = requests.get(API_TICKER)
    ticker = r.json()

    if ticker["result"] != "success":
        raise Exception("invalid response in coinone ticker api. errorcode is " + ticker['errorCode'])

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_ticker")

    for coin in COINS:
        timestamp = Decimal(ticker["timestamp"])
        price_krw = ticker[coin]["last"]

        logger.info("coin:{} timestamp:{}, price_krw:{}".format(
            coin.upper(), timestamp, price_krw
        ))

        if isTest is not True:
            table.put_item(
                Item={
                    "coin": coin.upper(),
                    "timestamp": timestamp,
                    "date_kst": dKst,
                    "price_krw": price_krw,
                }
            )
