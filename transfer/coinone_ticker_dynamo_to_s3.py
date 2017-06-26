import boto3
from botocore.vendored import requests
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone, timedelta
from dateutil import tz
from decimal import *
import json
import logging
import os


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def create_tsv_row(columns):
    line = ""
    for c in columns[:-1]:
        line += c + "\t"
    line += str(columns[-1]) # last column

    # newline will be added by the caller
    return line


def write_with_newline(f, text):
    f.write("{}\n".format(text))


def get_datetime_kst_now():
    return datetime.now(timezone.utc).astimezone(tz.gettz("Asia/Seoul"))


def get_datetime_kst_2days_ago(dtKst):
    dtKst = dtKst.replace(hour=0, minute=0, second=0, microsecond=0)
    dtKst += timedelta(days=-2)
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
    dtKstStart = get_datetime_kst_now()
    if isTest:
        dStrKstStart = event["testParams"]["dStrKstStart"]
        dtKstStart = datetime.strptime(dStrKstStart, "%Y-%m-%d").replace(
            tzinfo=tz.gettz("Asia/Seoul"))

    dtKstFrom = get_datetime_kst_2days_ago(dtKstStart)
    tsKstFrom = dtKstFrom.timestamp()
    dKstFrom = dtKstFrom.date()
    dtKstUntil = dtKstFrom + timedelta(days=+1)
    tsKstUntil = dtKstUntil.timestamp()
    dKstUntil = dtKstUntil.date()

    logger.info("dtKstStart:{} dtKstFrom :{} dtKstUntil:{} dKstFrom:{} dKstUntil:{} tsKstFrom:{} tsKstUntil:{}".format(
        dtKstStart, dtKstFrom, dtKstUntil, dKstFrom, dKstUntil, tsKstFrom, tsKstUntil))

    # get rows
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_ticker")

    result = table.scan(
        ProjectionExpression="#ts, date_kst, coin, price_krw",
        ExpressionAttributeNames={ "#ts": "timestamp", },
        FilterExpression=Key("timestamp").gte(Decimal(tsKstFrom)) & Key("timestamp").lt(Decimal(tsKstUntil)),
    )

    logger.info("Count:{} ScannedCount:{} HTTPStatusCode:{}".format(
        result["Count"], result["ScannedCount"], result["ResponseMetadata"]["HTTPStatusCode"]
    ))

    # write a temporary file to /tmp/dynamo_backup.csv
    tmpFileName = "/tmp/dynamo_backup.csv"

    try:
        os.remove(tmpFileName)
    except FileNotFoundError:
        logger.info("File doesn't exist, ignoring")

    if result["Count"] == 0:
        logger.info('result["Count"] == 0, exit')
        exit(0)

    rows = result["Items"]
    header = create_tsv_row(list(rows[0].keys()))
    logger.info("header:{}".format(header))

    f = open(tmpFileName, "w", encoding="utf-8")
    write_with_newline(f, header)

    # row is a dict
    counter = 0
    for row in rows:
        line = create_tsv_row(list(row.values()))
        write_with_newline(f, line)

        if counter < 5:
            logger.info("sampleRow:{}".format(line))
        counter += 1

    f.close()

    # set isTest false here if you want to do some operational tasks
    # isTest = False

    # store rows into s3
    bucketPath = "coinone_ticker/{dt:%Y}-{dt:%m}-{dt:%d}/log.tsv".format(dt=dKstFrom)
    if isTest:
        bucketPath = "test/coineone_ticker_{dt:%Y}-{dt:%m}-{dt:%d}.tsv".format(dt=dKstFrom)
    logger.info("bucketPath:{}".format(bucketPath))

    s3 = boto3.resource('s3')
    s3.Object("hamburg-ticker", bucketPath).put(Body=open(tmpFileName, "rb"))

    if isTest is not True:
        logger.info("Deleting table from {} until {} (KST)".format(dKstFrom, dKstUntil))
        with table.batch_writer(overwrite_by_pkeys=['timestamp', 'coin']) as batch:
            for row in rows:
                batch.delete_item(
                    Key={ 'timestamp': Decimal(row['timestamp']), 'coin': row['coin'], }
                )

