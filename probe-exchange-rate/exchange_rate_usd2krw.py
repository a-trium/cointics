import boto3
from botocore.vendored import requests
from datetime import datetime, timezone, timedelta
from dateutil import tz
from decimal import Decimal
import json
import logging


yahoo_usd_to_krw_url = 'http://query.yahooapis.com/v1/public/yql?q=select%20%2a%20from%20yahoo.finance.xchange%20where%20pair%20in%20%28%22USDKRW%22%29&format=json&env=store://datatables.org/alltableswithkeys'


def create_tsv_row(columns):
    line = ""
    for c in columns[:-1]:
        line += str(c) + "\t"
    line += str(columns[-1]) # last column

    # newline will be added by the caller
    return line


def write_with_newline(f, text):
    f.write("{}\n".format(text))


def get_datetime_kst_now():
    return datetime.now(timezone.utc).astimezone(tz.gettz("Asia/Seoul"))


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

    dt_kst_now = get_datetime_kst_now().replace(second=0, microsecond=0)
    timestamp = int(dt_kst_now.timestamp())
    rate = None

    try:
        response = requests.get(yahoo_usd_to_krw_url).json()
        logger.info("response: {}".format(response))
        rate = round(float(response['query']['results']['rate']['Rate']), 2)
    except Exception as e:
        logger.error("Failed to get response from yahoo currency api", e)
        exit(1)

    data = { "timestamp": timestamp, "rate": rate, }
    logger.info("timestamp:%s rate:%s", timestamp, rate)

    # write a temp file
    tmp_file_name = "/tmp/exchange_rate.tsv"
    f = open(tmp_file_name, "w", encoding="utf-8")
    write_with_newline(f, create_tsv_row(list(data.keys())))
    write_with_newline(f, create_tsv_row(list(data.values())))
    f.close()

    bucket_path = "test/exchange_rate_{dt:%Y}-{dt:%m}-{dt:%d}.tsv".format(dt=dt_kst_now)
    if is_test is not True:
        bucket_path = "exchange_rate/usd_to_krw.tsv"
    logger.info("bucket_path:{}".format(bucket_path))

    # store rows into s3
    s3 = boto3.resource('s3')
    s3.Object("cointics", bucket_path).put(Body=open(tmp_file_name, "rb"))

