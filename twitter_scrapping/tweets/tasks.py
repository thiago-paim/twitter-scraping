import traceback
from celery import shared_task
from celery.utils.log import get_task_logger
import snscrape.modules.twitter as sntwitter
from .models import Tweet, TwitterUser

logger = get_task_logger(__name__)

"""
from tweets.tasks import test_log
test_log.delay('test_log task')
"""
@shared_task
def test_log(msg):
    logger.info(msg)
    try:
        raise Exception('forced exception 1')
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f'Exception({e}):\n{tb}')
    raise Exception('forced exception 2')
    return msg


"""Exemplo de execução pelo django shell
from tweets.tasks import scrape_tweets
username = 'carteiroreaca'
since = '2023-03-01'
until = '2023-03-15'
scrape_tweets.delay(username, since, until)
"""
@shared_task
def scrape_tweets(username, since, until, recurse=False):
    logger.info(f'Iniciando scrape_tweets(username={username}, since={since}, until={until}, recurse={recurse})')
    if recurse:
        # Está disparando um erro no sntwitter, necessário investigar
        mode = sntwitter.TwitterTweetScraperMode.RECURSE
    else:
        mode = sntwitter.TwitterTweetScraperMode.SCROLL
    query = f'from:{username} since:{since} until:{until}'
    user_scrapping_results = sntwitter.TwitterSearchScraper(query)

    logger.info(f'Lendo tweets do usuário {username}')
    tweet_ids = []
    for tweet in user_scrapping_results.get_items():
        tweet_ids.append(tweet.id)
    logger.info(f'Encontrados {len(tweet_ids)} tweets')

    logger.info('Raspando tweets originais e respostas')
    tweets_and_replies = []
    for tweet_id in tweet_ids:
        tweet_scrapper = sntwitter.TwitterTweetScraper(tweet_id, mode=mode)
        for tweet in tweet_scrapper.get_items():
            tweets_and_replies.append(tweet)
    logger.info(f'Encontrados {len(tweets_and_replies)} tweets')

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

    logger.info(f'Iniciando gravacao de {len(tweets_and_replies)} tweets')
    new_tweets = []
    for tweet_data in tweets_and_replies:
        try:
            user_kwargs = {
                model_key: getattr(tweet_data.user, user_key) for user_key, model_key in user_key_mapping.items()
            }
            u = TwitterUser.objects.get(twitter_id=user_kwargs['twitter_id'])
            # Não está atualizando o usuario caso alguma informação tenha mudado
        except TwitterUser.DoesNotExist:
            u = TwitterUser.objects.create(**user_kwargs)
        except AttributeError as e:
            # To Do: Investigar esse erro
            # Em alguns casos ocorre um erro de que um objeto ´Tombstone´ não possui ´user´
            continue
        
        kwargs = {model_key: getattr(tweet_data, tweet_key) for tweet_key, model_key in tweet_key_mapping.items()}
        kwargs['user'] = u
        
        try:
            t = Tweet.objects.get(twitter_id=kwargs['twitter_id'])
        except Tweet.DoesNotExist:
            t = Tweet.objects.create(**kwargs)
            new_tweets.append(t)
        
    logger.info(f'Finalizando tarefa scrape_tweets(username={username}, since={since}, until={until}, recurse={recurse}): {len(new_tweets)} novos tweets salvos')
