from copy import deepcopy
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import json
import pandas as pd
from tweets.models import Tweet, ScrapingRequest
from tweets.values import ELECTED_SP_STATE_DEP, ELECTED_SP_FED_DEP


def export(queryset, filename=None, format="csv"):
    print(f"export({queryset.count()=}, {filename=}, {format=})")
    if not filename:
        filename = f"{queryset.model.__name__.lower()}s"
    time_signature = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    filepath = f"{settings.DEFAULT_EXPORT_PATH}{time_signature} {filename}"
    df = pd.DataFrame(tweet.export() for tweet in queryset)

    if format == "csv":
        filepath = f"{filepath}.csv"
        chunksize = 1000
        df.to_csv(filepath, chunksize=chunksize, sep=";")

    if format == "parquet":
        filepath = f"{filepath}.parquet"
        df.to_parquet(filepath)


def export_tweets_by_users_threads(
    users, filename=None, election_tweets=True, min_length=None, format="csv"
):
    queryset = Tweet.objects.filter(conversation_tweet__user__username__in=users)

    if election_tweets:
        since = timezone.make_aware(datetime.strptime("2022-09-01", "%Y-%m-%d"))
        until = timezone.make_aware(datetime.strptime("2022-11-01", "%Y-%m-%d"))
        queryset = queryset.filter(published_at__gte=since, published_at__lte=until)

    if min_length:
        queryset = queryset.filter(content__length__gt=min_length)

    export(queryset, filename=filename, format=format)


def export_sp_est_deps(min_length=None, format="csv"):
    return export_tweets_by_users_threads(
        users=ELECTED_SP_STATE_DEP,
        filename="sp_est_deps_tweets",
        format=format,
        min_length=min_length,
    )


def export_sp_fed_deps(min_length=None, format="csv"):
    return export_tweets_by_users_threads(
        users=ELECTED_SP_FED_DEP,
        filename="sp_fed_deps_tweets",
        format=format,
        min_length=min_length,
    )


def tweet_to_json(tweet):
    """Converts a snscrape.Tweet object to a JSON string"""
    tweet_dict = deepcopy(tweet.__dict__)

    if tweet_dict.get("quotedTweet"):
        tweet_dict["quotedTweet"] = tweet_to_json(tweet_dict["quotedTweet"])

    if tweet_dict.get("retweetedTweet"):
        tweet_dict["retweetedTweet"] = tweet_to_json(tweet_dict["retweetedTweet"])

    if tweet_dict.get("user"):
        user_dict = tweet_dict["user"].__dict__
        for key, value in user_dict.items():
            user_dict[key] = str(value)

    for key, value in tweet_dict.items():
        tweet_dict[key] = str(value)

    return json.dumps(tweet_dict)


def clear_unwanted_rt_requests():
    rts_ids = Tweet.objects.retweeted_tweets().values_list("twitter_id", flat=True)
    reqs_for_rts = ScrapingRequest.objects.filter(twitter_id__in=rts_ids)
    print(f"reqs_for_rts count: {len(reqs_for_rts)}")
    deleted = []
    for req in reqs_for_rts:
        try:
            tweet = Tweet.objects.get(twitter_id=req.twitter_id)
        except Tweet.DoesNotExist:
            deleted.append((req.id, req.username, req.twitter_id))
            req.delete()
            continue
        if tweet.user.username.lower() != req.username:
            deleted.append((req.id, req.username, req.twitter_id))
            req.delete()
            continue
    print(f"deleted count: {len(deleted)}")
    return deleted


def clear_unwanted_qt_requests():
    qts_ids = Tweet.objects.quoted_tweets().values_list("twitter_id", flat=True)
    reqs_for_qts = ScrapingRequest.objects.filter(twitter_id__in=qts_ids)
    print(f"reqs_for_qts count: {len(reqs_for_qts)}")
    deleted = []
    for req in reqs_for_qts:
        try:
            tweet = Tweet.objects.get(twitter_id=req.twitter_id)
        except Tweet.DoesNotExist:
            deleted.append((req.id, req.username, req.twitter_id))
            req.delete()
            continue
        if tweet.user.username.lower() != req.username:
            deleted.append((req.id, req.username, req.twitter_id))
            req.delete()
            continue
    print(f"deleted count: {len(deleted)}")
    return deleted


def clear_duplicated_requests(username):
    tweets = Tweet.objects.filter(
        user__username__iexact=username, in_reply_to_id__isnull=True
    )
    requests = ScrapingRequest.objects.filter(
        username__iexact=username,
        include_replies=True,
        status="created",
        twitter_id__isnull=False,
    )
    print(f"{len(tweets)=}, {len(requests)=}")

    for tweet in tweets:
        reqs = requests.filter(twitter_id=tweet.twitter_id)
        if reqs.count() > 1:
            print(
                tweet.id,
                tweet.twitter_id,
                tweet.user.username,
                reqs.count(),
                [r.id for r in reqs],
            )
            for req in reqs[1:]:
                req.delete()
