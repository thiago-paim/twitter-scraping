from dataclasses import fields
from datetime import datetime
import pandas as pd
import snscrape.modules.twitter as sntwitter
from tqdm import tqdm
from tweets.models import Tweet, TwitterUser

"""Exemplo de execução pelo django shell
from tweets.scripts import scrape_tweets
username = 'ErikakHilton'
since = '2022-11-03'
until = '2022-11-04'
scrape_tweets(username, since, until, recurse=True)
"""

def scrape_tweets(username, since, until, recurse=False):
    if recurse:
        # Está disparando um erro no sntwitter, necessário investigar
        mode = sntwitter.TwitterTweetScraperMode.RECURSE
    else:
        mode = sntwitter.TwitterTweetScraperMode.SCROLL
    query = f'from:{username} since:{since} until:{until}'
    user_scrapping_results = sntwitter.TwitterSearchScraper(query)

    print('Lendo tweets do usuário')
    tweet_ids = []
    for tweet in tqdm(user_scrapping_results.get_items()):
        tweet_ids.append(tweet.id)
    print(len(tweet_ids))

    print('Buscando tweets originais e respostas')
    tweets_and_replies = []
    for tweet_id in tqdm(tweet_ids):
        tweet_scrapper = sntwitter.TwitterTweetScraper(tweet_id, mode=mode)
        for tweet in tweet_scrapper.get_items():
            tweets_and_replies.append(tweet)
    print(len(tweets_and_replies))

    tweet_key_mapping = {
        'id': 'twitter_id',
        'rawContent': 'content',
        'date': 'published_at',
        'inReplyToTweetId': 'in_reply_to',
        'replyCount': 'reply_count',
        'retweetCount': 'retweet_count',
        'likeCount': 'like_count',
        'quoteCount': 'quote_count',
    }
    user_key_mapping = {
        'id': 'twitter_id',
        'username': 'username',
        'displayname': 'display_name',
        'rawDescription': 'description',
        'created': 'account_created_at',
        'location': 'location',
        'followersCount': 'followers_count',
    }

    print('Salvando tweets')
    new_tweets = []
    for tweet_data in tqdm(tweets_and_replies):
        user_kwargs = {model_key: getattr(tweet_data.user, user_key) for user_key, model_key in user_key_mapping.items()}
        try:
            u = TwitterUser.objects.get(twitter_id=user_kwargs['twitter_id'])
            # Não está atualizando o usuario caso alguma informação tenha mudado
        except TwitterUser.DoesNotExist:
            u = TwitterUser.objects.create(**user_kwargs)
        
        kwargs = {model_key: getattr(tweet_data, tweet_key) for tweet_key, model_key in tweet_key_mapping.items()}
        kwargs['user'] = u
        
        try:
            t = Tweet.objects.get(twitter_id=kwargs['twitter_id'])
        except Tweet.DoesNotExist:
            t = Tweet.objects.create(**kwargs)
            new_tweets.append(t)
        
    print(f'Adicionandos {len(new_tweets)} novos tweets')
