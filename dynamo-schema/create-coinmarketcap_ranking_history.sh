 #!/usr/bin/env bash

aws dynamodb create-table \
    --table-name coinmarketcap_ranking_history \
    --attribute-definitions \
        AttributeName=coin,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema AttributeName=coin,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
