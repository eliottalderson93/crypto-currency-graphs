from django.conf.urls import url
from . import views
urlpatterns = [
    url('', views.graphs),
    url(r'^bokeh/time/(?P<firstCoin>\w+)/?$',views.bokeh),
    url(r'^bokeh/time/(?P<firstCoin>\w+)/(?P<begin>\w+)/(?P<end>\w+)/?$',views.bokeh),
    url(r'^bokeh/(?P<firstCoin>\w+)/(?P<secondCoin>\w+)/?$',views.bokeh),
    url(r'^bokeh/(?P<firstCoin>\w+)/(?P<secondCoin>\w+)/(?P<begin>\w+)/(?P<end>\w+)/?$',views.bokeh),

]
