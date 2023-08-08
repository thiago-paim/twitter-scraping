from django.db.models import Count
from tweets.models import Tweet, ScrapingRequest
from tweets.tasks import scrape_tweet_replies, record_tweet



def clean_duplicated_tweets():
    print(Tweet.objects.values('twitter_id', 'created').annotate(Count('id')).order_by().filter(id__count__gt=1).count())

    duplicated_tweets = Tweet.objects.values('twitter_id', 'created').annotate(Count('id')).order_by().filter(id__count__gt=1)
    duplicated_twitter_ids = list(duplicated_tweets.values_list('twitter_id', flat=True))

    for tid in duplicated_twitter_ids:
        tweets = Tweet.objects.filter(twitter_id=tid)
        t = tweets[0]
        print(f'Deleting {t.id=}, {t.twitter_id=}')
        tweets.delete()
        t.save()
        
        
    affected_reqs = ScrapingRequest.objects.filter(twitter_id__in=duplicated_twitter_ids)
    for req in affected_reqs:
        req.reset()