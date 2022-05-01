from celery import shared_task
import logging
import json
import requests
import celery
from git import Repo
import tempfile
from celery.exceptions import Ignore
import celery_progress
from hurry.filesize import size
from bs4 import BeautifulSoup
from celery import shared_task, current_task
from celery_progress.backend import ProgressRecorder
import smtplib
import ast
import email.message
import math
import re
import jsbeautifier
from gzip import GzipFile
import ssl

try:
    from StringIO import StringIO
    readBytesCustom = StringIO
except ImportError:
    from io import BytesIO
    readBytesCustom = BytesIO

from urllib.request import Request, urlopen

import hashlib
from urllib.parse import urlparse
import jxmlease



from leaklooker_app.models import Monitor, Search, Rethink, Cassandra, Gitlab, Elastic, Dirs, Jenkins, Mongo, Rsync, \
    Sonarqube, Couchdb, Kibana, Ftp, Amazonbe, AmazonBuckets, Keys, Github, Amazons3be, Angular, Javascript

app = celery.Celery('leaklooker', broker="redis://localhost:6379")

def get_config():
    with open("config.json","r") as config:
        config_dict = json.load(config)

    return config_dict

regex_str = r"""
  (?:"|')                               # Start newline delimiter
  (
    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
    |
    ((?:/|\.\./|\./)                    # Start with /,../,./
    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    [^"'><,;|()]{1,})                   # Rest of the characters can't be
    |
    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    [a-zA-Z0-9_\-/]{1,}                 # Resource name
    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
    |
    ([a-zA-Z0-9_\-/]{1,}/               # REST API (no extension) with /
    [a-zA-Z0-9_\-/]{3,}                 # Proper REST endpoints usually have 3+ chars
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
    |
    AIza[0-9A-Za-z-_]{35}
    |
    (xox[p|b|o|a]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32})
    |
    AKIA[0-9A-Z]{16}
    |
    amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}
    |
    EAACEdEose0cBA[0-9A-Za-z]+
    |
    [f|F][a|A][c|C][e|E][b|B][o|O][o|O][k|K].*['|"][0-9a-f]{32}['|"]
    |
    [g|G][i|I][t|T][h|H][u|U][b|B].*['|"][0-9a-zA-Z]{35,40}['|"]
    |
    [a|A][p|P][i|I][_]?[k|K][e|E][y|Y].*['|"][0-9a-zA-Z]{32,45}['|"]
    |
    [s|S][e|E][c|C][r|R][e|E][t|T].*['|"][0-9a-zA-Z]{32,45}['|"]
    |
    [0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com
    |
    ya29\.[0-9A-Za-z\-_]+
    |
    [h|H][e|E][r|R][o|O][k|K][u|U].*[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}
    |
    [a-zA-Z]{3,10}://[^/\s:@]{3,20}:[^/\s:@]{3,20}@.{1,100}["'\s]
    |
    sk_live_[0-9a-zA-Z]{24}
    |
    https://hooks.slack.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}
    |
    [t|T][w|W][i|I][t|T][t|T][e|E][r|R].*[1-9][0-9]+-[0-9a-zA-Z]{40}
    |
    ([a-zA-Z0-9_\-]{1,}                 # filename
    \.(?:php|asp|aspx|jsp|json|
         action|html|js|txt|xml)        # . + extension
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
  )
  (?:"|')                               # End newline delimiter
"""

context_delimiter_str = "\n"

queries = {"gitlab": "title:%22gitlab%22%20AND%20web.body.content:%22register%22",
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
           'google_api_key':'web.body.content:"google_api_key"',
           'amazons3be':"web.body.content:ListBucketResult",
           'angular':"web.body.content:polyfills web.body.content:main web.body.content:runtime"}

buckets_all = ["s3.ap-southeast-1.amazonaws.com","s3.ap-southeast-2.amazonaws.com","s3-eu-west-1.amazonaws.com","s3-eu-west-2.amazonaws.com","s3-us-west-2.amazonaws.com","s3-us-west-1.amazonaws.com"]
keys_all = ['api_key','stripe','secret_key','google_api_key']
BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
HEX_CHARS = "1234567890abcdefABCDEF"

exclude = ['.png','.jpg', '.sum', "yarn.lock", "package-lock.json", ".svg", ".css"]

with open ("buckets.txt","r") as f:
    buckets_bruteforce = f.readlines()

