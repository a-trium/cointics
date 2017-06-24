import coinone_ticker_dynamo_to_s3

event = { "isTest": True, "testParams": {}, }
event["testParams"] = { "dStrKstFrom": "2017-06-21", }

coinone_ticker_dynamo_to_s3.lambda_handler(event, None)
