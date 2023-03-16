import traceback
from celery import shared_task
from celery.utils.log import get_task_logger
import snscrape.modules.twitter as sntwitter
from .models import Tweet, TwitterUser

logger = get_task_logger(__name__)


@shared_task
def scrape_tweets(username, since, until, recurse=False):
    logger.info(f'Iniciando scrape_tweets(username={username}, since={since}, until={until}, recurse={recurse})')
    if recurse:
        mode = sntwitter.TwitterTweetScraperMode.RECURSE
    else:
        mode = sntwitter.TwitterTweetScraperMode.SCROLL
    query = f'from:{username} since:{since} until:{until}'
    user_scrapping_results = sntwitter.TwitterSearchScraper(query)

    logger.info(f'Iterando tweets do usuário "{username}"')
    tweet_ids = []
    for tweet in user_scrapping_results.get_items():
        tweet_ids.append(tweet.id)
    logger.info(f'Encontrados {len(tweet_ids)} tweets')

    logger.info(f'Raspando tweets do usuário "{username}" e suas respostas')
    tweets_and_replies = []
    for tweet_id in tweet_ids:
        tweet_scrapper = sntwitter.TwitterTweetScraper(tweet_id, mode=mode).get_items()
        try:
            # Loop manual necessário para que erros em tweets pontuais não travem o generator
            while True:
                tweet = next(tweet_scrapper)
                tweets_and_replies.append(tweet)
        except StopIteration:
            continue
        except Exception as e:
            tb = traceback.format_exc()
            logger.debug(f'Erro ao raspar tweet {tweet_id}')
            logger.debug(f'Exception({e}):\n{tb}')
            continue
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
        logger.debug(f'Salvando {tweet_data}')
        try:
            user_kwargs = {
                model_key: getattr(tweet_data.user, user_key) for user_key, model_key in user_key_mapping.items()
            }
            try:
                # Usuário não é atualizado caso tenha alguma alteração
                u = TwitterUser.objects.get(twitter_id=user_kwargs['twitter_id'])
            except TwitterUser.DoesNotExist:
                u = TwitterUser.objects.create(**user_kwargs)
            
            tweet_kwargs = {model_key: getattr(tweet_data, tweet_key) for tweet_key, model_key in tweet_key_mapping.items()}
            tweet_kwargs['user'] = u
            try:
                # Tweet não é atualizado caso tenha alguma alteração
                tweet_id = tweet_kwargs['twitter_id']
                t = Tweet.objects.get(twitter_id=tweet_id)
                logger.debug(f'Tweet {tweet_id} já existe na base')
            except Tweet.DoesNotExist:
                t = Tweet.objects.create(**tweet_kwargs)
                logger.debug(f'Tweet {tweet_id} criado')
                new_tweets.append(t)
                
        except AttributeError as e:
            tb = traceback.format_exc()
            logger.debug(f'Erro ao salvar tweet {tweet_data}')
            logger.debug(f'Exception({e}):\n{tb}')
            continue

    logger.info(f'Finalizando scrape_tweets(username={username}, since={since}, until={until}, recurse={recurse}): {len(new_tweets)} novos tweets salvos')
