import boto3
from botocore.vendored import requests
from datetime import datetime, timezone, timedelta
from dateutil import tz
from decimal import *
import logging

API_CURRENCY= "https://api.coinone.co.kr/currency"
API_TICKER = "https://api.coinone.co.kr/ticker?currency=all"
COINS = ["btc", "eth", "etc", "xrp"]


def get_datetime_kst_now():
    return datetime.now(timezone.utc).astimezone(tz.gettz("Asia/Seoul"))


def get_datetime_kst_yesterday():
    dtKst = get_datetime_kst_now()
    dtKst = dtKst.replace(hour=0, minute=0, second=0, microsecond=0)
    dtKst += timedelta(days=-1)
    return dtKst


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

    # build datetime: batch job for yesterday
    dtKst = get_datetime_kst_yesterday()
    ts = dtKst.timestamp()
    dKst = dtKst.strftime('%Y-%m-%d')

    logger.info("dtKst:{} dKst:{} timestamp:{}".format(dtKst, dKst, ts))

    # sent request to get currency info
    r1 = requests.get(API_CURRENCY)
    currency = r1.json()

    if currency["result"] != "success":
        raise Exception("invalid response in coinone currency api. errorcode is " + currency["errorCode"])

    usd_to_krw = currency['currency']

    # sent request to get volume
    r2 = requests.get(API_TICKER)
    ticker = r2.json()

    if ticker["result"] != "success":
        raise Exception("invalid response in coinone ticker api. errorcode is " + ticker["errorCode"])

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_market")

    for coin in COINS:
        first_krw = ticker[coin]["first"]
        last_krw = ticker[coin]["last"]
        high_krw = ticker[coin]["high"]
        low_krw = ticker[coin]["low"]
        volume = Decimal(ticker[coin]["volume"])

        logger.info("first_krw:{} last_krw:{} high_krw:{} low_krw:{} volumn:{} usd_to_krw:{}".format(
            first_krw, last_krw, high_krw, low_krw, volume, usd_to_krw
        ))

        if isTest is not True:

            table.put_item(
                Item={
                    "coin": coin,
                    "date_kst": dKst,
                    "timestamp": Decimal(ts),
                    "first_krw": first_krw,
                    "last_krw": last_krw,
                    "high_krw": high_krw,
                    "low_krw": low_krw,
                    "volumn": volume,
                    "usd_to_krw": usd_to_krw,
                }
            )
