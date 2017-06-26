import boto3
from botocore.vendored import requests
import json
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone, timedelta
from dateutil import tz
from decimal import *
import os
import logging

api_coinone_currency = "https://api.coinone.co.kr/currency"
coinone_coins = ["BTC", "ETH", "ETC", "XRP"]
webhook_url = os.getenv("SLACK_WEBHOOK_URL")


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
    dtKst = get_datetime_kst_now()
    ts = dtKst.timestamp()
    dKst = dtKst.strftime('%Y-%m-%d')
    tKst = dtKst.strftime('%H:%M')

    logger.info("dtKst:{} dKst:{} tKst: {} timestamp:{}".format(dtKst, dKst, tKst, ts))

    # get currenct from coinone
    # r1 = requests.get(api_coinone_currency)
    # currency = r1.json()
    # if currency["result"] != "success":
    #     raise Exception("invalid response in coinone currency api. errorcode is " + currency["errorCode"])
    # usd_to_krw = currency['currency']

    # get tables
    dynamodb = boto3.resource('dynamodb')
    table_coinone_ticker = dynamodb.Table('coinone_ticker')
    table_coinmarketcap_ticker = dynamodb.Table('coinmarketcap_ticker')

    # get tickers for coins in coinone_ticker table
    coinone_ticker = {}
    for c in coinone_coins:
        result = table_coinone_ticker.query(
            KeyConditionExpression=Key('coin').eq(c),
            ScanIndexForward=False,
            Limit= 1,
        )

        if len(result["Items"]) > 0:
            coinone_ticker[c] = result["Items"][0]

        logger.info("{} coinone items: {}".format(c, result["Items"]))

    # get tickers for coins in coinmarketcap_table
    coinmarketcap_ticker = {}
    for c in coinone_coins:
        result = table_coinmarketcap_ticker.query(
            KeyConditionExpression=Key('coin').eq(c),
            ScanIndexForward=False,
            Limit= 1,
        )

        if len(result["Items"]) > 0:
            coinmarketcap_ticker[c] = result["Items"][0]

        logger.info("{} coinmarketcap items: {}".format(c, result["Items"]))

    slack_text = "[{} KST]\n".format(tKst)
    for c in coinone_coins:
        if c not in coinone_ticker or c not in coinmarketcap_ticker:
            continue

        coinone_price = Decimal(coinone_ticker[c]["price_krw"])
        coinmarketcap_price = Decimal(coinmarketcap_ticker[c]["price_krw"])
        price_diff_percent = coinone_price / coinmarketcap_price * 100 - 100
        price_diff_percent = round(price_diff_percent, 2)
        logger.info("{} {}".format(coinone_price, coinmarketcap_price))

        if price_diff_percent > 0:
            price_diff_percent = "+{}".format(price_diff_percent)
        slack_text += "{} : *{}%* (co: {:,}, cmkc: {:,})\n".format(
            c, price_diff_percent, coinone_price, round(coinmarketcap_price, 0)
        )

    logger.info(slack_text)

    if isTest is True:
        return

    response = requests.post(
        webhook_url, data=json.dumps({ "text": slack_text, }),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        logger.error("Failed to send slack message: {}".format(slack_text))
        logger.error("Status Code: {}".format(response.status_code))
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
