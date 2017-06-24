 #!/usr/bin/env bash

aws dynamodb create-table \
    --table-name coinone_market \
    --attribute-definitions \
        AttributeName=coin,AttributeType=S \
        AttributeName=date_kst,AttributeType=S \
    --key-schema AttributeName=coin,KeyType=HASH AttributeName=date_kst,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
