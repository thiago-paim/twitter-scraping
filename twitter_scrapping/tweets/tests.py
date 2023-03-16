from django.test import TestCase
from django.utils import timezone

from .models import Tweet, TwitterUser
from .serializers import SnscrapeTwitterUserSerializer


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
        
        
class SerializerTests(TestCase):
    def setUp(self):
        self.snscrape_user_kwargs = {
            'username': 'GergelyOrosz',
            'id': 30192824,
            'displayname': 'Gergely Orosz',
            'rawDescription': 'Writing @Pragmatic_Eng & @EngGuidebook. Advisor @mobile__dev. Uber & Skype alumni. Great tech jobs: https://t.co/MJ0eAtlaS1. Contact: https://t.co/POWftUprCb',
            'renderedDescription': 'Writing @Pragmatic_Eng & @EngGuidebook. Advisor @mobile__dev. Uber & Skype alumni. Great tech jobs: pragmaticurl.com/talent. Contact: pragmaticurl.com/contact',
            'verified': False,
            'created': timezone.now(),
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
            'date': timezone.now(),
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