from django.shortcuts import render
from leaklooker_app import forms
from leaklooker_app.models import Search, Amazons3be, Gitlab, Elastic, Rethink, Mongo, Cassandra, Monitor, Ftp, AmazonBuckets, Github
from leaklooker import tasks
from leaklooker.tasks import check_main
from django.apps import apps
import json
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseRedirect
import random
from celery.result import AsyncResult


types = ['angular','amazons3be',"gitlab","elastic","dirs","jenkins","mongo","rsync",'sonarqube','couchdb',"kibana","cassandra","rethink", "ftp"]

def index(request):

    credits = tasks.check_credits()
    for_later_counter = 0
    confirmed_counter = 0
    all_counter = 0
    labels = []
    data = []
    random_leaks_context = {}
    for_later_context = {}
    open_stats = []

    notif = Monitor.objects.all()

    models = apps.get_models(include_auto_created=False,include_swapped=False)
    for i in models:
        try:
            for_later_counter = for_later_counter + i.objects.filter(for_later=True).count()
            confirmed_counter = confirmed_counter + i.objects.filter(confirmed=True).count()
            all_counter = all_counter + i.objects.all().count()
            labels.append(i.__name__)
            data.append(i.objects.all().count())
        except Exception as e:
            print(e)

    random_model = random.choice(labels)
    model = apps.get_model('leaklooker_app', random_model)
    random_leaks = model.objects.filter(confirmed=False,for_later=False)
    try:
        random_leaks_context[random_model] = random.sample(list(random_leaks),8)
    except:
        random_leaks_context[random_model] = []

    try:
        for_later = model.objects.filter(confirmed=False,for_later=True).order_by('-id')
        for_later_context[random_model] = list(for_later)
    except Exception as e:
        print(e)

    try:
        checked_elastic = Elastic.objects.filter(confirmed=True) | Elastic.objects.filter(for_later=True)
        percentage_of_checked_elastic = checked_elastic.count()

        checked_rethink = Rethink.objects.filter(confirmed=True) | Rethink.objects.filter(for_later=True)
        percentage_of_checked_rethink = checked_rethink.count()

        checked_mongo = Mongo.objects.filter(confirmed=True) | Mongo.objects.filter(for_later=True)
        percentage_of_checked_mongo = checked_mongo.count()

        checked_cassandra = Cassandra.objects.filter(confirmed=True) | Cassandra.objects.filter(for_later=True)
        percentage_of_checked_cassandra = checked_cassandra.count()

        open_stats.append(percentage_of_checked_elastic)
        open_stats.append(percentage_of_checked_rethink)
        open_stats.append(percentage_of_checked_mongo)
        open_stats.append(percentage_of_checked_cassandra)

    except Exception as e:
        print(e)

    for i in notif:
        i.types = i.types[2:-2]



    context = {'credits':credits,
               "for_later_counter":for_later_counter,
               "confirmed_counter":confirmed_counter,
               "all_counter":all_counter,
               "labels":labels,
               'data':data,
               "random_leaks":random_leaks_context,
               "for_later":for_later_context,
               "percentages":open_stats,
               "monitor":notif}

    return render(request, 'index.html', context)

def database(request):
    results = []
    for i in apps.get_models(include_auto_created=False,include_swapped=False):
        if i.__name__.lower() in types:
            results.append(i.objects.all())

    return render(request, 'database.html', {"results":results})

def keyword(request):

    return render(request, "search_keyword.html",{})

def type(request):
    return render(request, 'search_type.html', {})

def search(request,type):
    context = {"type":type}

    return render(request, 'search.html', context)

def keyword_search_results(request):
    if request.is_ajax() and request.method == 'GET':

        keyword = request.GET['keyword']
        country = request.GET['country']
        network = request.GET['network']
        type = request.GET['type']
        search = Search(type=type, keyword=keyword,country=country,network=network)
        print(search.id)

        search.save()

        gitlab_search_task = tasks.check_main.delay(fk=search.id, page="1", keyword=keyword, country=country,
                                          network=network, type=type)
        request.session['task_id'] = gitlab_search_task.task_id

        # return render(request, 'search.html', context={'task_id': gitlab_search_task.task_id, 'type':type})
        return HttpResponse(json.dumps({'task_id': gitlab_search_task.task_id, "type":type}), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'OK2': '123123'}), content_type='application/json')

def search_results(request,type):
    if request.is_ajax() and request.method == "GET":
        keyword = request.GET['keyword']
        country = request.GET['country']
        network = request.GET['network']
        page = request.GET['page']

        search = Search(type=type, keyword=keyword, country=country, network=network)
        search.save()

        gitlab_search_task = tasks.check_main.delay(fk=search.id, page=page, keyword=keyword, country=country,
                                              network=network, type=type)

        request.session['task_id'] = gitlab_search_task.task_id
        print('test')
        # return render(request, 'search.html', context={'task_id': gitlab_search_task.task_id, 'type':type})
        return HttpResponse(json.dumps({'task_id': gitlab_search_task.task_id}), content_type='application/json')
            # return HttpResponse(json.dumps(gitlab_search_task), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'OK2': 'OK'}), content_type='application/json')


def get_task_info(request):
    task_id = request.GET.get('task_id', None)
    data = {}
    if task_id is not None:
        task = AsyncResult(task_id)
        print(task.result)
        if task.state == "PROGRESS":
            try:
                data = {
                    'state': task.state,
                    'result': task.result,
                    'percentage': task.result['current'] / task.result['total'] * 100,
                }
            except Exception as e:
                data = {
                    'state': task.state,
                    'result': task.result,
                }

        else:
            data = {
                'state': task.state,
                'result': task.result,
            }
            print(data)
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponse('No job id given.')

