from copy import deepcopy
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import json
import logging
import pandas as pd
from snscrape.base import ScraperException
from snscrape.modules.twitter import (
    TwitterProfileScraper,
    TwitterTweetScraper,
    TweetRef,
    User as SNUser,
    Tweet as SNTweet,
)
from tweets.models import Tweet, ScrapingRequest
from tweets.values import ELECTED_SP_STATE_DEP, ELECTED_SP_FED_DEP

_logger = logging.getLogger(__name__)


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
    
def export_tweets_by_users_threads(users, filename=None, election_tweets=True, min_length=None, format="csv"):
    queryset = Tweet.objects.filter(
        conversation_tweet__user__username__in=users
    )
    
    if election_tweets:
        since = timezone.make_aware(datetime.strptime("2022-09-01", "%Y-%m-%d"))
        until = timezone.make_aware(datetime.strptime("2022-11-01", "%Y-%m-%d"))
        queryset = queryset.filter(published_at__gte=since, published_at__lte=until)
        
    if min_length:
        queryset = queryset.filter(content__length__gt=min_length)
        
    export(queryset, filename=filename, format=format)
    
def export_sp_est_deps(min_length=None, format="csv"):
    return export_tweets_by_users_threads(
        users=ELECTED_SP_STATE_DEP, filename='sp_est_deps_tweets', format=format, min_length=min_length
    )
    
def export_sp_fed_deps(min_length=None, format="csv"):
    return export_tweets_by_users_threads(
        users=ELECTED_SP_FED_DEP, filename='sp_fed_deps_tweets', format=format, min_length=min_length
    )


# To Do: Apagar estes Scrapers customizados e atualizar a versão do SNScrape com a correção oficial
class CustomTwitterProfileScraper(TwitterProfileScraper):
    def _graphql_timeline_tweet_item_result_to_tweet(self, result, tweetId=None):
        if result["__typename"] == "Tweet":
            if not "rest_id" in result["core"]["user_results"]["result"]:
                return TweetRef(id=result["rest_id"])
        return super()._graphql_timeline_tweet_item_result_to_tweet(result, tweetId)


class CustomTwitterTweetScraper(TwitterTweetScraper):
    # Workaround for dealing with issue when scraping tweet 1651646573225418756
    def _graphql_timeline_instructions_to_tweets(
        self, instructions, includeConversationThreads=False
    ):
        for instruction in instructions:
            if instruction["type"] != "TimelineAddEntries":
                continue
            for entry in instruction["entries"]:
                if entry["entryId"].startswith("tweet-"):
                    tweetId = int(entry["entryId"].split("-", 1)[1])
                    if (
                        entry["content"]["entryType"] == "TimelineTimelineItem"
                        and entry["content"]["itemContent"]["itemType"]
                        == "TimelineTweet"
                    ):
                        if (
                            "result"
                            not in entry["content"]["itemContent"]["tweet_results"]
                        ):
                            _logger.warning(
                                f"Skipping empty tweet entry {entry['entryId']}"
                            )
                            continue
                        yield self._graphql_timeline_tweet_item_result_to_tweet(
                            entry["content"]["itemContent"]["tweet_results"]["result"],
                            tweetId=tweetId,
                        )
                    else:
                        _logger.warning("Got unrecognised timeline tweet item(s)")
                elif entry["entryId"].startswith("homeConversation-"):
                    if entry["content"]["entryType"] == "TimelineTimelineModule":
                        for item in entry["content"]["items"]:
                            if (
                                not item["entryId"].startswith("homeConversation-")
                                or "-tweet-" not in item["entryId"]
                            ):
                                raise ScraperException(
                                    f"Unexpected home conversation entry ID: {item['entryId']!r}"
                                )
                            tweetId = int(item["entryId"].split("-tweet-", 1)[1])
                            if (
                                item["item"]["itemContent"]["itemType"]
                                == "TimelineTweet"
                            ):
                                if (
                                    "result"
                                    in item["item"]["itemContent"]["tweet_results"]
                                ):
                                    yield self._graphql_timeline_tweet_item_result_to_tweet(
                                        item["item"]["itemContent"]["tweet_results"][
                                            "result"
                                        ],
                                        tweetId=tweetId,
                                    )
                                else:
                                    yield TweetRef(id=tweetId)
                elif includeConversationThreads and entry["entryId"].startswith(
                    "conversationthread-"
                ):  # TODO show more cursor?
                    for item in entry["content"]["items"]:
                        if item["entryId"].startswith(f"{entry['entryId']}-tweet-"):
                            if (
                                len(
                                    item["entryId"][len(entry["entryId"]) + 7 :].split(
                                        "-"
                                    )
                                )
                                > 1
                            ):
                                _logger.warning(
                                    f"Skipping unrecognised entry ID: {entry['entryId']!r}"
                                )
                                continue
                            tweetId = int(item["entryId"][len(entry["entryId"]) + 7 :])
                            yield self._graphql_timeline_tweet_item_result_to_tweet(
                                item["item"]["itemContent"]["tweet_results"]["result"],
                                tweetId=tweetId,
                            )
                elif not entry["entryId"].startswith("cursor-"):
                    _logger.warning(
                        f"Skipping unrecognised entry ID: {entry['entryId']!r}"
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
