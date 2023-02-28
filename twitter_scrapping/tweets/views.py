from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic

from .models import Tweet


class IndexView(generic.ListView):
    template_name  = 'tweets/index.html'
    context_object_name = 'latest_tweets'

    def get_queryset(self):
        return Tweet.objects.order_by('-published_at')[:5]


class DetailView(generic.DetailView):
    template_name  = 'tweets/detail.html'
    model = Tweet
    