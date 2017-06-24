import boto3
from botocore.vendored import requests
from datetime import datetime, timezone
from dateutil import tz
from decimal import *
import logging

ticker_api = "https://api.coinmarketcap.com/v1/ticker/?convert=KRW"
coin_id_to_symbol = {
    "bitcoin": "btc",
    "ethereum": "eth",
    "ripple": "xrp",
    "litecoin": "ltc",
    "ethereum-classic": "xem",
    "iota": "miota",
    "dash": "dash",
    "bitshares": "bts",
    "stratis": "strat",
    "monero": "xmr",
    "zcash": "zec",
    "golem-network-tokens": "gnt",
    "waves": "waves",
    "steem": "steem",
}


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
    timestamp = Decimal(dtKstNow.timestamp())
    dKst = dtKstNow.strftime('%Y-%m-%d')
    logger.info("dtKstNow:{} dKst:{}".format(dtKstNow, dKst))

    r = requests.get(ticker_api)
    tickers = r.json()

    if len(tickers) <= 0:
        raise Exception("invalid response in coinmarketcap ticker api. len is " + len(tickers))

    logger.info("{} coins are registered in the market".format(len(tickers)))

    if isTest is not True:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("coinmarketcap_ticker")
        with table.batch_writer() as batch:
            for ticker in tickers:

                batch.put_item(
                    Item={
                        'coin': ticker["symbol"].upper(),
                        'timestamp': timestamp,
                        'id': ticker["id"],
                        'rank': ticker["rank"],
                        'price_usd': ticker["price_usd"],
                        'price_btc': ticker["price_btc"],
                        'price_krw': ticker["price_krw"],
                        'available_supply': ticker["available_supply"],
                        'total_supply': ticker["total_supply"],
                    }
                )
