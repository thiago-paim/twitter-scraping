from django.test import TestCase
from django.utils import timezone

from .models import Tweet, TwitterUser


class TweetModelTests(TestCase):
    
    def setUp(self):
        self.user = TwitterUser.objects.create(
            twitter_id='999',
            username='random_username',
            display_name='Random User',
            description='Just another user',
            account_created_at=timezone.now(),
        )
        
        self.tweet1 = Tweet.objects.create(
            twitter_id='111',
            content='test tweet',
            published_at=timezone.now(),
            user=self.user
        )
        self.tweet2 = Tweet.objects.create(
            twitter_id='112',
            content='test tweet reply',
            published_at=timezone.now(),
            in_reply_to_id='111',
            conversation_id='111',
            user=self.user
        )
        self.tweet3 = Tweet.objects.create(
            twitter_id='113',
            content='test tweet missing reply',
            published_at=timezone.now(),
            in_reply_to_id='222',
            conversation_id='222',
            user=self.user
        )
        self.tweet4 = Tweet.objects.create(
            twitter_id='114',
            content='test tweet reply reply',
            published_at=timezone.now(),
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