from copy import deepcopy
from django.conf import settings
from django.utils import timezone
import json
import pandas as pd
from snscrape.modules.twitter import (
    TwitterProfileScraper,
    TweetRef,
    User as SNUser,
    Tweet as SNTweet,
)


def export_csv(queryset, filename=None):
    if not filename:
        filename = f"{queryset.model.__name__.lower()}s"
    time_signature = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    filepath = f"{settings.DEFAULT_EXPORT_PATH}{time_signature} {filename}.csv"
    chunksize = 1000

    df = pd.DataFrame(tweet.export() for tweet in queryset)
    df.to_csv(filepath, chunksize=chunksize)


class CustomTwitterProfileScraper(TwitterProfileScraper):
    def _graphql_timeline_tweet_item_result_to_tweet(self, result, tweetId=None):
        if result["__typename"] == "Tweet":
            if not "rest_id" in result["core"]["user_results"]["result"]:
                return TweetRef(id=result["rest_id"])
        return super()._graphql_timeline_tweet_item_result_to_tweet(result, tweetId)


def tweet_to_json(tweet):
    """Converts a snscrape.Tweet object to a JSON string"""
    tweet_dict = deepcopy(tweet.__dict__)

    if tweet_dict.get("quotedTweet"):
        tweet_dict["quotedTweet"] = tweet_to_json(tweet_dict["quotedTweet"])

    if tweet_dict.get("user"):
        user_dict = tweet_dict["user"].__dict__
        for key, value in user_dict.items():
            user_dict[key] = str(value)

    for key, value in tweet_dict.items():
        tweet_dict[key] = str(value)

    return json.dumps(tweet_dict)