def check_credits():
    credits = 0
    config = get_config()

    headers = {'X-Key': config['config']['BINARY_EDGE_KEY']}
    try:
        req = requests.get("https://api.binaryedge.io/v2/user/subscription", headers=headers)
        req_json = json.loads(req.content)
        credits = req_json['requests_left']
    except Exception as e:
        print(e)

    return credits


def stats(type=None):
    count = 0
    config = get_config()

    headers = {'X-Key': config['config']['BINARY_EDGE_KEY']}
    if type:
        query = queries[type]
        end = 'https://api.binaryedge.io/v2/query/search/stats?query=' + query + "&type=ports"
        req = requests.get(end, headers=headers)
        req_json = json.loads(req.content)

        for i in req_json:
            count = count + i['doc_count']
    return count


@shared_task(bind=True)
def check_main(self, fk, keyword=None, country=None, network=None, page=None, type=None):
    config = get_config()

    headers = {'X-Key': config['config']['BINARY_EDGE_KEY']}
    search = Search.objects.get(id=fk)
    progress_recorder = ProgressRecorder(self)
    results = {}
    counter = 0
    query = ""

    if keyword:
        query = "%20" + keyword + "%20"

    if " " in keyword:
        keyword = keyword.split(" ")[0]

    if country:
        query = query + "country:" + country + "%20"

    if network:
        query = query + 'ip:"' + network + '"'

    if page:
        query = query + "&page=" + page


    end = 'https://api.binaryedge.io/v2/query/search?query=' + queries[type.lower()]
    req = requests.get(end + query, headers=headers)
    req_json = json.loads(req.content)


    total = len(req_json['events'])

    events = req_json['total']
    if type.lower() == "gitlab":
        for c, i in enumerate(req_json['events']):
            results_gitlab = check_gitlab(c, i, search, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_gitlab

        self.update_state(state="SUCCESS",
                          meta={"type": 'gitlab', "total": total, 'events': events, 'results': results})
        raise Ignore()


    if type.lower() == "elastic":
        for c, i in enumerate(req_json['events']):
            results_elastic = check_elastic(c, i, search,keyword=keyword, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_elastic

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})

        raise Ignore()

    if type.lower() == "angular":
        for c, i in enumerate(req_json['events']):
            results_angular = check_angular(c, i, search,keyword=keyword, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_angular

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})

        raise Ignore()

    if type.lower() == "amazons3be":
        for c, i in enumerate(req_json['events']):
            results_amazons3be = check_amazons3be(c, i, search,keyword=keyword, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_amazons3be

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})

        raise Ignore()

    if type.lower() == 'asia' or type.lower() == "europe" or type.lower() == "north america":
        for c,i in enumerate(req_json['events']):
            results_amazonbe = check_amazonbe(c,i,search, config=config)
            progress_recorder.set_progress(c+1,total=total)
            results[c] = results_amazonbe

        self.update_state(state="SUCCESS", meta={"type":type.lower(),"total":total,'events':events, "results":results})

        raise Ignore()

    if type.lower() in keys_all:
        for c,i in enumerate(req_json['events']):
            results_keys = check_keys(c,i,search, config=config)
            progress_recorder.set_progress(c+1,total=total)
            results[c] = results_keys

        self.update_state(state="SUCCESS", meta={"type":'keys',"total":total,'events':events, "results":results})

        raise Ignore()

    if type.lower() == "dirs":
        for c, i in enumerate(req_json['events']):
            results_dirs = check_dir(c, i, search,keyword=keyword, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_dirs

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "jenkins":
        for c, i in enumerate(req_json['events']):
            results_jenkins = check_jenkins(c, i, search, keyword=keyword, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_jenkins

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "mongo":
        for c, i in enumerate(req_json['events']):
            results_mongo = check_mongo(c, i, search, keyword=keyword, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_mongo

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()
    if type.lower() == "rsync":
        for c, i in enumerate(req_json['events']):
            results_rsync = check_rsync(c, i, search, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_rsync

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "ftp":
        for c, i in enumerate(req_json['events']):
            results_ftp = check_ftp(c, i, search, keyword=keyword, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_ftp

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})

        raise Ignore()

    if type.lower() == "sonarqube":
        for c, i in enumerate(req_json['events']):
            results_sonarqube = check_sonarqube(c, i, search, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_sonarqube

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "couchdb":
        for c, i in enumerate(req_json['events']):
            results_couchdb = check_couchdb(c, i, search, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_couchdb

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "kibana":
        for c, i in enumerate(req_json['events']):
            results_kibana = check_kibana(c, i, search, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_kibana

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "cassandra":
        for c, i in enumerate(req_json['events']):
            results_cassandra = check_cassandra(c, i, search, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_cassandra

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "rethink":
        for c, i in enumerate(req_json['events']):
            results_rethink = check_rethink(c, i, search, config=config)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_rethink

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()


    return results


@app.task
def monitor_periodic():
    all = Monitor.objects.all()

    for i in all:
        types = ast.literal_eval(i.types)
        monitor(types, keyword=i.keyword, network=i.network)


@app.task
def monitor(types, keyword="", network=""):
    new_types = types[0].split(",")

    query = ""
    q = ""
    if keyword:
        query = "%20" + keyword + "%20"
        q = keyword

    if network:
        query = query + 'ip:"' + network + '"'
        q = network

    return_dict = {}
    for type in new_types:
        return_dict[type.lower()] = {}
        return_dict[type.lower()].update({"keyword": q})
        return_dict[type.lower()].update({"results": {}})

        search = Search(type=type)
        search.save()
        end = 'https://api.binaryedge.io/v2/query/search?query=' + queries[type.lower()]
        req = requests.get(end + query, headers=headers)
        req_json = json.loads(req.content)

        for number in range(1, int(math.ceil(req_json['total'] / 20)) + 1):
            end = 'https://api.binaryedge.io/v2/query/search?query=' + queries[type.lower()]
            req1= requests.get(end + query + "&page=" + str(number), headers=headers)
            req_json1 = json.loads(req1.content)
            if type.lower() == 'gitlab':
                for c, i in enumerate(req_json1['events']):
                    results = check_gitlab(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}
            if type.lower() == 'jenkins':
                for c, i in enumerate(req_json1['events']):
                    results = check_jenkins(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}
            if type.lower() == 'rethink':
                for c, i in enumerate(req_json1['events']):
                    results = check_rethink(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}
            if type.lower() == 'couchdb':
                for c, i in enumerate(req_json1['events']):
                    results = check_couchdb(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}

            if type.lower() == 'elastic':



                for c, i in enumerate(req_json1['events']):
                    results = check_elastic(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:

                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}

            if type.lower() == 'kibana':
                for c, i in enumerate(req_json1['events']):
                    results = check_kibana(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}

            if type.lower() == 'mongo':
                for c, i in enumerate(req_json1['events']):
                    results = check_mongo(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:

                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}

            if type.lower() == 'dirs':
                for c, i in enumerate(req_json1['events']):
                    results = check_dir(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}


            if type.lower() == 'sonarqube':
                for c, i in enumerate(req_json1['events']):
                    results = check_sonarqube(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}

            if type.lower() == 'rsync':
                for c, i in enumerate(req_json1['events']):
                    results = check_rsync(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}

            if type.lower() == 'cassandra':
                for c, i in enumerate(req_json1['events']):
                    results = check_cassandra(c, i, search)
                    if results:
                        for j in results:
                            if results[j]:
                                return_dict[type.lower()]['results'][c]['ip'] = results[j]
                            else:
                                return_dict[type.lower()]['results'] = {}



    send_mail(return_dict)


## { 'gitlab': {'keyword":"fa"}, 0 : {'ip':1111.1.1}}

def send_mail(results):
    body = ""
    for i, v in results.items():
        body = body + 'Your results for ' + "<b>" + i + "</b> with keyword " + "<b>" + v['keyword'] + "</b><br>"
        if not v['results']:
            body = body + 'No results' + "<br>"
        for k in v['results']:
            body = body + "https://app.binaryedge.io/services/query/" + v['results'][k]['ip'] + "<br>"

    # print(results)
    msg = email.message.Message()
    msg['Subject'] = 'LeakLooker Notification'
    msg['From'] = config['config']['monitoring']['gmail_email']
    msg['To'] = config['config']['monitoring']['gmail_email']
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(body)

    gmail_user = config['config']['monitoring']['gmail_email']
    gmail_password = config['config']['monitoring']['gmail_password']

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.close()

        print('Email sent!')
    except Exception as e:
        print(e)
        print('Something went wrong...')
    pass

def check_amazons3be(c,i,search,keyword, config):
    return_dict = {}
    myparser = jxmlease.Parser()

    ip = i['target']['ip']
    port = i['target']['port']
    files = []
    indicators = []

    if Amazons3be.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        try:
            root = myparser(i['result']['data']['response']['body']['content'])
            if 'Contents' in root['ListBucketResult']:
                for counter, i in enumerate(root['ListBucketResult']['Contents']):

                    if keyword in str(i['Key'].lower()):
                        indicators.append(str(i['Key']))
                    if counter < 50:
                        files.append(str(i['Key']))

                device = Amazons3be(search=search, ip=ip, port=port, files=files, indicator=indicators)
                device.save()

                return_dict[c] = {"ip": ip, "port": port, 'files': files}


        except Exception as e:
            return_dict = {}
            print(e)

    return return_dict


def check_rethink(c, i, search, config):
    return_dict = {}

    ip = i['target']['ip']
    port = i['target']['port']
    databases = []

    if Rethink.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        if 'databases' in i['result']['data']:
            for database in i['result']['data']['databases']:
                databases.append(database)

        device = Rethink(search=search, ip=ip, port=port, databases=databases)
        device.save()

        return_dict[c] = {"ip": ip, "port": port, 'databases': databases}

    return return_dict


def check_cassandra(c, i, search, config):
    return_dict = {}
    ip = i['target']['ip']
    port = i['target']['port']
    keyspaces = []

    if Cassandra.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        if 'keyspaces' in i['result']['data']:
            for keyspace in i['result']['data']['keyspaces']:
                keyspaces.append(keyspace)

        device = Cassandra(search=search, ip=ip, port=port, keyspaces=keyspaces)
        device.save()

        return_dict[c] = {"ip": ip, "port": port, 'keyspaces': keyspaces}

    return return_dict


def check_ftp(c,i, search, keyword, config):
    return_dict = {}
    files = []
    ip = i['target']['ip']
    port = i['target']['port']


    indicator = []
    if Ftp.objects.filter(ip=ip).exists():
        pass
    elif ip in config['config']['blacklist']:
        pass
    else:
        try:
            for j in i['result']['data']['content']:
                if keyword in j['name'].lower():
                    indicator.append(j['name'])
                if j['type'] == "d":
                    files.append(j['name'])
                    if 'content' in j:
                        for k in j['content']:
                            if keyword in k['name'].lower():
                                indicator.append(j['name'])
                                indicator.append(k['name'])
                            if k['type'] == "d":
                                files.append(k['name'])
                                if 'content' in k:
                                    for l in k['content']:
                                        if keyword in k['name'].lower():
                                            indicator.append(j['name'])
                                            indicator.append(k['name'])
                                            indicator.append(l['name'])
                                        if l['type'] == 'd':
                                            files.append(l['name'])

            if "." in files:
                files.remove('.')
            if ".." in files:
                files.remove("..")

            device = Ftp(search=search, ip=ip, port=port, files=files, indicator=indicator)
            device.save()
            return_dict[c] = {"ip": ip, "port": port, 'files': files}

        except Exception as e:
            print(e)


    return return_dict



def check_kibana(c, i, search, config):
    return_dict = {}
    ip = i['target']['ip']
    port = i['target']['port']

    if Kibana.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:

        device = Kibana(search=search, ip=ip, port=port)
        device.save()

        return_dict[c] = {"ip": ip, "port": port}

    return return_dict


def check_couchdb(c, i, search, config):
    return_dict = {}
    ip = i['target']['ip']
    port = i['target']['port']

    if Couchdb.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:

        device = Couchdb(search=search, ip=ip, port=port)
        device.save()

        return_dict[c] = {"ip": ip, "port": port}

    return return_dict


def check_sonarqube(c, i, search, config):
    return_dict = {}
    ip = i['target']['ip']
    url = ""
    port = i['target']['port']

    if Sonarqube.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        if 'response' in i['result']['data']:
            if 'url' in i['result']['data']['response']:
                url = i['result']['data']['response']['url']
        device = Sonarqube(search=search, url=url, ip=ip, port=port)
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port}

    return return_dict


def check_rsync(c, i, search, config):
    return_dict = {}
    shares = []
    ip = i['target']['ip']
    port = i['target']['port']

    if Rsync.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        try:
            banner = i['result']['data']['service']['banner'].split("\\n")
            for share in banner:
                shares.append(share)
            device = Rsync(search=search, ip=ip, port=port, shares=shares)
            device.save()
        except Exception as e:
            print(e)

    return_dict[c] = {"ip": ip, "port": port, "shares": shares}

    return return_dict


def check_jenkins(c, i, search, keyword, config):
    return_dict = {}
    jobs = []
    ip = i['target']['ip']
    port = i['target']['port']
    url = ""
    indicators = []

    if Jenkins.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        if 'response' in i['result']['data']:
            if 'url' in i['result']['data']['response']:
                url = i['result']['data']['response']['url']

            try:
                if isinstance(i['result']['data']['response']['body'], str):
                    html_code = i['result']['data']['response']['body']
                else:
                    html_code = i['result']['data']['response']['body']['content']

                jobs = []
                try:
                    soup = BeautifulSoup(html_code, features="html.parser")

                    for project in soup.find_all("a", {"class": "model-link inside"}):
                        if project['href'].startswith("job"):
                            splitted = project['href'].split("/")
                            if keyword in splitted[1].lower():
                                indicators.append(splitted[1])

                            jobs.append(splitted[1])
                except Exception as e:
                    pass
            except Exception as e:
                pass
        device = Jenkins(search=search, url=url, ip=ip, port=port, jobs=jobs, indicator=indicators)
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port, "jobs": jobs}

    return return_dict

@app.task
def check_mongo(c, i, search, keyword, config):
    return_dict = {}
    dbs = []
    ip = i['target']['ip']
    url = ""
    port = i['target']['port']
    bytes_size = 0
    indicators = []

    if Mongo.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass


    else:
        if 'response' in i['result']['data']:
            if 'url' in i['result']['data']['response']:
                url = i['result']['data']['response']['url']

        if not i['result']['error']:
            if 'databases' in i['result']['data']['listDatabases']:
                for k in i['result']['data']['listDatabases']['databases']:
                    bytes_size = bytes_size + k['sizeOnDisk']
                    if not "<script>" in k['name']:
                        if keyword in k['name'].lower():
                            indicators.append(k['name'])
                        dbs.append(k['name'])

        new_size = size(bytes_size)

        device = Mongo(search=search, ip=ip, port=port, databases=dbs, size=str(new_size), indicator = indicators)
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port, 'databases': dbs, "size": str(size)}

    return return_dict

def parser_file(content, regex_str, keyword, mode=1, more_regex=None, no_dup=1):
    '''
    Parse Input
    content:    string of content to be searched
    regex_str:  string of regex (The link should be in the group(1))
    mode:       mode of parsing. Set 1 to include surrounding contexts in the result
    more_regex: string of regex to filter the result
    no_dup:     remove duplicated link (context is NOT counted)
    Return the list of ["link": link, "context": context]
    The context is optional if mode=1 is provided.
    '''
    global context_delimiter_str

    ip = keyword.split("/")
    if mode == 1:
        # Beautify
        if len(content) > 1000000:
            content = content.replace(";",";\r\n").replace(",",",\r\n")
            with open(ip[2] +".js",'w') as f:
                f.write(content)
        else:
            content = jsbeautifier.beautify(content)
            with open(ip[2] +".js",'w') as f:
                f.write(content)

    regex = re.compile(regex_str, re.VERBOSE)

    if mode == 1:
        all_matches = [(m.group(1), m.start(0), m.end(0)) for m in re.finditer(regex, content)]
        items = getContext(all_matches, content, context_delimiter_str=context_delimiter_str)
    else:
        items = [{"link": m.group(1)} for m in re.finditer(regex, content)]

    if no_dup:
        # Remove duplication
        all_links = set()
        no_dup_items = []
        for item in items:
            if item["link"] not in all_links:
                all_links.add(item["link"])
                no_dup_items.append(item)
        items = no_dup_items

    # Match Regex
    filtered_items = []
    for item in items:
        # Remove other capture groups from regex results
        if more_regex:
            if re.search(more_regex, item["link"]):
                filtered_items.append(item)
        else:
            filtered_items.append(item)

    return filtered_items


@app.task
def check_dir(c, i, search, keyword, config):
    return_dict = {}
    ip = i['target']['ip']
    url = ""
    dirs = ""
    html_code = ""
    indicators = []

    port = i['target']['port']

    if Dirs.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass

    else:
        if 'response' in i['result']['data']:
            if 'url' in i['result']['data']['response']:
                url = i['result']['data']['response']['url']

            try:
                if isinstance(i['result']['data']['response']['body'], str):
                    html_code = i['result']['data']['response']['body']
                else:
                    html_code = i['result']['data']['response']['body']['content']

                dirs = []
                try:
                    soup = BeautifulSoup(html_code, features="html.parser")

                    for project in soup.find_all("a", href=True):
                        if project.contents[0] == "Name" or project.contents[0] == "Last modified" or project.contents[
                            0] == "Size" or project.contents[0] == "Description":
                            pass
                        else:
                            if keyword in str(project.contents[0].lower()):
                                indicators.append(str(project.contents[0]))
                            dirs.append(str(project.contents[0]))
                except Exception as e:
                    print(e)
            except Exception as e:
                print(e)

        # print(dirs)
        device = Dirs(search=search, url=url, ip=ip, port=port, dirs=dirs, indicator=indicators)
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port, 'dirs': dirs}

    return return_dict

def send_request(url):
    '''
    Send requests with Requests
    '''
    q = Request(url)

    q.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
    q.add_header('Accept', 'text/html,\
        application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    q.add_header('Accept-Language', 'en-US,en;q=0.8')
    q.add_header('Accept-Encoding', 'gzip')

    try:
        sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        response = urlopen(q, context=sslcontext)
    except:
        sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        response = urlopen(q, context=sslcontext)

    if response.info().get('Content-Encoding') == 'gzip':
        data = GzipFile(fileobj=readBytesCustom(response.read())).read()
    elif response.info().get('Content-Encoding') == 'deflate':
        data = response.read().read()
    else:
        data = response.read()

    return data.decode('utf-8', 'replace')

@app.task
def check_angular(c,i,search,keyword,config):
    return_dict = {}

    ip = i['target']['ip']
    port = i['target']['port']
    path = ""
    title = ""
    if Angular.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        try:
            html = i['result']['data']['response']['body']['content']
            soup = BeautifulSoup(html)

            for src in soup.find_all('script', {"src": True}):
                if 'main' in src['src']:
                    path = i['target']['ip'] + "/" + src['src']

            for k in soup.find_all('title', limit=1):
                title = (k.contents[0])

            device = Angular(search=search, ip=ip, port=port, title=title, path = path)

            device.save()

            if port == 443:
                pre = "https://"
            else:
                pre = "http://"
            return_dict[c] = {"ip": ip, "port": port, 'title': title, 'path':pre+path}
        except Exception as e:
            print(e)

    return return_dict


@app.task
def check_elastic(c, i, search, keyword, config):
    return_dict = {}
    indices_list = []
    bytes_size = 0
    new_size = ""
    ip = i['target']['ip']
    name = i['result']['data']['cluster_name']
    port = i['target']['port']
    indicators = []

    if Elastic.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        try:
            for indice in i['result']['data']['indices']:
                bytes_size = bytes_size + indice['size_in_bytes']
                if not "<script>" in indice['index_name']:
                    if keyword in indice['index_name'].lower():
                        indicators.append(indice['index_name'])
                    indices_list.append(indice['index_name'])

            new_size = size(bytes_size)
            device = Elastic(search=search, name=name, ip=ip, port=port, size=new_size, indices=indices_list,
                             indicator=indicators)
            device.save()
            return_dict[c] = {"name": name, "ip": ip, "port": port, 'size': new_size, "indice": indices_list}
        except Exception as e:
            print(e)


    return return_dict

def getContext(list_matches, content, include_delimiter=0, context_delimiter_str="\n"):
    '''
    Parse Input
    list_matches:       list of tuple (link, start_index, end_index)
    content:            content to search for the context
    include_delimiter   Set 1 to include delimiter in context
    '''
    items = []
    for m in list_matches:
        match_str = m[0]
        match_start = m[1]
        match_end = m[2]
        context_start_index = match_start
        context_end_index = match_end
        delimiter_len = len(context_delimiter_str)
        content_max_index = len(content) - 1

        while content[context_start_index] != context_delimiter_str and context_start_index > 0:
            context_start_index = context_start_index - 1

        while content[context_end_index] != context_delimiter_str and context_end_index < content_max_index:
            context_end_index = context_end_index + 1

        if include_delimiter:
            context = content[context_start_index: context_end_index]
        else:
            context = content[context_start_index + delimiter_len: context_end_index]

        item = {
            "link": match_str,
            "context": context
        }
        items.append(item)

    return items


def check_gitlab(c, i, search, config):
    return_dict = {}

    ip = i['target']['ip']
    url = ""
    port = i['target']['port']

    if Gitlab.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        if 'response' in i['result']['data']:
            if 'url' in i['result']['data']['response']:
                url = i['result']['data']['response']['url']
        device = Gitlab(search=search, url=url, ip=ip, port=port)
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port}

    return return_dict


def parse_bucket(link):
    parsed = urlparse(link)
    if parsed.hostname in buckets_all:
        path_splitted = parsed.path.split("/")
        return urlparse(link).hostname + "/" + path_splitted[1]
    else:
        return urlparse(link).hostname

def check_keys(c,i,search, config):
    return_dict = {}

    ip = i['target']['ip']
    port = i['target']['port']
    buckets = set()
    title = ""

    if Keys.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        if 'response' in i['result']['data']:
            if 'url' in i['result']['data']['response']:
                url = i['result']['data']['response']['url']

        try:
            title = i['result']['data']['response']['title']
        except Exception as e:
            pass

        device = Keys(search=search, ip=ip, port=port, title=title)
        device.save()

        return_dict[c] = {"ip": ip, "port": port, 'title': title}

    return return_dict

def shannon_entropy(data, iterator):
    """
    Borrowed from http://blog.dkbza.org/2007/05/scanning-data-for-entropy-anomalies.html
    """
    if not data:
        return 0
    entropy = 0
    for x in iterator:
        p_x = float(data.count(x))/len(data)
        if p_x > 0:
            entropy += - p_x*math.log(p_x, 2)
    return entropy


def check_amazonbe(c,i,search, config):
    return_dict = {}

    ip = i['target']['ip']
    port = i['target']['port']
    buckets = set()

    if Amazonbe.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:

        try:
            soup = BeautifulSoup(i['result']['data']['service']['banner'], "html.parser")

            for a in soup.find_all(href=True):
                if "amazonaws.com" in a['href']:
                    buckets.add(parse_bucket(a['href']))

            for a in soup.find_all("script", {"src": True}):
                if "amazonaws.com" in a['src']:
                    buckets.add(parse_bucket(a['src']))

            for a in soup.find_all("img", {"src": True}):
                if "amazonaws.com" in a['src']:
                    buckets.add(parse_bucket(a['src']))

            title = soup.find("meta", property="og:image")
            if title:
                if "amazonaws.com" in title['content']:
                    buckets.add(parse_bucket(title['content']))
        except Exception as e:
            print(e)

        device = Amazonbe(search=search, ip=ip, port=port, buckets=list(buckets))
        device.save()

        return_dict[c] = {"ip": ip, "port": port, 'buckets': list(buckets)}

    return return_dict


@shared_task(bind=True)
def brute_buckets(self, keyword):
    progress_recorder = ProgressRecorder(self)

    total = len(buckets_bruteforce)
    k = []
    for c,i in enumerate(buckets_bruteforce):


        req = requests.get("https://" + keyword + i.rstrip() + ".s3.amazonaws.com", verify=False)


        if req.status_code == 200 or req.status_code == 403:
            am = AmazonBuckets(bucket=keyword + i.rstrip() + ".s3.amazonaws.com", confirmed=False,for_later=False)
            am.save()

        progress_recorder.set_progress(c+1, total=total)

        self.update_state(state="PROGRESS",
                          meta={"results": "https://" + keyword + i.rstrip() + ".s3.amazonaws.com",
                                "code": req.status_code, "percentage": c / total * 100})

    self.update_state(state="SUCCESS",
                      meta={"type": 'amazon', "total": total})

    raise Ignore()

def clone_git_repo(git_url):
    try:
        project_path = tempfile.mkdtemp()
        Repo.clone_from(git_url, project_path)
        return project_path
    except Exception as e:
        print(e.args)

def get_strings_of_set(word, char_set, threshold=20):
    count = 0
    letters = ""
    strings = []
    for char in word:
        if char in char_set:
            letters += char
            count += 1
        else:
            if count > threshold:
                strings.append(letters)
            letters = ""
            count = 0
    if count > threshold:
        strings.append(letters)
    return strings

def get_secrets(diff, branch_name,prev_commit):
    stringsFound = set()
    paths = []
    path_secrets = {'path':[], 'secrets':[]}

    for blob in diff: # for every text in diff
        text = blob.diff.decode('utf-8', errors='replace') # extract text from blob
        # extract path from blob, sometimes it's a_path, sometimes it's b_path.
        path = blob.b_path if blob.b_path else blob.a_path

        if any(x in path for x in exclude):
            pass
        else:

            for line in text.split('\n'): # for every line in diff's blob
                for word in line.split():
                    base64_strings = get_strings_of_set(word, BASE64_CHARS) # check if string contains characters from base64 char set
                    hex_strings = get_strings_of_set(word, HEX_CHARS) # check if string contains character from hex char set
                    for string in base64_strings: # if any string was found
                        b64Entropy = shannon_entropy(string, BASE64_CHARS) # calculate entropy
                        if b64Entropy > 4.5:
                            stringsFound.add(string)
                            path_secrets['path'].append(path)# add string to list
                            path_secrets['secrets'].append(string)
                            # text = text.replace(string,colors.WARNING + string + bcolors.ENDC) # it is raw whole commit text
                    for string in hex_strings:
                        hexEntropy = shannon_entropy(string, HEX_CHARS)
                        if hexEntropy > 3:
                            stringsFound.add(string)
                            path_secrets['path'].append(path)
                            path_secrets['secrets'].append((string))
                            # text = text.replace(string,bcolors.WARNING + string + bcolors.ENDC)

    return path_secrets

def rules(diff):

    path_secrets = {'path':[], 'secrets':[]}
    with open('rules.json', "r") as ruleFile:
        rules = json.loads(ruleFile.read())
        for rule in rules:
            rules[rule] = re.compile(rules[rule])

        regex_matches = []

        for blob in diff:
            path = blob.b_path if blob.b_path else blob.a_path
            if any(x in path for x in exclude):
                pass
            else:
                for key in rules:
                    try:
                        text = blob.diff.decode('utf-8', errors='replace')
                        found_strings = rules[key].findall(text)
                        if len(found_strings) > 0:
                            for i in found_strings:
                                path_secrets['secrets'].append(i)


                            path_secrets['path'].append(path)
                    except:
                        pass

    return path_secrets

@shared_task(bind=True)
def javascript_search(self, keyword):
    ff = send_request(keyword)
    enpoints = parser_file(ff, regex_str, keyword)

    links = []
    context = []

    for i in enpoints:
        links.append(i['link'])
        context.append(i['context'])

    js = Javascript(secrets=links, context=context, path=keyword)
    js.save()

    self.update_state(state="SUCCESS",
                      meta={"type": 'js', "secrets": links, 'context':context,'path':keyword})

    raise Ignore()


@shared_task(bind=True)
def github_repo_search(self,keyword):
    progress_recorder = ProgressRecorder(self)
    project_path = clone_git_repo(keyword)  # cloning repo
    repo_git = Repo(project_path)
    branches = repo_git.remotes.origin.fetch()
    checked = set()  # set for already checked elements
    total2= len(list(repo_git.iter_commits('HEAD')))
    results = {}
    paths = []
    # print("Searching repo: " + keyword)
    for remote_branch in branches:  # for every branch in repo
        branch_name = remote_branch.name  # fetch branch name
        # print("Searching in branch: " + branch_name)
        previous_commit = None
        for c,current_commit in enumerate(repo_git.iter_commits(branch_name)):
            percent = round(c / total2 * 100, 2)

            progress_recorder.set_progress(c + 1, total=total2)
            self.update_state(state="PROGRESS",
                              meta={"commit": str(current_commit), "percent": percent})
            # print("Searching in commit: " + str(current_commit))
            diff_hash = hashlib.md5((str(previous_commit) + str(current_commit)).encode(
                'utf-8')).digest()  # calculate hash from diffs to check if it has been checked already
            if not previous_commit:  # first commit
                previous_commit = current_commit
                continue
            elif diff_hash in checked:  # if hash has been checked, it means that previous commit becomes current commit
                previous_commit = current_commit
                continue
            else:

                diff = previous_commit.diff(current_commit, create_patch=True)  # calculate diff
                checked.add(diff_hash)  # add diff hash to checked list
                # all_secrets = {'paths':}
                secrets = get_secrets(diff, branch_name, previous_commit)
                secrets_from_rules = rules(diff)

                # print(secrets_from_rules)
                # print(secrets)


                # all_secrets = {**secrets, **secrets_from_rules}
                #
                # print(all_secrets)
                # two_secrets = list(secrets) + list(secrets_from_rules)
                if len(secrets['secrets']) > 0 or len(secrets_from_rules['secrets']) > 0:
                    together_paths = set(list(secrets_from_rules['path']) + list(secrets['path']))
                    together_secrets = secrets_from_rules['secrets'] + secrets['secrets']



                    asd = set(together_secrets)

                    all_secrets = {'path': list(together_paths),
                                   "secret": list(asd)}

                    results[str(previous_commit)] = all_secrets

                    # print(two_secrets)

                    am = Github(commit=str(current_commit), keyword=keyword, path=list(together_paths), secret=list(asd), confirmed=False,
                                for_later=False)
                    am.save()


            previous_commit = current_commit

    self.update_state(state="SUCCESS",
                      meta={"type": 'github', "results":results})

    raise Ignore()
