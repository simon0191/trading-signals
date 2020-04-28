from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Signal
from .strategies.post_covid_strategy import PostCovidStrategy

def index(request):
  signals = Signal.objects.order_by('-created_at')[:50]
  context = {
    'signals': signals
  }
  return render(request, 'signals/index.html', context)

def run_strategy(request):
  strategy = PostCovidStrategy()
  prospects = strategy.run(save=True)

  return HttpResponse(f"{len(prospects)} prospects found")

def detail(request, signal_id):
  signal = get_object_or_404(Signal, pk=signal_id)
  return render(request, 'signals/show.html', {'signal': signal})
