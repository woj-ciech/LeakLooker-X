import logging
import json
import requests
import celery
from celery import task
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

from leaklooker_app.models import Monitor, Search, Rethink, Cassandra, Gitlab, Elastic, Dirs, Jenkins, Mongo, Rsync, \
    Sonarqube, Couchdb, Kibana

app = celery.Celery('leaklooker', broker="redis://localhost:6379")

def get_config():
    with open("config.json","r") as config:
        config_dict = json.load(config)

    return config_dict

config = get_config()

headers = {'X-Key': config['config']['BINARY_EDGE_KEY']}

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
           "rethink": "type:rethinkdb"}


def check_credits():
    credits = 0
    try:
        req = requests.get("https://api.binaryedge.io/v2/user/subscription", headers=headers)
        req_json = json.loads(req.content)
        credits = req_json['requests_left']
    except Exception as e:
        print(e)

    return credits


def stats(type=None):
    count = 0
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
    search = Search.objects.get(id=fk)
    progress_recorder = ProgressRecorder(self)
    results = {}
    counter = 0
    query = ""

    if keyword:
        query = "%20" + keyword + "%20"

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
            results_gitlab = check_gitlab(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_gitlab

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "elastic":
        for c, i in enumerate(req_json['events']):
            results_elastic = check_elastic(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_elastic

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "dirs":
        for c, i in enumerate(req_json['events']):
            results_dirs = check_dir(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_dirs

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "jenkins":
        for c, i in enumerate(req_json['events']):
            results_jenkins = check_jenkins(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_jenkins

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "mongo":
        for c, i in enumerate(req_json['events']):
            results_mongo = check_mongo(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_mongo

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()
    if type.lower() == "rsync":
        for c, i in enumerate(req_json['events']):
            results_rsync = check_rsync(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_rsync

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "sonarqube":
        for c, i in enumerate(req_json['events']):
            results_sonarqube = check_sonarqube(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_sonarqube

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "couchdb":
        for c, i in enumerate(req_json['events']):
            results_couchdb = check_couchdb(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_couchdb

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "kibana":
        for c, i in enumerate(req_json['events']):
            results_kibana = check_kibana(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_kibana

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "cassandra":
        for c, i in enumerate(req_json['events']):
            results_cassandra = check_cassandra(c, i, search)
            progress_recorder.set_progress(c + 1, total=total)
            results[c] = results_cassandra

        self.update_state(state="SUCCESS",
                          meta={"type": type.lower(), "total": total, 'events': events, 'results': results})
        raise Ignore()

    if type.lower() == "rethink":
        for c, i in enumerate(req_json['events']):
            results_rethink = check_rethink(c, i, search)
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
            print(end + query)
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


def check_rethink(c, i, search):
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


def check_cassandra(c, i, search):
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


def check_kibana(c, i, search):
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


def check_couchdb(c, i, search):
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


def check_sonarqube(c, i, search):
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


def check_rsync(c, i, search):
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

        except Exception as e:
            print(e)

    device = Rsync(search=search, ip=ip, port=port, shares=shares)
    device.save()

    return_dict[c] = {"ip": ip, "port": port, "shares": shares}

    return return_dict


def check_jenkins(c, i, search):
    return_dict = {}
    jobs = []
    ip = i['target']['ip']
    port = i['target']['port']
    url = ""

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

                jobs = extract_jobs(html_code)
            except Exception as e:
                print(e)
        device = Jenkins(search=search, url=url, ip=ip, port=port, jobs=jobs)
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port, "jobs": jobs}

    return return_dict

@app.task
def check_mongo(c, i, search):
    return_dict = {}
    dbs = []
    ip = i['target']['ip']
    url = ""
    port = i['target']['port']
    size = 0

    if Mongo.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass


    else:
        if 'response' in i['result']['data']:
            if 'url' in i['result']['data']['response']:
                url = i['result']['data']['response']['url']

        if not i['result']['error']:
            if 'databases' in i['result']['data']['listDatabases']:
                for k in i['result']['data']['listDatabases']['databases']:
                    size = size + k['sizeOnDisk']
                    if not "<script>" in k['name']:
                        dbs.append(k['name'])

        device = Mongo(search=search, ip=ip, port=port, databases=dbs, size=str(size))
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port, 'databases': dbs, "size": str(size)}

    return return_dict


def extract_jobs(content):
    jobs = []
    try:
        soup = BeautifulSoup(content, features="html.parser")

        for project in soup.find_all("a", {"class": "model-link inside"}):
            if project['href'].startswith("job"):
                splitted = project['href'].split("/")
                jobs.append(splitted[1])

        return jobs
    except Exception as e:
        print(e)
        return jobs


def extract_dirs(content):
    dirs = []
    try:
        soup = BeautifulSoup(content, features="html.parser")

        for project in soup.find_all("a", href=True):
            if project.contents[0] == "Name" or project.contents[0] == "Last modified" or project.contents[
                0] == "Size" or project.contents[0] == "Description":
                pass
            else:
                dirs.append(str(project.contents[0]))

        return dirs
    except Exception as e:
        print(e)
        return dirs

@app.task
def check_dir(c, i, search):
    return_dict = {}
    ip = i['target']['ip']
    url = ""
    dirs = ""
    html_code = ""

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

                dirs = extract_dirs(html_code)
            except Exception as e:
                print(e)

        # print(dirs)
        device = Dirs(search=search, url=url, ip=ip, port=port, dirs=dirs)
        device.save()

        return_dict[c] = {"url": url, "ip": ip, "port": port, 'dirs': dirs}

    return return_dict

@app.task
def check_elastic(c, i, search):
    return_dict = {}
    indices_list = []
    bytes_size = 0
    new_size = ""
    ip = i['target']['ip']
    name = i['result']['data']['cluster_name']
    port = i['target']['port']

    if Elastic.objects.filter(ip=ip).exists() or ip in config['config']['blacklist']:
        pass
    else:
        try:
            for indice in i['result']['data']['indices']:
                bytes_size = bytes_size + indice['size_in_bytes']
                if not "<script>" in indice['index_name']:
                    indices_list.append(indice['index_name'])

            new_size = size(bytes_size)

        except Exception as e:
            print(e)

    return_dict[c] = {"name": name, "ip": ip, "port": port, 'size': new_size, "indice": indices_list}

    device = Elastic(search=search, name=name, ip=ip, port=port, size=new_size, indices=indices_list)
    device.save()
    return return_dict


def check_gitlab(c, i, search):
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
