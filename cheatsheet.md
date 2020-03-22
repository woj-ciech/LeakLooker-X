# Rsync
``````
rsync -az IP:/module ~/ — progress

rsync — list-only IP:/

rsync -avrz /opt/data/filename root@ip:/opt/data/file
``````
# CouchDb
```
/_all_dbs

<db>/_all_docs?include_docs=true&limit=50

/<db>/doc?rev=<nr>

<db>/doc

<db>/doc/<name>

/<db>/<docid>

/<db>/<id>/<attachment_id>
```
# MongoDB
``````
show databases

use ‘db’

show collections

db.’collection’.stats()

db.’collection’.findOne()

db.’collection’.find().prettyPrint()

db.’collection’.find()
``````
# Elastic
``````
_cat/nodes?v

_cat/count?v

<indices>/_search?size=50
``````