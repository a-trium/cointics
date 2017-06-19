import coinone_market_api

# mock for lambda func arguments
queryStringParameters = { "from": "2017-06-17", "to": "2017-06-18" }
event = { "queryStringParameters": queryStringParameters }

result = coinone_market_api.lambda_handler(event, None)
print(result)