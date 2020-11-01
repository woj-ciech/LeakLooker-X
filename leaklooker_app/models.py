from django.db import models


# Create your models here.
class Search(models.Model):
    id = models.AutoField(primary_key=True)

    type = models.CharField(max_length=100)
    keyword = models.CharField(max_length=100)
    network = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)

class Gitlab(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)

class Ftp(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    files = models.CharField(max_length=10000)
    indicator = models.CharField(max_length=10000)


class Elastic(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    indices =models.CharField(max_length=10000)
    size = models.CharField(max_length=100)
    indicator = models.CharField(max_length=10000)


class Keys(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    title = models.CharField(max_length=1000, null=True)

class Amazonbe(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    buckets = models.CharField(max_length=10000)

class AmazonBuckets(models.Model):
    bucket = models.CharField(max_length=1000)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)

class Github(models.Model):
    commit = models.CharField(max_length=1000)
    path = models.CharField(max_length=1000)
    secret = models.CharField(max_length=10000)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    keyword = models.CharField(max_length=10000)

class Javascript(models.Model):
    secrets = models.CharField(max_length=1000)
    path = models.CharField(max_length=10000)
    context = models.CharField(max_length=10000)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    keyword = models.CharField(max_length=10000)

class Dirs(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    dirs = models.CharField(max_length=10000)
    url = models.CharField(max_length=100)
    indicator = models.CharField(max_length=10000)

class Jenkins(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    jobs = models.CharField(max_length=10000)
    url = models.CharField(max_length=100)
    indicator = models.CharField(max_length=10000)

class Amazons3be(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    files = models.CharField(max_length=10000)
    url = models.CharField(max_length=100)
    indicator = models.CharField(max_length=10000)

class Mongo(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    databases = models.CharField(max_length=10000)
    size = models.CharField(max_length=100)
    indicator = models.CharField(max_length=10000)


class Rsync(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    shares = models.CharField(max_length=10000)

class Sonarqube(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    url = models.CharField(max_length=10000)

class Couchdb(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)

class Kibana(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)

class Cassandra(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    keyspaces = models.CharField(max_length=10000)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)

class Rethink(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    databases = models.CharField(max_length=10000)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)

class Monitor(models.Model):
    keyword = models.CharField(max_length=100)
    network = models.CharField(max_length=100)
    types = models.CharField(max_length=1000)
    created_on = models.DateTimeField(auto_now_add=True)

class Angular(models.Model):
    search = models.ForeignKey(Search, on_delete=models.CASCADE)
    ip = models.CharField(max_length=100)
    port = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    for_later = models.BooleanField(default=False)
    title = models.CharField(max_length=1000, null=True)
    path =models.CharField(max_length=1000, null=True)


