from django.test import TestCase
from django.utils import timezone
from snscrape.modules.twitter import User as SNUser, Tweet as SNTweet

from .fixtures import tweet1
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
            'user': self.snscrape_user_kwargs,
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
    
    def test_valid_kwargs(self):
        serializer = SnscrapeTweetSerializer(data=self.snscrape_tweet_kwargs)
        serializer.is_valid()
        print(serializer.errors)
        self.assertTrue(serializer.is_valid())
        
        
class SnscrapeTweetSerializerTest(TestCase):
    
    def setUp(self):
        self.tweet = tweet1
        
    def test_valid_kwargs(self):
        serializer = SnscrapeTweetSerializer(data=self.tweet)
        self.assertTrue(serializer.is_valid())
        tweet = serializer.save()

        self.assertEqual(tweet.twitter_id, '1636295637187584000')
        self.assertEqual(tweet.content, 'Test tweet content')
        self.assertEqual(tweet.published_at, timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz))
        self.assertEqual(tweet.in_reply_to_id, '98765')
        self.assertEqual(tweet.conversation_id, '54321')
        self.assertEqual(tweet.reply_count, 1)
        self.assertEqual(tweet.retweet_count, 2)
        self.assertEqual(tweet.like_count, 3)
        self.assertEqual(tweet.quote_count, 4)
    
    # def test_snscrape_tweet_serializer(self):
    #     serializer = SnscrapeTweetSerializer(data=self.tweet_data)
    #     self.assertTrue(serializer.is_valid())
    #     tweet = serializer.save()
        
    #     self.assertEqual(tweet.twitter_id, '12345')
    #     self.assertEqual(tweet.content, 'Test tweet content')
    #     self.assertEqual(tweet.published_at, timezone.datetime(2022, 1, 1, 12, 0, 0, 0, tz))
    #     self.assertEqual(tweet.in_reply_to_id, '98765')
    #     self.assertEqual(tweet.conversation_id, '54321')
    #     self.assertEqual(tweet.reply_count, 1)
    #     self.assertEqual(tweet.retweet_count, 2)
    #     self.assertEqual(tweet.like_count, 3)
    #     self.assertEqual(tweet.quote_count, 4)






    #     tweet = SNTweet(
    #         url='https://twitter.com/GergelyOrosz/status/1636295637187584000',
    #         date=timezone.datetime(2023, 3, 16, 9, 17, 35, tzinfo=tz),
    #         rawContent='When I talked w ~70 companies about what vendor costs they are reducing, the two most frequently mentioned was AWS/GCP and Datadog. Simply because they were usually by far the biggest spend.\n\nGiven DDG is usage based, reducing it is usually easier.\n\nMore:  https://t.co/NxOVEcYCds',
    #         renderedContent='When I talked w ~70 companies about what vendor costs they are reducing, the two most frequently mentioned was AWS/GCP and Datadog. Simply because they were usually by far the biggest spend.\n\nGiven DDG is usage based, reducing it is usually easier.\n\nMore:  newsletter.pragmaticengineer.com/p/vendor-spend…',
    #         id=1636295637187584000,
    #         user=User(
    #             username='GergelyOrosz',
    #             id=30192824,
    #             displayname='Gergely Orosz',
    #             rawDescription='Writing @Pragmatic_Eng & @EngGuidebook. Advisor @mobile__dev. Uber & Skype alumni. Great tech jobs: https://t.co/MJ0eAtlaS1. Contact: https://t.co/POWftUprCb',
    #             renderedDescription='Writing @Pragmatic_Eng & @EngGuidebook. Advisor @mobile__dev. Uber & Skype alumni. Great tech jobs: pragmaticurl.com/talent. Contact: pragmaticurl.com/contact',
    #             descriptionLinks=[
    #                 TextLink(
    #                     text='pragmaticurl.com/talent',
    #                     url='http://pragmaticurl.com/talent',
    #                     tcourl='https://t.co/MJ0eAtlaS1',
    #                     indices=(100, 123)
    #                 ),
    #                 TextLink(
    #                     text='pragmaticurl.com/contact',
    #                     url='http://pragmaticurl.com/contact',
    #                     tcourl='https://t.co/POWftUprCb',
    #                     indices=(134, 157))
    #             ],
    #             verified=False,
    #             created=timezone.datetime(2009, 4, 10, 10, 1, 11, tzinfo=tz),
    #             followersCount=202171,
    #             friendsCount=1368,
    #             statusesCount=24961,
    #             favouritesCount=32295,
    #             listedCount=2268,
    #             mediaCount=2511,
    #             location='Amsterdam, The Netherlands',
    #             protected=False,
    #             link=TextLink(
    #                 text='pragmaticengineer.com',
    #                 url='https://pragmaticengineer.com/',
    #                 tcourl='https://t.co/x8RulFU4ID',
    #                 indices=(0, 23)
    #             ),
    #             profileImageUrl='https://pbs.twimg.com/profile_images/673095429748350976/ei5eeouV_normal.png',
    #             profileBannerUrl='https://pbs.twimg.com/profile_banners/30192824/1619604364',
    #             label=None
    #         ),
    #         replyCount=22,
    #         retweetCount=13,
    #         likeCount=235,
    #         quoteCount=2,
    #         conversationId=1636295637187584000,
    #         lang='en',
    #         source=None,
    #         sourceUrl=None,
    #         sourceLabel=None,
    #         links=[
    #             TextLink(
    #                 text='newsletter.pragmaticengineer.com/p/vendor-spend…',
    #                 url='https://newsletter.pragmaticengineer.com/p/vendor-spend-cuts',
    #                 tcourl='https://t.co/NxOVEcYCds',
    #                 indices=(257, 280)
    #             )
    #         ],
    #         media=None,
    #         retweetedTweet=None,
    #         quotedTweet=Tweet(
    #             url='https://twitter.com/jamesacowling/status/1636168208377077760',
    #             date=timezone.datetime(2023, 3, 16, 0, 51, 14, tzinfo=tz),
    #             rawContent='Real monthly bills at an early-stage startup:\n\n@datadoghq: $11,386\n@getsentry: $134',
    #             renderedContent='Real monthly bills at an early-stage startup:\n\n@datadoghq: $11,386\n@getsentry: $134',
    #             id=1636168208377077760,
    #             user=User(
    #                 username='jamesacowling',
    #                 id=738506197158895616,
    #                 displayname='James Cowling',
    #                 rawDescription='@convex_dev co-founder. Infrastructure person. Reformed academic. Maker of things. Karaoke enthusiast.',
    # renderedDescription='@convex_dev co-founder. Infrastructure person. Reformed academic. Maker of things. Karaoke enthusiast.',
    # descriptionLinks=None,
    # verified=False,
    # created=timezone.datetime(2016, 6, 2, 23, 2, 53, tzinfo=tz),
    # followersCount=805,
    # friendsCount=165,
    # statusesCount=187,
    # favouritesCount=267,
    # listedCount=19,
    # mediaCount=8,
    # location='San Francisco,CA',
    # protected=False,
    # link=TextLink(text='convex.dev',
    # url='http://convex.dev',
    # tcourl='https://t.co/HAhmzsryzZ',
    # indices=(0,
    # 23)),
    # profileImageUrl='https://pbs.twimg.com/profile_images/1550543886610640896/3JztoI2B_normal.jpg',
    # profileBannerUrl='https://pbs.twimg.com/profile_banners/738506197158895616/1661050219',
    # label=None),
    # replyCount=57,
    # retweetCount=42,
    # likeCount=703,
    # quoteCount=22,
    # conversationId=1636168208377077760,
    # lang='en',
    # source=None,
    # sourceUrl=None,
    # sourceLabel=None,
    # links=None,
    # media=None,
    # retweetedTweet=None,
    # quotedTweet=None,
    # inReplyToTweetId=None,
    # inReplyToUser=None,
    # mentionedUsers=[User(username='datadoghq',
    # id=123093566,
    # displayname='Datadog,
    # Inc.',
    # rawDescription=None,
    # renderedDescription=None,
    # descriptionLinks=None,
    # verified=None,
    # created=None,
    # followersCount=None,
    # friendsCount=None,
    # statusesCount=None,
    # favouritesCount=None,
    # listedCount=None,
    # mediaCount=None,
    # location=None,
    # protected=None,
    # link=None,
    # profileImageUrl=None,
    # profileBannerUrl=None,
    # label=None),
    # User(username='getsentry',
    # id=464217126,
    # displayname='Sentry',
    # rawDescription=None,
    # renderedDescription=None,
    # descriptionLinks=None,
    # verified=None,
    # created=None,
    # followersCount=None,
    # friendsCount=None,
    # statusesCount=None,
    # favouritesCount=None,
    # listedCount=None,
    # mediaCount=None,
    # location=None,
    # protected=None,
    # link=None,
    # profileImageUrl=None,
    # profileBannerUrl=None,
    # label=None)],
    # coordinates=None,
    # place=None,
    # hashtags=None,
    # cashtags=None,
    # card=None,
    # viewCount=446377,
    # vibe=None),
    # inReplyToTweetId=None,
    # inReplyToUser=None,
    # mentionedUsers=None,
    # coordinates=None,
    # place=None,
    # hashtags=None,
    # cashtags=None,
    # card=SummaryCard(title='Are Tech Companies Aggressively Cutting Back on Vendor Spend?',
    # url='https://newsletter.pragmaticengineer.com/p/vendor-spend-cuts',
    # description='A deep dive into why vendor cuts are happening,
    # which areas are most impacted,
    # and actionable advice on how to save costs. With data points from more than 70 companies.',
    # thumbnailUrl='https://pbs.twimg.com/card_img/1635716365712777217/N5WilS7O?format=jpg&name=orig',
    # siteUser=None,
    # creatorUser=None),
    # viewCount=161280,
    # vibe=None)