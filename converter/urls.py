from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('iso2dcat/', views.iso2dcat, name='iso2dcat'),
    path('iso2dcat/convert/', views.convert_iso2dcat, name='convert_iso2dcat'),
    path('dcat2iso/', views.dcat2iso, name='dcat2iso'),
    path('dcat2iso/convert/', views.convert_dcat2iso, name='convert_dcat2iso'),
    path('validate/', views.validate, name='validate'),
]
