import boto3
from botocore.vendored import requests
import __main__ as main
import datetime

API_TICKER = "https://api.coinone.co.kr/ticker?currency=all"
COINS = ["btc", "eth", "etc", "xrp"]

def lambda_handler(event, context):
    r = requests.get(API_TICKER)
    ticker = r.json()

    if ticker["result"] != "success":
        raise Exception("invalid response in coinone ticker api. errorcode is " + ticker['errorCode'])

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_ticker")

    utcnow = datetime.datetime.utcnow()
    time_gap = datetime.timedelta(hours=9)
    kor_time = utcnow + time_gap
    date = kor_time.strftime('%Y-%m-%d')

    for coin in COINS:
        timestamp = int(ticker["timestamp"])
        price_krw = ticker[coin]["last"]

        isTest = main.__file__.endswith(".test.py")
        if isTest is not True:
            table.put_item(
                Item={
                    "coin": coin,
                    "timestamp": timestamp,
                    "date": date,
                    "price_krw": price_krw,
                }
            )

        print("coinone", coin, date, timestamp, price_krw, "KRW")



