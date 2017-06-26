import coinone_ticker_dynamo_to_s3

event = { "isTest": False, "testParams": {}, }
event["testParams"] = { "dStrKstStart": "2017-06-27", }

coinone_ticker_dynamo_to_s3.lambda_handler(event, None)