def notifications(request):
    all = Monitor.objects.all()
    # Monitor.objects.all().delete()

    for i in all:
        i.types = i.types[2:-2]

    return render(request, "notifications.html",{"notifications":all})

def delete_notification(request,id):
    if request.is_ajax() and request.method == 'GET':
        Monitor.objects.filter(id=id).delete()

        return HttpResponse(json.dumps({"status":"removed"}),
                            content_type='application/json')
    else:
        return HttpResponse(json.dumps({'OK2': '123123'}), content_type='application/json')

def monitor(request):
    if request.is_ajax() and request.method == 'GET':
        types = request.GET.getlist('type')
        try:
            keyword = request.GET['keyword']
        except:
            keyword = ""

        try:
            network = request.GET['network']
        except:
            network = ""

        mon = Monitor(keyword=keyword, network=network, types=types)
        mon.save()

        # gitlab_search_task = tasks.monitor(keyword=keyword,network=network, types=types2)
        # return render(request, 'search.html', context={'task_id': gitlab_search_task.task_id, 'type':type})
        return HttpResponse(json.dumps({'keyword': keyword,"network":network,"types":types}),
                            content_type='application/json')
    else:
        return HttpResponse(json.dumps({'OK2': '123123'}), content_type='application/json')

def browse(request,type):
    model = apps.get_model('leaklooker_app', type)
    all = model.objects.all()

    context = {"type": type,
               'all':all}


    return render(request, "browse.html", context=context)

def stats(request, type):
    if request.is_ajax() and request.method == 'GET':
        counter = tasks.stats(type=type)

        return HttpResponse(json.dumps({"Results":counter}), content_type='application/json')

def stats_db(request,type):
    if request.is_ajax() and request.method == 'GET':
        model = apps.get_model('leaklooker_app', type)
        all = model.objects.all().count()

        return HttpResponse(json.dumps({"Results":all}), content_type='application/json')

def delete(request,ip, type):
    if request.is_ajax() and request.method == 'GET':
        if type=='amazonbuckets':
            amazon = AmazonBuckets.objects.get(bucket=ip)
            amazon.delete()
        elif type == 'github':
            gitt = Github.objects.get(commit=ip)
            gitt.delete()
        else:



            
            model = apps.get_model('leaklooker_app', type)
            all = model.objects.get(ip=ip)

            with open("config.json","r+") as config:
                config_dict = json.load(config)
                config_dict['config']['blacklist'].append(ip)
                config.seek(0)  # <--- should reset file position to the beginning.
                json.dump(config_dict, config, indent=4)
                config.truncate()

            all.delete()

        return HttpResponse(json.dumps({"Results": "OK"}), content_type='application/json')

def confirm(request,ip, type):
    if request.is_ajax() and request.method == 'GET':
        if type=='amazonbuckets':
            amazon = AmazonBuckets.objects.get(bucket=ip)
            amazon.confirmed = True
            amazon.for_later = False

            amazon.save()
        elif type == 'github':
            gitt = Github.objects.get(commit=ip)
            gitt.confirmed = True
            gitt.for_later = False

            gitt.save()
        else:
            model = apps.get_model('leaklooker_app', type)
            all = model.objects.get(ip=ip)
            all.confirmed = True
            all.for_later = False

            all.save()

        return HttpResponse(json.dumps({"Results": "OK"}), content_type='application/json')

def for_later(request,ip,type):
    if request.is_ajax() and request.method == 'GET':
        if type=='amazonbuckets':
            amazon = AmazonBuckets.objects.get(bucket=ip)
            amazon.for_later = True
            amazon.confirmed = False

            amazon.save()
        elif type == 'github':
            gitt = Github.objects.get(commit=ip)
            gitt.confirmed = False
            gitt.for_later = True

            gitt.save()
        else:
            model = apps.get_model('leaklooker_app', type)
            all = model.objects.get(ip=ip)

            all.for_later = True
            all.confirmed = False

            all.save()

        return HttpResponse(json.dumps({"Results": "OK"}), content_type='application/json')

def elastic_search(request):
    return render(request, 'search.html', {})


def amazonbuckets(request):
    return render(request, "amazon.html",{})

def bruteforce_bucket(request):
    if request.is_ajax() and request.method == "GET":
        keyword = request.GET['keyword']

        gitlab_search_task = tasks.brute_buckets.delay(keyword=keyword)

        request.session['task_id'] = gitlab_search_task.task_id
        return HttpResponse(json.dumps({'task_id': gitlab_search_task.task_id}), content_type='application/json')
        # return HttpResponse(json.dumps(gitlab_search_task), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'OK2': 'OK'}), content_type='application/json')

def github(request):
    return render(request, "github.html",{})

def js(request):
    return render(request, "js.html",{})

def js_file(request):
    if request.is_ajax() and request.method == "GET":
        keyword = request.GET['keyword']
        print(keyword)
        gitlab_search_task = tasks.javascript_search.delay(keyword=keyword)

        request.session['task_id'] = gitlab_search_task.task_id
        return HttpResponse(json.dumps({'task_id': gitlab_search_task.task_id}), content_type='application/json')
        # return HttpResponse(json.dumps(gitlab_search_task), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'OK2': 'OK'}), content_type='application/json')

def github_repo(request):
    if request.is_ajax() and request.method == "GET":
        keyword = request.GET['keyword']
        print(keyword)
        gitlab_search_task = tasks.github_repo_search.delay(keyword=keyword)

        request.session['task_id'] = gitlab_search_task.task_id
        return HttpResponse(json.dumps({'task_id': gitlab_search_task.task_id}), content_type='application/json')
        # return HttpResponse(json.dumps(gitlab_search_task), content_type='application/json')
    else:
        return HttpResponse(json.dumps({'OK2': 'OK'}), content_type='application/json')
