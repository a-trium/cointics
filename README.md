# cointics 

Toy Project
 
- build data pipeline using AWS
  * collects alt coin dataset using public APIs provided by exchanges (lambda -> dynamo)
  * create summary table (dynamo -> dynamo)
  * backup old logs (dynamo -> s3)
- send some notifications to slack
- webapp hosted in firebase 

## Structure

| Module | Description |
| --- | --- |
| probe-* | lambda funcs which collect data |
| notification-* | lambda funcs notify events to slack or somewhere |
| *-schema | scripts for creating s3 buckets, dynamo tables, and so on |
| transfer | backup lambda funcs from dynamo to s3 |
| api | api gateway conf, lambda funcs |  

## Requirements

| Name | Version |
| --- | --- |
| Python | 3.6.1+ |
| Node | 6.9.0+ |

