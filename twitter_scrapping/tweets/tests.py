from copy import deepcopy
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from .fixtures import tweet1, tweet1_updated_tweet, tweet1_updated_user, tweet1_updated_both, tweet1_incomplete
from .models import Tweet, TwitterUser
from .serializers import SnscrapeTwitterUserSerializer, SnscrapeTweetSerializer
from .tasks import save_scrapped_tweet, scrape_tweets


tz = timezone.get_default_timezone()

class TweetModelTests(TestCase):
    
    def setUp(self):
        self.user = TwitterUser.objects.create(
            twitter_id='999',
            username='random_username',
            display_name='Random User',
            description='Just another user',
            account_created_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
        )
        
        self.tweet1 = Tweet.objects.create(
            twitter_id='111',
            content='test tweet',
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            user=self.user
        )
        self.tweet2 = Tweet.objects.create(
            twitter_id='112',
            content='test tweet reply',
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            in_reply_to_id='111',
            conversation_id='111',
            user=self.user
        )
        self.tweet3 = Tweet.objects.create(
            twitter_id='113',
            content='test tweet missing reply',
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            in_reply_to_id='222',
            conversation_id='222',
            user=self.user
        )
        self.tweet4 = Tweet.objects.create(
            twitter_id='114',
            content='test tweet reply reply',
            published_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            in_reply_to_id='112',
            conversation_id='111',
            user=self.user
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


class TasksTest(TestCase):
    
    def setUp(self):
        self.tweet1 = deepcopy(tweet1)
        self.tweet1_incomplete = deepcopy(tweet1_incomplete)
    
    @patch('tweets.serializers.SnscrapeTweetSerializer.save')
    def test_save_scrapped_tweet(self, save_mock):
        save_scrapped_tweet(self.tweet1)
        save_mock.assert_called()
    
    @patch('tweets.serializers.SnscrapeTweetSerializer.save')
    def test_save_invalid_scrapped_tweet(self, save_mock):
        from rest_framework.serializers import ValidationError
        with self.assertRaises(ValidationError):
            save_scrapped_tweet(self.tweet1_incomplete)
            save_mock.assert_not_called()
    
    @patch('snscrape.modules.twitter.TwitterSearchScraper.get_items')
    @patch('snscrape.modules.twitter.TwitterTweetScraper.get_items')
    @patch('tweets.tasks.save_scrapped_tweet')
    def test_scrape_tweets(self, save_scrapped_tweet_mock, tweet_scrapper_mock, search_scrapper_mock):
        search_scrapper_mock.side_effect = [[self.tweet1].__iter__()]
        tweet_scrapper_mock.side_effect = [[self.tweet1].__iter__()]
        username = 'GergelyOrosz'
        since = '2023-03-15'
        until = '2023-03-16'
        
        scrape_tweets(username, since, until)
        save_scrapped_tweet_mock.assert_called_with(self.tweet1)