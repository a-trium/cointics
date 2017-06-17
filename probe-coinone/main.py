import requests
import boto3

currencyAPI = "https://api.coinone.co.kr/currency"
tickerAPI = "https://api.coinone.co.kr/ticker?currency=all"

def lambda_handler(event, context):
    r1 = requests.get(currencyAPI)
    USD2KRW = r1.json()['currency']

    r2 = requests.get(tickerAPI)
    ticker = r2.json()

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('coinone_ticker')

    for coin in ['btc', 'eth', 'etc', 'xrp']:
        table.put_item(
            Item={
                'coin': coin,
                'timestamp': int(ticker['timestamp']),
                'KRW': ticker[coin]['last'],
                'USD2KRW': USD2KRW,
            }
        )
