from copy import deepcopy
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

_logger = logging.getLogger(__name__)


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
                                f'Skipping empty tweet entry {entry["entryId"]}'
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
                                    f'Unexpected home conversation entry ID: {item["entryId"]!r}'
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
                        if item["entryId"].startswith(f'{entry["entryId"]}-tweet-'):
                            if (
                                len(
                                    item["entryId"][len(entry["entryId"]) + 7 :].split(
                                        "-"
                                    )
                                )
                                > 1
                            ):
                                _logger.warning(
                                    f'Skipping unrecognised entry ID: {entry["entryId"]!r}'
                                )
                                continue
                            tweetId = int(item["entryId"][len(entry["entryId"]) + 7 :])
                            yield self._graphql_timeline_tweet_item_result_to_tweet(
                                item["item"]["itemContent"]["tweet_results"]["result"],
                                tweetId=tweetId,
                            )
                elif not entry["entryId"].startswith("cursor-"):
                    _logger.warning(
                        f'Skipping unrecognised entry ID: {entry["entryId"]!r}'
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
