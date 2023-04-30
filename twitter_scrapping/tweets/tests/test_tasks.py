from copy import deepcopy
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from tweets.models import Tweet, ScrappingRequest
from tweets.tests.fixtures import (
    tweet1,
    tweet1_incomplete,
)
from tweets.tests.tweet_samples import (
    normal_tweet,
    tweet_in_reply_to,
    tweet_replying_another_reply,
    tweet_with_quoted_tweet,
    tweet_with_quoted_tombstone,
    tweet_with_retweet,
    user_tweet_1,
    user_tweet_2,
    user_tweet_3,
)
from tweets.tasks import (
    save_scrapped_tweet,
    scrape_tweets_and_replies,
    record_tweet,
    scrape_user_tweets,
    scrape_tweet_replies,
)
from tweets.utils import tweet_to_json

tz = timezone.get_default_timezone()


class BaseTweetTestCase(TestCase):
    def _validate_user(self, user, scraped_user):
        self.assertEqual(user.twitter_id, str(scraped_user.id))
        self.assertEqual(user.username, scraped_user.username)
        self.assertEqual(user.display_name, scraped_user.displayname)
        self.assertEqual(user.description, scraped_user.rawDescription)
        self.assertEqual(user.account_created_at, scraped_user.created)
        self.assertEqual(user.location, scraped_user.location)
        self.assertEqual(user.followers_count, scraped_user.followersCount)
        self.assertEqual(user.following_count, scraped_user.friendsCount)
        self.assertEqual(user.tweet_count, scraped_user.statusesCount)
        self.assertEqual(user.listed_count, scraped_user.listedCount)

    def _validate_tweet(self, tweet, scraped_tweet):
        self.assertEqual(tweet.scrapping_request.id, self.req.id)
        self.assertEqual(tweet.twitter_id, str(scraped_tweet.id))
        self.assertEqual(tweet.content, scraped_tweet.rawContent)
        self.assertEqual(tweet.published_at, scraped_tweet.date)
        self.assertEqual(
            tweet.in_reply_to_id,
            str(scraped_tweet.inReplyToTweetId)
            if scraped_tweet.inReplyToTweetId
            else None,
        )
        self.assertEqual(
            tweet.conversation_id,
            str(scraped_tweet.conversationId) if scraped_tweet.conversationId else None,
        )
        self.assertEqual(
            tweet.retweeted_id,
            str(scraped_tweet.retweetedTweet.id)
            if scraped_tweet.retweetedTweet
            else None,
        )
        self.assertEqual(
            tweet.retweeted_tweet.twitter_id if tweet.retweeted_tweet else None,
            str(scraped_tweet.retweetedTweet.id) if tweet.retweeted_tweet else None,
        )
        self.assertEqual(
            tweet.quoted_id,
            str(scraped_tweet.quotedTweet.id) if scraped_tweet.quotedTweet else None,
        )
        self.assertEqual(
            tweet.quoted_tweet.twitter_id if tweet.quoted_tweet else None,
            str(scraped_tweet.quotedTweet.id) if tweet.quoted_tweet else None,
        )
        self.assertEqual(tweet.reply_count, scraped_tweet.replyCount)
        self.assertEqual(tweet.retweet_count, scraped_tweet.retweetCount)
        self.assertEqual(tweet.like_count, scraped_tweet.likeCount)
        self.assertEqual(tweet.quote_count, scraped_tweet.quoteCount)
        self.assertEqual(tweet.view_count, scraped_tweet.viewCount)


class RecordTweetTest(BaseTweetTestCase):
    def setUp(self):
        self.req = ScrappingRequest.objects.create(
            username="GergelyOrosz",
            since=timezone.datetime(2022, 1, 1, tzinfo=tz),
            until=timezone.datetime(2024, 1, 1, tzinfo=tz),
        )

    def test_record_tweet(self):
        scraped_tweet = deepcopy(normal_tweet)
        tweet, created = record_tweet(scraped_tweet, self.req.id)
        tweet_json = tweet_to_json(deepcopy(scraped_tweet))

        self._validate_tweet(tweet, scraped_tweet)
        self._validate_user(tweet.user, scraped_tweet.user)
        self.assertEqual(tweet.raw_tweet_object, tweet_json)

    def test_record_tweet_quoted_tweet(self):
        scraped_tweet = deepcopy(tweet_with_quoted_tweet)
        tweet, created = record_tweet(scraped_tweet, self.req.id)
        tweet_json = tweet_to_json(deepcopy(scraped_tweet))
        qt_tweet_json = tweet_to_json(deepcopy(scraped_tweet.quotedTweet))

        self._validate_tweet(tweet, scraped_tweet)
        self._validate_user(tweet.user, scraped_tweet.user)
        self.assertEqual(tweet.raw_tweet_object, tweet_json)

        self._validate_user(tweet.quoted_tweet.user, scraped_tweet.quotedTweet.user)
        self._validate_tweet(tweet.quoted_tweet, scraped_tweet.quotedTweet)
        self.assertEqual(tweet.quoted_tweet.raw_tweet_object, qt_tweet_json)

    def test_record_tweet_quoted_tombstone(self):
        scraped_tweet = deepcopy(tweet_with_quoted_tombstone)
        tweet, created = record_tweet(scraped_tweet, self.req.id)
        tweet_json = tweet_to_json(deepcopy(scraped_tweet))

        self._validate_tweet(tweet, scraped_tweet)
        self._validate_user(tweet.user, scraped_tweet.user)
        self.assertEqual(tweet.raw_tweet_object, tweet_json)

    def test_record_tweet_retweeted_tweet(self):
        scraped_tweet = deepcopy(tweet_with_retweet)
        tweet, created = record_tweet(scraped_tweet, self.req.id)
        tweet_json = tweet_to_json(deepcopy(scraped_tweet))
        rt_tweet_json = tweet_to_json(deepcopy(scraped_tweet.retweetedTweet))

        self._validate_tweet(tweet, scraped_tweet)
        self._validate_user(tweet.user, scraped_tweet.user)
        self.assertEqual(tweet.raw_tweet_object, tweet_json)

        self._validate_user(
            tweet.retweeted_tweet.user, scraped_tweet.retweetedTweet.user
        )
        self._validate_tweet(tweet.retweeted_tweet, scraped_tweet.retweetedTweet)
        self.assertEqual(tweet.retweeted_tweet.raw_tweet_object, rt_tweet_json)

    def test_record_tweet_retweeted_tombstone(self):
        ...  # Requires sample tweet

    def test_record_tweet_in_reply_to(self):
        scraped_tweet = deepcopy(tweet_in_reply_to)
        tweet, created = record_tweet(scraped_tweet, self.req.id)
        tweet_json = tweet_to_json(deepcopy(scraped_tweet))

        self._validate_tweet(tweet, scraped_tweet)
        self._validate_user(tweet.user, scraped_tweet.user)
        self.assertEqual(tweet.raw_tweet_object, tweet_json)

    def test_record_tweet_in_reply_to_another_reply(self):
        scraped_tweet = deepcopy(tweet_replying_another_reply)
        tweet, created = record_tweet(scraped_tweet, self.req.id)
        tweet_json = tweet_to_json(deepcopy(scraped_tweet))

        self._validate_tweet(tweet, scraped_tweet)
        self._validate_user(tweet.user, scraped_tweet.user)
        self.assertEqual(tweet.raw_tweet_object, tweet_json)


