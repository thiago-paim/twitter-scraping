from copy import deepcopy
from django.test import TestCase
from django.utils import timezone

from tweets.models import ScrappingRequest
from tweets.serializers import SnscrapeTwitterUserSerializer, SnscrapeTweetSerializer
from tweets.tests.fixtures import (
    tweet1,
    tweet1_updated_tweet,
    tweet1_updated_user,
    tweet1_updated_both,
    tweet1_incomplete,
)

tz = timezone.get_default_timezone()


class SnscrapeTweetSerializerTest(TestCase):
    def setUp(self):
        self.tweet1 = deepcopy(tweet1)
        self.tweet1_updated_tweet = deepcopy(tweet1_updated_tweet)
        self.tweet1_updated_user = deepcopy(tweet1_updated_user)
        self.tweet1_updated_both = deepcopy(tweet1_updated_both)

        self.req = ScrappingRequest.objects.create(
            username="GergelyOrosz",
            since=timezone.datetime(2023, 3, 15, tzinfo=tz),
            until=timezone.datetime(2023, 3, 17, tzinfo=tz),
        )
        for t in [
            self.tweet1,
            self.tweet1_updated_tweet,
            self.tweet1_updated_user,
            self.tweet1_updated_both,
        ]:
            t.scrapping_request = self.req.id

    def test_create_tweet(self):
        user_serializer = SnscrapeTwitterUserSerializer(data=deepcopy(self.tweet1.user))
        self.assertTrue(user_serializer.is_valid())
        user = user_serializer.save()

        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1))
        self.assertTrue(serializer.is_valid())

        tweet, created = serializer.save()
        self.assertEqual(created, True)
        self.assertEqual(tweet.twitter_id, str(self.tweet1.id))
        self.assertEqual(tweet.content, self.tweet1.rawContent)
        self.assertEqual(tweet.published_at, self.tweet1.date)
        self.assertEqual(tweet.in_reply_to_id, self.tweet1.inReplyToTweetId)
        self.assertEqual(tweet.conversation_id, str(self.tweet1.conversationId))
        self.assertEqual(tweet.reply_count, self.tweet1.replyCount)
        self.assertEqual(tweet.retweet_count, self.tweet1.retweetCount)
        self.assertEqual(tweet.like_count, self.tweet1.likeCount)
        self.assertEqual(tweet.quote_count, self.tweet1.quoteCount)
        self.assertEqual(tweet.scrapping_request.id, self.req.id)
        self.assertEqual(tweet.user.id, user.id)
        self.assertEqual(tweet.user.twitter_id, user.twitter_id)

    def test_create_tweet_and_user(self):
        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1))
        serializer.is_valid()
        self.assertTrue(serializer.is_valid())

        tweet, created = serializer.save()
        self.assertEqual(created, True)
        self.assertEqual(tweet.twitter_id, str(self.tweet1.id))
        self.assertEqual(tweet.content, self.tweet1.rawContent)
        self.assertEqual(tweet.published_at, self.tweet1.date)
        self.assertEqual(tweet.in_reply_to_id, self.tweet1.inReplyToTweetId)
        self.assertEqual(tweet.conversation_id, str(self.tweet1.conversationId))
        self.assertEqual(tweet.reply_count, self.tweet1.replyCount)
        self.assertEqual(tweet.retweet_count, self.tweet1.retweetCount)
        self.assertEqual(tweet.like_count, self.tweet1.likeCount)
        self.assertEqual(tweet.quote_count, self.tweet1.quoteCount)
        self.assertEqual(tweet.scrapping_request.id, self.req.id)

        user = tweet.user
        self.assertEqual(user.twitter_id, str(self.tweet1.user.id))
        self.assertEqual(user.username, self.tweet1.user.username)
        self.assertEqual(user.display_name, self.tweet1.user.displayname)
        self.assertEqual(user.description, self.tweet1.user.rawDescription)
        self.assertEqual(user.account_created_at, self.tweet1.user.created)
        self.assertEqual(user.followers_count, self.tweet1.user.followersCount)
        self.assertEqual(user.following_count, self.tweet1.user.friendsCount)
        self.assertEqual(user.tweet_count, self.tweet1.user.statusesCount)
        self.assertEqual(user.listed_count, self.tweet1.user.listedCount)
        self.assertEqual(user.location, self.tweet1.user.location)

    def test_update_exact_tweet(self):
        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1))
        self.assertTrue(serializer.is_valid())
        tweet, created = serializer.save()
        self.assertEqual(created, True)

        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1))
        self.assertTrue(serializer.is_valid())

        tweet, created = serializer.save()
        self.assertEqual(created, False)
        self.assertEqual(tweet.twitter_id, str(self.tweet1.id))
        self.assertEqual(tweet.reply_count, self.tweet1.replyCount)
        self.assertEqual(tweet.retweet_count, self.tweet1.retweetCount)
        self.assertEqual(tweet.like_count, self.tweet1.likeCount)
        self.assertEqual(tweet.quote_count, self.tweet1.quoteCount)
        self.assertEqual(tweet.scrapping_request.id, self.req.id)

        user = tweet.user
        self.assertEqual(user.twitter_id, str(self.tweet1.user.id))
        self.assertEqual(user.username, self.tweet1.user.username)

    def test_update_tweet_only(self):
        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1))
        self.assertTrue(serializer.is_valid())
        tweet, created = serializer.save()
        self.assertEqual(created, True)

        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1_updated_tweet))
        self.assertTrue(serializer.is_valid())

        tweet, created = serializer.save()
        self.assertEqual(created, False)
        self.assertEqual(tweet.twitter_id, str(self.tweet1_updated_tweet.id))
        self.assertEqual(tweet.content, self.tweet1_updated_tweet.rawContent)
        self.assertEqual(tweet.published_at, self.tweet1_updated_tweet.date)
        self.assertEqual(
            tweet.in_reply_to_id, self.tweet1_updated_tweet.inReplyToTweetId
        )
        self.assertEqual(
            tweet.conversation_id, str(self.tweet1_updated_tweet.conversationId)
        )
        self.assertEqual(tweet.reply_count, self.tweet1_updated_tweet.replyCount)
        self.assertEqual(tweet.retweet_count, self.tweet1_updated_tweet.retweetCount)
        self.assertEqual(tweet.like_count, self.tweet1_updated_tweet.likeCount)
        self.assertEqual(tweet.quote_count, self.tweet1_updated_tweet.quoteCount)
        self.assertEqual(tweet.scrapping_request.id, self.req.id)

        user = tweet.user
        self.assertEqual(user.twitter_id, str(self.tweet1.user.id))
        self.assertEqual(user.username, self.tweet1.user.username)

    def test_update_user_only(self):
        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1))
        self.assertTrue(serializer.is_valid())
        tweet, created = serializer.save()
        self.assertEqual(created, True)

        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1_updated_user))
        self.assertTrue(serializer.is_valid())

        tweet, created = serializer.save()
        self.assertEqual(created, False)
        self.assertEqual(tweet.twitter_id, str(self.tweet1.id))
        self.assertEqual(tweet.reply_count, self.tweet1.replyCount)
        self.assertEqual(tweet.retweet_count, self.tweet1.retweetCount)
        self.assertEqual(tweet.like_count, self.tweet1.likeCount)
        self.assertEqual(tweet.quote_count, self.tweet1.quoteCount)
        self.assertEqual(tweet.scrapping_request.id, self.req.id)

        user = tweet.user
        self.assertEqual(user.twitter_id, str(self.tweet1_updated_user.user.id))
        self.assertEqual(user.username, self.tweet1_updated_user.user.username)
        self.assertEqual(user.display_name, self.tweet1_updated_user.user.displayname)
        self.assertEqual(user.description, self.tweet1_updated_user.user.rawDescription)
        self.assertEqual(user.account_created_at, self.tweet1_updated_user.user.created)
        self.assertEqual(
            user.followers_count, self.tweet1_updated_user.user.followersCount
        )
        self.assertEqual(
            user.following_count, self.tweet1_updated_user.user.friendsCount
        )
        self.assertEqual(user.tweet_count, self.tweet1_updated_user.user.statusesCount)
        self.assertEqual(user.listed_count, self.tweet1_updated_user.user.listedCount)
        self.assertEqual(user.location, self.tweet1_updated_user.user.location)

    def test_update_tweet_and_user(self):
        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1))
        self.assertTrue(serializer.is_valid())
        tweet, created = serializer.save()
        self.assertEqual(created, True)

        serializer = SnscrapeTweetSerializer(data=deepcopy(self.tweet1_updated_both))
        self.assertTrue(serializer.is_valid())

        tweet, created = serializer.save()
        self.assertEqual(created, False)
        self.assertEqual(tweet.twitter_id, str(self.tweet1_updated_both.id))
        self.assertEqual(tweet.reply_count, self.tweet1_updated_both.replyCount)
        self.assertEqual(tweet.retweet_count, self.tweet1_updated_both.retweetCount)
        self.assertEqual(tweet.like_count, self.tweet1_updated_both.likeCount)
        self.assertEqual(tweet.quote_count, self.tweet1_updated_both.quoteCount)
        self.assertEqual(tweet.scrapping_request.id, self.req.id)

        user = tweet.user
        self.assertEqual(user.twitter_id, str(self.tweet1_updated_both.user.id))
        self.assertEqual(user.username, self.tweet1_updated_both.user.username)
        self.assertEqual(user.display_name, self.tweet1_updated_both.user.displayname)
        self.assertEqual(user.description, self.tweet1_updated_both.user.rawDescription)
        self.assertEqual(user.account_created_at, self.tweet1_updated_both.user.created)
        self.assertEqual(
            user.followers_count, self.tweet1_updated_both.user.followersCount
        )
        self.assertEqual(
            user.following_count, self.tweet1_updated_both.user.friendsCount
        )
        self.assertEqual(user.tweet_count, self.tweet1_updated_both.user.statusesCount)
        self.assertEqual(user.listed_count, self.tweet1_updated_both.user.listedCount)
        self.assertEqual(user.location, self.tweet1_updated_both.user.location)
