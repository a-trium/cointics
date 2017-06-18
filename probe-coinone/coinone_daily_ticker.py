import boto3
from botocore.vendored import requests
import __main__ as main
import datetime
from decimal import *

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

    utcnow = datetime.datetime.utcnow()
    time_gap = datetime.timedelta(hours=9)
    kor_time = utcnow + time_gap
    date = kor_time.strftime('%Y-%m-%d')

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_daily_ticker")

    for coin in COINS:
        timestamp = int(ticker["timestamp"])
        first_krw = ticker[coin]["first"]
        last_krw = ticker[coin]["last"]
        high_krw = ticker[coin]["high"]
        low_krw = ticker[coin]["low"]
        volume = Decimal(ticker[coin]["volume"])

        isTest = main.__file__.endswith(".test.py")
        if isTest is not True:

            table.put_item(
                Item={
                    "coin": coin,
                    "date": date,
                    "timestamp": timestamp,
                    "first_krw": first_krw,
                    "last_krw": last_krw,
                    "high_krw": high_krw,
                    "low_krw": low_krw,
                    "volumn": volume,
                    "usd_to_krw": usd_to_krw,
                }
            )

        print("coinone", date, timestamp, first_krw, last_krw, high_krw, low_krw, volume, usd_to_krw)



