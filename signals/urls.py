from django.urls import path

from . import views

app_name = 'signals'

urlpatterns = [
  path('', views.index, name='index'),
  path('strategies/post_covid', views.run_strategy, name='run_strategy'),
  path('<int:signal_id>', views.detail, name='signal_detail'),
]
