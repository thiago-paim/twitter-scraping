from django.test import TestCase
from django.utils import timezone
from snscrape.modules.twitter import User as SNScrapeUser

from .models import Tweet, TwitterUser
from .serializers import SnscrapeTwitterUserSerializer, SnscrapeTweetSerializer


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
        
        
class SerializerTests(TestCase):
    def setUp(self):
        self.snscrape_user_kwargs = {
            'username': 'GergelyOrosz',
            'id': 30192824,
            'displayname': 'Gergely Orosz',
            'rawDescription': 'Writing @Pragmatic_Eng & @EngGuidebook. Advisor @mobile__dev. Uber & Skype alumni. Great tech jobs: https://t.co/MJ0eAtlaS1. Contact: https://t.co/POWftUprCb',
            'renderedDescription': 'Writing @Pragmatic_Eng & @EngGuidebook. Advisor @mobile__dev. Uber & Skype alumni. Great tech jobs: pragmaticurl.com/talent. Contact: pragmaticurl.com/contact',
            'verified': False,
            'created': timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            'followersCount': 201772,
            'friendsCount': 1368,
            'statusesCount': 24929,
            'favouritesCount': 32243,
            'listedCount': 2267,
            'mediaCount': 2508,
            'location': 'Amsterdam, The Netherlands',
        }
        
        self.snscrape_tweet_kwargs = {
            'url': 'https://twitter.com/GergelyOrosz/status/1636295637187584000',
            'date': timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            'rawContent': 'When I talked w ~70 companies about what vendor costs they are reducing, the two most frequently mentioned was AWS/GCP and Datadog. Simply because they were usually by far the biggest spend.\n\nGiven DDG is usage based, reducing it is usually easier.\n\nMore:  https://t.co/NxOVEcYCds',
            'renderedContent': 'When I talked w ~70 companies about what vendor costs they are reducing, the two most frequently mentioned was AWS/GCP and Datadog. Simply because they were usually by far the biggest spend.\n\nGiven DDG is usage based, reducing it is usually easier.\n\nMore:  newsletter.pragmaticengineer.com/p/vendor-spend…',
            'id': 1636295637187584000,
            'user': None,
            'replyCount': 18,
            'retweetCount': 10,
            'likeCount': 180,
            'quoteCount': 2,
            'conversationId': 1636295637187584000,
            'lang': 'en',
            'source': None,
            'sourceUrl': None,
            'sourceLabel': None,
            'links': [],
            'media': None,
            'retweetedTweet': None,
            'quotedTweet': None,
            'inReplyToTweetId': None,
            'inReplyToUser': None,
            'mentionedUsers': None,
            'coordinates': None,
            'place': None,
            'hashtags': None,
            'viewCount': 111208,
        }
    
    def test_valid_user_kwargs(self):
        serializer = SnscrapeTwitterUserSerializer(data=self.snscrape_user_kwargs)
        self.assertTrue(serializer.is_valid())
        
        
class SnscrapeTweetSerializerTest(TestCase):
    
    def setUp(self):
        self.user = TwitterUser.objects.create(
            twitter_id='123', 
            username='testuser',
            display_name='Test User', 
            description='Just a test',
            account_created_at=timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz), 
            location='Testville',
            followers_count=10
        )
        dummy_user = SNScrapeUser(id='123', username='testuser')
        self.tweet_data = {
            'id': '12345',
            'user': dummy_user,
            'rawContent': 'Test tweet content',
            'date': timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz),
            'inReplyToTweetId': '98765',
            'conversationId': '54321',
            'replyCount': 1,
            'retweetCount': 2,
            'likeCount': 3,
            'quoteCount': 4,
        }
    
    def test_snscrape_tweet_serializer(self):
        serializer = SnscrapeTweetSerializer(data=self.tweet_data)
        self.assertTrue(serializer.is_valid())
        tweet = serializer.save()
        
        self.assertEqual(tweet.twitter_id, '12345')
        self.assertEqual(tweet.content, 'Test tweet content')
        self.assertEqual(tweet.published_at, timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz))
        self.assertEqual(tweet.in_reply_to_id, '98765')
        self.assertEqual(tweet.conversation_id, '54321')
        self.assertEqual(tweet.reply_count, 1)
        self.assertEqual(tweet.retweet_count, 2)
        self.assertEqual(tweet.like_count, 3)
        self.assertEqual(tweet.quote_count, 4)
