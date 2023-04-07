from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from rest_framework.serializers import ValidationError
import snscrape.modules.twitter as sntwitter
import traceback

from .serializers import SnscrapeTweetSerializer

logger = get_task_logger(__name__)


@shared_task
def scrape_single_tweet(tweet_id):
    mode = sntwitter.TwitterTweetScraperMode.SINGLE
    tweet_scrapper = sntwitter.TwitterTweetScraper(tweet_id, mode=mode).get_items()
    tweet = next(tweet_scrapper)
    return tweet


@shared_task
def scrape_tweets(req_id):
    from .models import ScrappingRequest

    started_at = timezone.now()
    req = ScrappingRequest.objects.get(id=req_id)
    req.start()

    username = req.username
    since = req.since.strftime("%Y-%m-%dT%H:%M:%SZ")
    until = req.until.strftime("%Y-%m-%dT%H:%M:%SZ")
    logger.info(
        f"Iniciando scrape_tweets(username={username}, since={since}, until={until}, recurse={req.recurse})"
    )

    started_scrapping_at = timezone.now()
    query = f"from:{username} since:{since} until:{until}"
    user_scrapping_results = sntwitter.TwitterSearchScraper(query).get_items()
    tweet_ids = []
    logger.info(f'Contando tweets do usuário "{username}"')
    for tweet in user_scrapping_results:
        tweet_ids.append(tweet.id)
    logger.info(f"Encontrados {len(tweet_ids)} tweets")

    logger.info(f'Raspando tweets do usuário "{username}" e suas respostas')
    tweets_and_replies = []
    if req.recurse:
        mode = sntwitter.TwitterTweetScraperMode.RECURSE
    else:
        mode = sntwitter.TwitterTweetScraperMode.SCROLL
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
            logger.error(f"Exceção ao raspar tweet {tweet_id}: {e}:\n{tb}")
    logger.info(f"Encontrados {len(tweets_and_replies)} tweets")

    started_saving_at = timezone.now()
    logger.info(f"Iniciando gravacao de {len(tweets_and_replies)} tweets")
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
            logger.error(f"Erro de validação ao salvar tweet {tweet_data}: {e}")

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exceção ao salvar tweet {tweet_data}: {e}:\n{tb}")

    req.finish()
    finished_at = timezone.now()
    logger.info(
        f"Finalizando scrape_tweets(username={username}, since={since}, until={until}, recurse={req.recurse}):"
        + f"{len(created_tweets)} tweets criados, {len(updated_tweets)} tweets atualizados"
    )
    logger.info(
        f"Tempo total={finished_at - started_at}; Tempo de scrapping={started_saving_at - started_scrapping_at}; Tempo de gravação={finished_at - started_saving_at}"
    )


def save_scrapped_tweet(tweet_data, req_id):
    tweet_data.scrapping_request = req_id
    tweet_serializer = SnscrapeTweetSerializer(data=tweet_data)
    if tweet_serializer.is_valid():
        tweet, created = tweet_serializer.save()
        return tweet, created
    else:
        raise ValidationError(tweet_serializer.errors)


@shared_task
def create_scrapping_requests(usernames, periods):
    from .models import ScrappingRequest

    created_requests = []
    for period in periods:
        since = timezone.make_aware(datetime.strptime(period["since"], "%Y-%m-%d"))
        until = timezone.make_aware(datetime.strptime(period["until"], "%Y-%m-%d"))

        for username in usernames:
            if not ScrappingRequest.objects.filter(
                username=username, since=since, until=until
            ).exists():
                req = ScrappingRequest.objects.create(
                    username=username, since=since, until=until
                )
                req.save()
                created_requests.append(req)
                logger.info(
                    f"Criando ScrappingRequest(username={username}, since={period['since']}, until={period['until']})"
                )

    logger.info(f"Criados {len(created_requests)} ScrappingRequest's")
    return created_requests


@shared_task
def start_next_scrapping_request():
    from .models import ScrappingRequest

    running_requests_count = ScrappingRequest.objects.filter(status="started").count()
    if running_requests_count >= settings.MAX_SCRAPPINGS:
        return

    requests = list(ScrappingRequest.objects.filter(status="created"))
    while requests and running_requests_count < settings.MAX_SCRAPPINGS:
        req = requests.pop(0)
        req.create_scrapping_task()
        logger.info(
            f"Iniciando ScrappingRequest(username={req.username}, since={req.since}, until={req.until})"
        )
        running_requests_count += 1
