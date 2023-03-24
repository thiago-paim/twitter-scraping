from copy import deepcopy
from django.test import TestCase
from django.utils import timezone

from tweets.tests.fixtures import tweet1, tweet1_updated_tweet, tweet1_updated_user, tweet1_updated_both, tweet1_incomplete
from tweets.serializers import SnscrapeTwitterUserSerializer, SnscrapeTweetSerializer

tz = timezone.get_default_timezone()


class SnscrapeTweetSerializerTest(TestCase):
    
    def setUp(self):
        self.tweet1 = deepcopy(tweet1)
        self.tweet1_updated_tweet = deepcopy(tweet1_updated_tweet)
        self.tweet1_updated_user = deepcopy(tweet1_updated_user)
        self.tweet1_updated_both = deepcopy(tweet1_updated_both)
        
    def test_create_tweet(self):
        user_serializer = SnscrapeTwitterUserSerializer(data=self.tweet1.user)
        self.assertTrue(user_serializer.is_valid())
        user = user_serializer.save()
        
        serializer = SnscrapeTweetSerializer(data=self.tweet1)
        self.assertTrue(serializer.is_valid())
        tweet = serializer.save()
        self.assertEqual(tweet.twitter_id, '1636295637187584000')
        self.assertEqual(tweet.content, 'Test tweet content')
        self.assertEqual(tweet.published_at, timezone.datetime(2023, 3, 16, 9, 17, 35, tzinfo=tz))
        self.assertEqual(tweet.in_reply_to_id, None)
        self.assertEqual(tweet.conversation_id, '1636295637187584000')
        self.assertEqual(tweet.reply_count, 22)
        self.assertEqual(tweet.retweet_count, 13)
        self.assertEqual(tweet.like_count, 235)
        self.assertEqual(tweet.quote_count, 2)
        self.assertEqual(tweet.user.id, user.id)
        self.assertEqual(tweet.user.twitter_id, user.twitter_id)
        
    def test_create_tweet_and_user(self):
        serializer = SnscrapeTweetSerializer(data=self.tweet1)
        serializer.is_valid()
        self.assertTrue(serializer.is_valid())
        
        tweet = serializer.save()
        self.assertEqual(tweet.twitter_id, '1636295637187584000')
        self.assertEqual(tweet.content, 'Test tweet content')
        self.assertEqual(tweet.published_at, timezone.datetime(2023, 3, 16, 9, 17, 35, tzinfo=tz))
        self.assertEqual(tweet.in_reply_to_id, None)
        self.assertEqual(tweet.conversation_id, '1636295637187584000')
        self.assertEqual(tweet.reply_count, 22)
        self.assertEqual(tweet.retweet_count, 13)
        self.assertEqual(tweet.like_count, 235)
        self.assertEqual(tweet.quote_count, 2)

        user = tweet.user
        self.assertEqual(user.twitter_id, '30192824')
        self.assertEqual(user.username, 'GergelyOrosz')
        self.assertEqual(user.display_name, 'Gergely Orosz')
        self.assertEqual(user.description, 'Writing @Pragmatic_Eng & @EngGuidebook.')
        self.assertEqual(user.account_created_at, timezone.datetime(2009, 4, 10, 10, 1, 11, tzinfo=tz))
        self.assertEqual(user.followers_count, 202171)
        self.assertEqual(user.following_count, 1368)
        self.assertEqual(user.tweet_count, 24961)
        self.assertEqual(user.listed_count, 2268)
        
    def test_update_tweet_only(self):
        serializer = SnscrapeTweetSerializer(data=self.tweet1)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        serializer = SnscrapeTweetSerializer(data=self.tweet1_updated_tweet)
        self.assertTrue(serializer.is_valid())
        
        tweet = serializer.save()
        self.assertEqual(tweet.twitter_id, '1636295637187584000')
        self.assertEqual(tweet.reply_count, 32)
        self.assertEqual(tweet.retweet_count, 13)
        self.assertEqual(tweet.like_count, 335)
        self.assertEqual(tweet.quote_count, 2)

        user = tweet.user
        self.assertEqual(user.twitter_id, '30192824')
        self.assertEqual(user.followers_count, 202171)
        self.assertEqual(user.following_count, 1368)
        self.assertEqual(user.tweet_count, 24961)
        self.assertEqual(user.listed_count, 2268)
    
    def test_update_user_only(self):
        serializer = SnscrapeTweetSerializer(data=self.tweet1)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        serializer = SnscrapeTweetSerializer(data=self.tweet1_updated_user)
        self.assertTrue(serializer.is_valid())
        
        tweet = serializer.save()
        self.assertEqual(tweet.twitter_id, '1636295637187584000')
        self.assertEqual(tweet.reply_count, 22)
        self.assertEqual(tweet.retweet_count, 13)
        self.assertEqual(tweet.like_count, 235)
        self.assertEqual(tweet.quote_count, 2)

        user = tweet.user
        self.assertEqual(user.twitter_id, '30192824')
        self.assertEqual(user.followers_count, 202173)
        self.assertEqual(user.following_count, 1368)
        self.assertEqual(user.tweet_count, 24965)
        self.assertEqual(user.listed_count, 2268)
    
    def test_update_tweet_and_user(self):
        serializer = SnscrapeTweetSerializer(data=self.tweet1)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        serializer = SnscrapeTweetSerializer(data=self.tweet1_updated_both)
        self.assertTrue(serializer.is_valid())
        
        tweet = serializer.save()
        self.assertEqual(tweet.twitter_id, '1636295637187584000')
        self.assertEqual(tweet.reply_count, 32)
        self.assertEqual(tweet.retweet_count, 13)
        self.assertEqual(tweet.like_count, 335)
        self.assertEqual(tweet.quote_count, 2)

        user = tweet.user
        self.assertEqual(user.twitter_id, '30192824')
        self.assertEqual(user.followers_count, 202173)
        self.assertEqual(user.following_count, 1368)
        self.assertEqual(user.tweet_count, 24965)
        self.assertEqual(user.listed_count, 2268)
