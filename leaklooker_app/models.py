from django.db import models

# Create your models here.
class Search(models.Model):
    id = models.AutoField(primary_key=True)

    type = models.CharField(max_length=100)
    keyword = models.CharField(max_length=100)
    network = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)

class DbType(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Gitlab(DbType):
    url = models.CharField(max_length=100)

class Elastic(DbType):
    name = models.CharField(max_length=100)
    indices =models.CharField(max_length=10000)
    size = models.CharField(max_length=100)

class Dirs(DbType):
    dirs = models.CharField(max_length=10000)
    url = models.CharField(max_length=100)

class Jenkins(DbType):
    jobs = models.CharField(max_length=10000)
    url = models.CharField(max_length=100)

class Mongo(DbType):
    databases = models.CharField(max_length=10000)
    size = models.CharField(max_length=100)

class Rsync(DbType):
    shares = models.CharField(max_length=10000)

class Sonarqube(DbType):
    url = models.CharField(max_length=10000)

class Couchdb(DbType):
    pass

class Kibana(DbType):
    pass

class Cassandra(DbType):
    keyspaces = models.CharField(max_length=10000)

class Rethink(DbType):
    databases = models.CharField(max_length=10000)

class Monitor(models.Model):
    keyword = models.CharField(max_length=100)
    network = models.CharField(max_length=100)
    types = models.CharField(max_length=1000)
    created_on = models.DateTimeField(auto_now_add=True)

