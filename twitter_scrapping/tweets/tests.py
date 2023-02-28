from django.test import TestCase
from django.utils import timezone

from .models import Tweet


class TweetModelTests(TestCase):
    
    def test_has_in_reply_to(self):
        reply_tweet = Tweet(
            twitter_id='112',
            content='test tweet reply',
            published_at=timezone.now(),
            in_reply_to='111',
            username='witty sername',
            user_id='1'
        )
        self.assertIs(reply_tweet.is_reply(), True)
    
    def test_empty_in_reply_to(self):
        reply_tweet = Tweet(
            twitter_id='112',
            content='test tweet reply',
            published_at=timezone.now(),
            username='witty sername',
            user_id='1'
        )
        self.assertIs(reply_tweet.is_reply(), False)