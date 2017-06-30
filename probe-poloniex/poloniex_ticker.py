import boto3
from botocore.vendored import requests
from datetime import datetime, timezone
from dateutil import tz
from decimal import *
import logging

ticker_api = "https://poloniex.com/public?command=returnTicker"
available_currency = {
    "BTC": "USDT_BTC",
    "ETH": "USDT_ETH",
    "ETC": "USDT_ETC",
    "XRP": "USDT_XRP",
    "LTC": "USDT_LTC",
    "DASH": "USDT_DASH",
    "NXT": "USDT_NXT",
    "STR": "USDT_STR",
    "XMR": "USDT_XMR",
    "REP": "USDT_REP",
    "ZEC": "USDT_ZEC",
}


def get_datetime_kst_now():
    return datetime.now(timezone.utc).astimezone(tz.gettz("Asia/Seoul"))


def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    is_test = False
    try:
        is_test = event["isTest"]
    except KeyError:
        logger.info("isTest:{}".format(is_test))

    if is_test:
        logger.addHandler(logging.StreamHandler())

    dt_kst_now = get_datetime_kst_now().replace(second=0, microsecond=0)
    dt_str_kst = dt_kst_now.strftime("%Y-%m-%d %H:%M:%S")
    timestamp = Decimal(int(dt_kst_now.timestamp()))
    logger.info("datetime_kst:{} timestamp:{}".format(dt_kst_now, timestamp))

    r = requests.get(ticker_api)
    tickers = r.json()

    if len(tickers) <= 0:
        logger.error("invalid response in poloniex ticker api. len is " + len(tickers))
        exit(1)

    coins = list(available_currency.keys())

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("poloniex_ticker")

    with table.batch_writer() as batch:
        for coin in coins:

            currency = available_currency[coin]
            price_usd = tickers[currency]["lowestAsk"] # use lowestAsk as price
            volume = tickers[currency]["quoteVolume"]
            bid = tickers[currency]["highestBid"]
            ask = tickers[currency]["lowestAsk"]
            percent_change_price_usd = tickers[currency]["percentChange"]

            logger.info("coin:{} currency:{} price_usd:{} volume:{} ask:{} bid:{} percent_change_price_usd:{}".format(
                coin, currency, price_usd, volume, ask, bid, percent_change_price_usd
            ))

            if is_test is not True:
                batch.put_item(
                    Item={
                        'coin': coin,
                        'timestamp': timestamp,
                        'datetime_kst': dt_str_kst,
                        'price_usd': price_usd,
                        'volume': volume,
                        'ask': ask,
                        'bid': bid,
                        'percent_change_price_usd': percent_change_price_usd,
                    }
                )