class ScrapeUserTweetsTest(BaseTweetTestCase):
    def setUp(self):
        self.req = ScrappingRequest.objects.create(
            username="GergelyOrosz",
            since=timezone.datetime(2022, 1, 1, tzinfo=tz),
            until=timezone.datetime(2024, 1, 1, tzinfo=tz),
        )

    @patch("tweets.utils.CustomTwitterProfileScraper.get_items")
    @patch("tweets.tasks.start_next_scrapping_request")
    def test_scrape_user_tweets(
        self, start_next_scrapping_request_mock, user_scraper_mock
    ):
        user_scraper_mock.side_effect = [
            [user_tweet_1, user_tweet_2, user_tweet_3].__iter__()
        ]
        scrape_user_tweets(self.req.id)
        tweets = Tweet.objects.all()
        self._validate_tweet(tweets[0], user_tweet_1)
        self._validate_tweet(tweets[1], user_tweet_2)
        self._validate_tweet(tweets[2], user_tweet_3)

        # Test that related ScrapingRequests were created

    def test_tombstone(self):
        ...

    def test_tweetref(self):
        ...


class ScrapeTweetRepliesTest(BaseTweetTestCase):
    def setUp(self):
        self.req = ScrappingRequest.objects.create(
            username="GergelyOrosz",
            since=timezone.datetime(2022, 1, 1, tzinfo=tz),
            until=timezone.datetime(2024, 1, 1, tzinfo=tz),
        )

    @patch("tweets.tasks.TwitterTweetScraper.get_items")
    @patch("tweets.tasks.start_next_scrapping_request")
    def test_scrape_tweet_replies(
        self, start_next_scrapping_request_mock, scraper_mock
    ):
        scraper_mock.side_effect = [
            [normal_tweet, tweet_in_reply_to, tweet_replying_another_reply].__iter__()
        ]
        scrape_tweet_replies(normal_tweet.id, self.req.id)
        tweets = Tweet.objects.all()
        self._validate_tweet(tweets[0], normal_tweet)
        self._validate_tweet(tweets[1], tweet_in_reply_to)
        self._validate_tweet(tweets[2], tweet_replying_another_reply)

    def test_tombstone(self):
        ...

    def test_tweetref(self):
        ...


class TasksTest(TestCase):
    def setUp(self):
        self.tweet1 = deepcopy(tweet1)
        self.tweet1_incomplete = deepcopy(tweet1_incomplete)
        self.req = ScrappingRequest.objects.create(
            username="GergelyOrosz",
            since=timezone.datetime(2023, 3, 15, tzinfo=tz),
            until=timezone.datetime(2023, 3, 17, tzinfo=tz),
        )

    def test_save_scrapped_tweet(self):
        t, created = save_scrapped_tweet(self.tweet1, self.req.id)
        self.assertEqual(created, True)
        self.assertEqual(t.twitter_id, str(self.tweet1.id))
        self.assertEqual(t.scrapping_request, self.req)

    @patch("tweets.serializers.SnscrapeTweetSerializer.save")
    def test_save_invalid_scrapped_tweet(self, save_mock):
        from rest_framework.serializers import ValidationError

        with self.assertRaises(ValidationError):
            save_scrapped_tweet(self.tweet1_incomplete, self.req.id)
            save_mock.assert_not_called()

    @patch("snscrape.modules.twitter.TwitterSearchScraper.get_items")
    @patch("snscrape.modules.twitter.TwitterTweetScraper.get_items")
    @patch("tweets.tasks.save_scrapped_tweet")
    def test_scrape_tweets_and_replies(
        self, save_scrapped_tweet_mock, tweet_scrapper_mock, search_scrapper_mock
    ):
        search_scrapper_mock.side_effect = [[self.tweet1].__iter__()]
        tweet_scrapper_mock.side_effect = [[self.tweet1].__iter__()]

        scrape_tweets_and_replies(self.req.id)
        save_scrapped_tweet_mock.assert_called_with(self.tweet1, self.req.id)
