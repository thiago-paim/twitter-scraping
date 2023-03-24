import traceback
from celery import shared_task
from celery.utils.log import get_task_logger
from rest_framework.serializers import ValidationError
import snscrape.modules.twitter as sntwitter
from .serializers import SnscrapeTweetSerializer

logger = get_task_logger(__name__)


@shared_task
def scrape_single_tweet(tweet_id):
    mode = sntwitter.TwitterTweetScraperMode.SINGLE
    tweet_scrapper = sntwitter.TwitterTweetScraper(tweet_id, mode=mode).get_items()
    tweet = next(tweet_scrapper)
    return tweet


@shared_task
def scrape_tweets(req_id, recurse=False):
    from .models import ScrappingRequest
    req = ScrappingRequest.objects.get(id=req_id)
    req.start()
    
    username = req.username
    since = req.since.strftime('%Y-%m-%dT%H:%M:%SZ')
    until = req.until.strftime('%Y-%m-%dT%H:%M:%SZ')
    logger.info(
        f'Iniciando scrape_tweets(username={username}, since={since}, until={until}, recurse={recurse})'
    )

    if recurse:
        mode = sntwitter.TwitterTweetScraperMode.RECURSE
    else:
        mode = sntwitter.TwitterTweetScraperMode.SCROLL
    query = f'from:{username} since:{since} until:{until}'
    user_scrapping_results = sntwitter.TwitterSearchScraper(query).get_items()
    
    logger.info(f'Iterando tweets do usuário "{username}"')
    tweet_ids = []
    for tweet in user_scrapping_results:
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
            logger.error(f'Erro ao raspar tweet {tweet_id}: {e}:\n{tb}')            
    logger.info(f'Encontrados {len(tweets_and_replies)} tweets')

    logger.info(f'Iniciando gravacao de {len(tweets_and_replies)} tweets')
    created_tweets = []
    updated_tweets = []
    for tweet_data in tweets_and_replies:
        try:
            t, created = save_scrapped_tweet(tweet_data, req_id)
            if created:
                created_tweets.append(t)
            else:
                updated_tweets.append(t)
        
        except ValidationError as e:
            logger.error(f'Erro ao salvar tweet {tweet_data}: {e}')
            
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f'Exceção ao salvar tweet {tweet_data}: {e}:\n{tb}')
        
    logger.info(
        f'Finalizando scrape_tweets(username={username}, since={since}, until={until}, recurse={recurse}):' + 
        f'{len(created_tweets)} tweets criados, {len(updated_tweets)} tweets atualizados'
    )
    req.finish()
   

def save_scrapped_tweet(tweet_data, req_id):
    tweet_data.scrapping_request = req_id
    tweet_serializer = SnscrapeTweetSerializer(data=tweet_data)
    if tweet_serializer.is_valid():
        tweet, created = tweet_serializer.save()
        return tweet, created
    else:
        raise ValidationError(tweet_serializer.errors)
