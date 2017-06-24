 #!/usr/bin/env bash

aws dynamodb create-table \
    --table-name coinone_ticker \
    --attribute-definitions \
        AttributeName=coin,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema AttributeName=coin,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
