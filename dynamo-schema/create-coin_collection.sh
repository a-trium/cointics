 #!/usr/bin/env bash

aws dynamodb create-table \
    --table-name coin_collection \
    --attribute-definitions \
        AttributeName=coin,AttributeType=S \
        AttributeName=last_updated,AttributeType=N \
    --key-schema AttributeName=coin,KeyType=HASH AttributeName=last_updated,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
