from django.urls import path, include
from leaklooker_app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/type', views.type, name='type'),
    path('search/keyword', views.keyword, name='keyword'),
    path('monitor', views.monitor, name='monitor'),
    path('notifications', views.notifications, name='notifications'),
    path('notifications/delete/<id>', views.delete_notification, name='delete_notification'),

    path('search/<type>', views.search, name='search'),
    path('search/<type>/search_results', views.search_results, name='search_results'),
    path('browse/<type>', views.browse, name='browse'),

    path('search/stats/<type>', views.stats, name='stats'),
    path('search/stats/db/<type>', views.stats_db, name='stats_db'),
    path('<type>/delete/<ip>', views.delete, name='delete'),
    path('<type>/confirm/<ip>', views.confirm, name='confirm'),
    path('<type>/later/<ip>', views.for_later, name='for_later'),
    path('database', views.database, name='database'),
    path('keyword/search', views.keyword_search_results, name='keyword_search_results'),
    path(r'^celery-progress/', include('celery_progress.urls')),
    path('get-task-info/', views.get_task_info, name="get_task_info"),
    path('amazon_buckets/', views.amazonbuckets, name="amazonbuckets"),
    # path('amazon_buckets/delete/', views.amazonbuckets, name="amazonbuckets"),
    path('amazon_buckets/bruteforce', views.bruteforce_bucket, name="bruteforce_bucket"),
    path('github/', views.github, name="github"),
    path('github/github_repo', views.github_repo, name="github_repo"),
    path('javascript/', views.js, name="javascript"),
    path('javascript/javascript_file', views.js_file, name="javascript_file"),

]
