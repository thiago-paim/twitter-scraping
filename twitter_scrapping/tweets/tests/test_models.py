from copy import deepcopy
from django.test import TestCase
from django.utils import timezone

from tweets.models import Tweet, TwitterUser, ScrappingRequest
from tweets.tasks import record_tweet
from tweets.tests.tweet_samples import (
    user_tweet_1,
    user_tweet_2,
    user_tweet_3,
)

tz = timezone.get_default_timezone()


class TweetModelTests(TestCase):
    def setUp(self):
        self.user = TwitterUser.objects.create(
            twitter_id="999",
            username="random_username",
            display_name="Random User",
            description="Just another user",
            account_created_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
        )

        self.tweet1 = Tweet.objects.create(
            twitter_id="111",
            content="test tweet",
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            user=self.user,
        )
        self.tweet2 = Tweet.objects.create(
            twitter_id="112",
            content="test tweet reply",
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            in_reply_to_id="111",
            conversation_id="111",
            user=self.user,
        )
        self.tweet3 = Tweet.objects.create(
            twitter_id="113",
            content="test tweet missing reply",
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            in_reply_to_id="222",
            conversation_id="222",
            user=self.user,
        )
        self.tweet4 = Tweet.objects.create(
            twitter_id="114",
            content="test tweet reply reply",
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            in_reply_to_id="112",
            conversation_id="111",
            user=self.user,
        )

    def test_get_in_reply_to_tweet_empty(self):
        self.tweet1.get_in_reply_to_tweet()
        self.assertEqual(self.tweet1.in_reply_to_tweet, None)

    def test_get_in_reply_to_tweet_success(self):
        self.tweet2.get_in_reply_to_tweet()
        self.assertEqual(self.tweet2.in_reply_to_tweet, self.tweet1)

    def test_get_in_reply_to_tweet_not_found(self):
        self.tweet3.get_in_reply_to_tweet()
        self.assertEqual(self.tweet3.in_reply_to_tweet, None)

    def test_get_conversation_tweet_empty(self):
        self.tweet1.get_conversation_tweet()
        self.assertEqual(self.tweet1.conversation_tweet, None)

    def test_get_conversation_tweet_equals_reply(self):
        self.tweet2.get_conversation_tweet()
        self.assertEqual(self.tweet2.conversation_tweet, self.tweet1)

    def test_get_conversation_tweet_different_reply(self):
        self.tweet4.get_conversation_tweet()
        self.assertEqual(self.tweet4.conversation_tweet, self.tweet1)

    def test_get_conversation_tweet_not_found(self):
        self.tweet3.get_conversation_tweet()
        self.assertEqual(self.tweet3.conversation_tweet, None)


class TweetManagerTestCase(TestCase):
    def setUp(self):
        self.user = TwitterUser.objects.create(
            twitter_id="999",
            username="random_username",
            display_name="Random User",
            description="Just another user",
            account_created_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
        )

        self.tweet1 = Tweet.objects.create(
            twitter_id="1",
            content="This tweet does not contain any bad words",
            published_at=timezone.datetime(2022, 1, 1, tzinfo=timezone.utc),
            user=self.user,
        )
        self.tweet2 = Tweet.objects.create(
            twitter_id="2",
            content="This tweet contains the word acefalo",
            published_at=timezone.datetime(2022, 1, 2, tzinfo=timezone.utc),
            user=self.user,
        )
        self.tweet3 = Tweet.objects.create(
            twitter_id="3",
            content="This tweet contains the word Acefala",
            published_at=timezone.datetime(2022, 1, 3, tzinfo=timezone.utc),
            user=self.user,
        )
        self.tweet4 = Tweet.objects.create(
            twitter_id="4",
            content="This tweet contains multiple bad words acefalo and acefala",
            published_at=timezone.datetime(2022, 1, 4, tzinfo=timezone.utc),
            user=self.user,
        )

    def test_contains_hate_words(self):
        filtered_tweets = Tweet.objects.contains_hate_words()
        self.assertEqual(
            list(filtered_tweets.values_list("pk", flat=True)),
            [2, 3, 4],
        )


class ScrappingRequestModelTest(TestCase):
    def setUp(self):
        self.req = ScrappingRequest.objects.create(
            username="GergelyOrosz",
            include_replies=False,
            since=timezone.datetime(2022, 1, 1, tzinfo=tz),
            until=timezone.datetime(2024, 1, 1, tzinfo=tz),
        )

    def test_create_conversation_scraping_requests(self):
        record_tweet(user_tweet_1, self.req.id)
        record_tweet(user_tweet_2, self.req.id)
        record_tweet(user_tweet_3, self.req.id)

        self.req.create_conversation_scraping_requests()

        requests = ScrappingRequest.objects.filter(
            username=self.req.username, include_replies=True, status="created"
        )

        self.assertEqual(requests.count(), 1)
        self.assertEqual(requests[0].twitter_id, str(user_tweet_1.id))

    def test_create_conversation_scraping_requests_doesnt_duplicate(self):
        record_tweet(user_tweet_1, self.req.id)
        record_tweet(user_tweet_2, self.req.id)
        record_tweet(user_tweet_3, self.req.id)

        self.req.create_conversation_scraping_requests()
        self.req.create_conversation_scraping_requests()

        requests = ScrappingRequest.objects.filter(
            username=self.req.username, include_replies=True, status="created"
        )

        self.assertEqual(requests.count(), 1)
        self.assertEqual(requests[0].twitter_id, str(user_tweet_1.id))

    def test_create_conversation_scraping_requests_duplicate_interrupted(self):
        record_tweet(user_tweet_1, self.req.id)
        record_tweet(user_tweet_2, self.req.id)
        record_tweet(user_tweet_3, self.req.id)

        self.req.create_conversation_scraping_requests()
        new_req = ScrappingRequest.objects.get(twitter_id=str(user_tweet_1.id))
        new_req.interrupt()
        self.req.create_conversation_scraping_requests()

        requests = ScrappingRequest.objects.filter(
            username=self.req.username, include_replies=True, status="created"
        )

        self.assertEqual(requests.count(), 1)
        self.assertEqual(requests[0].twitter_id, str(user_tweet_1.id))
