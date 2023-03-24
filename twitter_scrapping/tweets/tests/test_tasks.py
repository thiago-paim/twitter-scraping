from copy import deepcopy
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from tweets.models import Tweet, ScrappingRequest
from tweets.tests.fixtures import tweet1, tweet1_updated_tweet, tweet1_updated_user, tweet1_updated_both, tweet1_incomplete
from tweets.tasks import save_scrapped_tweet, scrape_tweets

tz = timezone.get_default_timezone()


class TasksTest(TestCase):
    
    def setUp(self):
        self.tweet1 = deepcopy(tweet1)
        self.tweet1_incomplete = deepcopy(tweet1_incomplete)
        self.req = ScrappingRequest.objects.create(
            username='GergelyOrosz',
            since=timezone.datetime(2023, 3, 15, tzinfo=tz),
            until=timezone.datetime(2023, 3, 17, tzinfo=tz),
            
        )

    def test_save_scrapped_tweet(self):
        t, created = save_scrapped_tweet(self.tweet1)
        self.assertEqual(created, True)
        self.assertEqual(t.twitter_id, str(self.tweet1.id))
    
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
        
        scrape_tweets(self.req.id)
        save_scrapped_tweet_mock.assert_called_with(self.tweet1)
