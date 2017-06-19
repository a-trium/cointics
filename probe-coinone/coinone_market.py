import boto3
from botocore.vendored import requests
from datetime import datetime, timedelta, time
from decimal import *
import __main__ as main
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
isTest = main.__file__.endswith(".test.py")

if isTest:
    logger.addHandler(logging.StreamHandler())

API_CURRENCY= "https://api.coinone.co.kr/currency"
API_TICKER = "https://api.coinone.co.kr/ticker?currency=all"
COINS = ["btc", "eth", "etc", "xrp"]

def lambda_handler(event, context):
    r1 = requests.get(API_CURRENCY)
    currency = r1.json()

    if currency["result"] != "success":
        raise Exception("invalid response in coinone currency api. errorcode is " + currency["errorCode"])

    usd_to_krw = currency['currency']

    r2 = requests.get(API_TICKER)
    ticker = r2.json()

    if ticker["result"] != "success":
        raise Exception("invalid response in coinone ticker api. errorcode is " + ticker["errorCode"])

    utcnow = datetime.utcnow()
    dtKstNow = utcnow + timedelta(days=-1, hours=9) # get yesterday's (KST) stat
    dKst = dtKstNow.date()
    dtKstZeroTime = datetime.combine(dtKstNow, time.min)
    tsKstZeroTime = int(dtKstZeroTime.timestamp())

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_market")

    for coin in COINS:
        first_krw = ticker[coin]["first"]
        last_krw = ticker[coin]["last"]
        high_krw = ticker[coin]["high"]
        low_krw = ticker[coin]["low"]
        volume = Decimal(ticker[coin]["volume"])

        if isTest is not True:

            table.put_item(
                Item={
                    "coin": coin,
                    "date": dKst,
                    "timestamp": tsKstZeroTime,
                    "first_krw": first_krw,
                    "last_krw": last_krw,
                    "high_krw": high_krw,
                    "low_krw": low_krw,
                    "volumn": volume,
                    "usd_to_krw": usd_to_krw,
                }
            )

        logger.info("date:{} timestamp:{} first_krw:{} last_krw:{} high_krw:{} low_krw:{} volumn:{} usd_to_krw:{}".format(
            dKst, tsKstZeroTime, first_krw, last_krw, high_krw, low_krw, volume, usd_to_krw
        ))



