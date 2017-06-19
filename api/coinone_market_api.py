import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from datetime import datetime, timedelta
from datetime import timezone
import decimal
from decimal import *
import __main__ as main
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
isTest = main.__file__.endswith(".test.py")

if isTest:
    logger.addHandler(logging.StreamHandler())

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    # use querystring provided by lambda proxy integration
    queryDateFrom = event["queryStringParameters"]["from"]
    queryDateTo = event["queryStringParameters"]["to"]

    dtUtcFrom = datetime.strptime(queryDateFrom, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    # add 1d to represent `until`
    dtUtcUntil= datetime.strptime(queryDateTo, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)

    # requested date is GMT+9
    dtKstFrom = dtUtcFrom + timedelta(hours=-9)
    dtKstUntil = dtUtcUntil + timedelta(hours=-9)
    tsKstFrom = int(dtKstFrom.timestamp())
    tsKstUntil = int(dtKstUntil.timestamp())

    logger.info("dateKstFrom:{} dateKstTo:{} timestampKstFrom:{} timestampKstUntil:{}".format(
        dtKstFrom.date(), dtKstUntil.date(), tsKstFrom, tsKstUntil
    ))

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("coinone_market")

    result = table.scan(
        ProjectionExpression="#ts, #dt, coin, high_krw, low_krw, usd_to_krw, volumn",
        ExpressionAttributeNames={ "#dt": "date" , "#ts": "timestamp", },
        FilterExpression=Key('timestamp').gte(Decimal(tsKstFrom)) & Key('timestamp').lt(Decimal(tsKstUntil)),
    )

    logger.info("Count:{} ScannedCount:{} HTTPStatusCode:{}".format(
        result["Count"], result["ScannedCount"], result["ResponseMetadata"]["HTTPStatusCode"]
    ))

    # rerturn format for lambda proxy integration
    return {
        "statusCode": 200,
        'headers': { 'Content-Type': 'application/json', },
        "body": json.dumps(result["Items"], cls=DecimalEncoder),
    }