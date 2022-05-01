# LeakLooker X - GUI
## Powered by Binary Edge

### Discover, browse and monitor database/source code leaks

https://www.offensiveosint.io/offensive-osint-so1e07-offensive-leak-hunt-with-leaklooker

https://www.offensiveosint.io/leaklooker-gui-discover-browse-and-monitor-database-source-code-leaks/

![](https://www.offensiveosint.io/content/images/2020/06/LL-1.jpg)


![](https://www.offensiveosint.io/content/images/2020/06/types.jpg)

# Supported sources
- Gitlab
- Elasticsearch
- Kibana
- Sonarqube
- Kibana
- Jenkins
- MongoDB
- Rsync
- Listing directory
- Cassandra
- CouchDB
- RethinkDB
- Anonymous FTP
- S3 bruteforce
- Open S3 buckets
- Buckets in HTML
- Github (Secrets)
- API keys in HTML
- Angular applications
- Javascript (Secrets)

# Requirements
- python3
- Binary Edge paid plan
- django
- celery
- redis
- BeautifulSoup
- jsbeautifier

~~~
pip install -r requirements.txt
sudo apt-get install python3-jsbeautifier
sudo pip3 install celery-progress hurry-filesize jxmlease
~~~ 

# Install & Run
- Paste your Binary Edge api key into config.json
- Paste your gmail email and password in case you want to use monitoring feature
```
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver
```

n a new window fire up redis 

```apt-get install redis redis-server```

```redis-server```

In a new window (in main directory) run 

```celery -A leaklooker worker --loglevel=info```

For scheduling task (monitoring) run also 

```celery -A leaklooker beat --loglevel=info```

I

And server should be available on https://localhost:8000/

# Guide

Useful commands https://github.com/woj-ciech/LeakLooker-X/blob/master/cheatsheet.md

## Dashboard
![](https://i.imgur.com/IlVRBW1.jpg)

![](https://i.imgur.com/a4vuOZA.jpg)

Dashboard shows chart of retrieved databases by type

Number of confirmed/for later findings 

Binary Edge credits and total amount of records in database

Progress of checking MongoDB/Cassandra/Rethink/Elastic (% of findings marked as confirmed or for later)

Random leaks by type (not confirmed nor marked for later)

Findings marked "for later" for the same random type

Notifications

## Discover
- by type
![](https://i.imgur.com/8AMhN67.jpg)

Orange "count" button counts amount of records in your database

Blue "count" button counts amount in Binary Edge

- by keyword & network & all types at once
![](https://i.imgur.com/Hxnp7ZT.jpg)

If there are no results (due to blacklist or they are already in db) you will be informed

![](https://i.imgur.com/sTwXFCq.jpg)

## Browse
- by type (recommended)
![](https://i.imgur.com/959Qja5.jpg)

- whole database
![](https://i.imgur.com/93xseqb.jpg)

Red button deletes record and put it in blacklist so it will be never displayed again

Green button confirms finding

Blue button marks it as "for later review"

## Monitor

It will sent mail every 24 hours with new findings based on provided keywords/network.

It compares new results with database and blacklist and sends only new findings.

![](https://i.imgur.com/Ohws6rn.jpg)

![](https://i.imgur.com/lzzat3a.jpg)

## Screens
![](https://www.offensiveosint.io/content/images/2020/06/peek1-1.gif)



# Queries
```
"gitlab": "title:%22gitlab%22%20AND%20web.body.content:%22register%22",
"elastic": "type:%22elasticsearch%22",
"dirs": "title:%22Index of /%22",
"jenkins": "title:%22Dashboard [Jenkins]%22",
"mongo": "type:%22mongodb%22",
"rsync": "port:873 @RSYNCD",
'sonarqube': "title:SonarQube",
'couchdb': "product:couchdb",
"kibana": "product:kibana",
"cassandra": "type:cassandra",
"rethink": "type:rethinkdb",
"ftp":"ftp.user:anonymous",
"asia":"tag:'webserver' s3.ap-southeast-1.amazonaws.com",
"europe":"tag:'webserver' s3-eu-west-1.amazonaws.com",
"north america":"tag:'webserver' s3-us-west-2.amazonaws.com",
"api_key":'web.body.content:"api_key" -web.title:swagger',
"stripe":'web.body.content:"STRIPE_KEY"',
"secret_key":'web.body.content:"secret_key" -web.title:swagger',
'google_api_key':'web.body.content:"google_api_key"'
'amazons3be':'web.body.content:ListBucketResult',
'angular':"web.body.content:polyfills web.body.content:main web.body.content:runtime"
```

# Additional
- I am not responsible for any damage caused by using the tool
- You must login to the gmail account via browser first to use monitoring
- If something does not work or you have an idea raise an issue
- Tested on Kali Linux on newest browser
- All credits for template goes to ColorLib
