from celery import shared_task
from celery.utils.log import get_task_logger
from copy import deepcopy
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from rest_framework.serializers import ValidationError
from snscrape.modules.twitter import (
    TwitterTweetScraperMode,
    TwitterTweetScraper,
    TwitterSearchScraper,
    TwitterProfileScraper,
    User as SNUser,
    Tweet as SNTweet,
    Tombstone,
)
import traceback

from .serializers import SnscrapeTweetSerializer
from .utils import CustomTwitterProfileScraper, tweet_to_json

logger = get_task_logger(__name__)


@shared_task
def scrape_tweet(tweet_id, mode=TwitterTweetScraperMode.SINGLE):
    mode = mode
    tweet_scrapper = TwitterTweetScraper(tweet_id, mode=mode).get_items()
    tweet = next(tweet_scrapper)
    return tweet


def record_tweet(raw_tweet, req_id):
    # Consider moving this to SnscrapeTweetSerializer
    tweet = deepcopy(raw_tweet)
    tweet.raw_tweet_object = tweet_to_json(tweet)

    if tweet.quotedTweet:
        if type(tweet.quotedTweet) == SNTweet:
            qt_tweet, created = record_tweet(tweet.quotedTweet, req_id)
            tweet.quoted_id = qt_tweet.twitter_id
            tweet.quoted_tweet = qt_tweet.id

        if type(tweet.quotedTweet) == Tombstone:
            tweet.quoted_id = tweet.quotedTweet.id

    if tweet.retweetedTweet:
        if type(tweet.retweetedTweet) == SNTweet:
            rt_tweet, created = record_tweet(tweet.retweetedTweet, req_id)
            tweet.retweeted_id = rt_tweet.twitter_id
            tweet.retweeted_tweet = rt_tweet.id

        if type(tweet.retweetedTweet) == Tombstone:
            tweet.retweeted_id = tweet.retweetedTweet.id

    tweet.scrapping_request = req_id
    tweet_serializer = SnscrapeTweetSerializer(data=tweet)
    if tweet_serializer.is_valid():
        tweet, created = tweet_serializer.save()
        # To Do: Retornar também outros tweets que tenham sido criados (rt ou qt)
        return tweet, created
    else:
        raise ValidationError(tweet_serializer.errors)


@shared_task
def scrape_user_tweets(req_id):
    try:
        from .models import ScrappingRequest

        started_at = timezone.now()
        req = ScrappingRequest.objects.get(id=req_id)
        req.start()

        username = req.username
        logger.info(
            f"req_id={req_id}: Iniciando scrape_user_tweets com username={username}, since={req.since}, until={req.until})"
        )

        tweets = []
        created_tweets = []
        updated_tweets = []
        MIN_TWEETS = (
            5  # É comum que usuários tenham 1 ou 2 tweets fixados no topo do perfil
        )
        tweet_scrapper = CustomTwitterProfileScraper(username).get_items()

        # Loop manual necessário para que erros em tweets pontuais não travem o generator
        while True:
            try:
                tweet = next(tweet_scrapper)
                if tweet.date < req.since and len(tweets) > MIN_TWEETS:
                    logger.info(
                        f"req_id={req_id}: Limite de raspagem atingido em {tweet.date}"
                    )
                    break

                try:
                    tweets.append(tweet)
                    t, created = record_tweet(tweet, req_id)
                    if created:
                        created_tweets.append(t)
                    else:
                        updated_tweets.append(t)
                except ValidationError as e:
                    logger.error(
                        f"req_id={req_id}: Erro de validação ao salvar tweet {tweet}: {e}"
                    )
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(
                        f"req_id={req_id}: Exceção ao salvar tweet {tweet}: {e}:\n{tb}"
                    )

            except StopIteration:
                break
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(
                    f"req_id={req_id}: Exceção no tweet {tweet.id}: {e}:\n{tb}"
                )
                raise

        logger.info(f"req_id={req_id}: Encontrados {len(tweets)} tweets")

        req.finish()
        finished_at = timezone.now()
        logger.info(
            f"req_id={req_id}: Finalizando scrape_user_tweets(username={username}, since={req.since}, until={req.until}):"
            + f"{len(created_tweets)} tweets criados, {len(updated_tweets)} tweets atualizados"
        )
        logger.info(f"req_id={req_id}: Tempo total={finished_at - started_at}")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            f"req_id={req_id}: Exceção geral ao executar scrape_user_tweets: {e}:\n{tb}"
        )
        req.interrupt()


@shared_task
def scrape_last_tweet_from_user(username):
    tweet = next(CustomTwitterProfileScraper(username).get_items())
    return tweet


@shared_task
def scrape_tweets_and_replies(req_id):
    try:
        from .models import ScrappingRequest

        started_at = timezone.now()
        req = ScrappingRequest.objects.get(id=req_id)
        req.start()

        username = req.username
        since = req.since.strftime("%Y-%m-%dT%H:%M:%SZ")
        until = req.until.strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(
            f"Iniciando scrape_tweets_and_replies(username={username}, since={since}, until={until}, recurse={req.recurse})"
        )

        started_scrapping_at = timezone.now()
        query = f"from:{username} since:{since} until:{until}"
        user_scrapping_results = TwitterSearchScraper(query).get_items()
        tweet_ids = []
        logger.info(f'Contando tweets do usuário "{username}"')
        for tweet in user_scrapping_results:
            tweet_ids.append(tweet.id)
        logger.info(f"Encontrados {len(tweet_ids)} tweets")

        logger.info(f'Raspando tweets do usuário "{username}" e suas respostas')
        tweets_and_replies = []
        if req.recurse:
            mode = TwitterTweetScraperMode.RECURSE
        else:
            mode = TwitterTweetScraperMode.SCROLL
        for tweet_id in tweet_ids:
            tweet_scrapper = TwitterTweetScraper(tweet_id, mode=mode).get_items()
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
            f"Finalizando scrape_tweets_and_replies(username={username}, since={since}, until={until}, recurse={req.recurse}):"
            + f"{len(created_tweets)} tweets criados, {len(updated_tweets)} tweets atualizados"
        )
        logger.info(
            f"Tempo total={finished_at - started_at}; Tempo de scrapping={started_saving_at - started_scrapping_at}; Tempo de gravação={finished_at - started_saving_at}"
        )
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(
            f"Exceção ao executar scrape_tweets_and_replies(req_id={req_id}): {e}:\n{tb}"
        )
        req.interrupt()


def save_scrapped_tweet(tweet_data, req_id):
    tweet_data.scrapping_request = req_id
    tweet_serializer = SnscrapeTweetSerializer(data=tweet_data)
    if tweet_serializer.is_valid():
        tweet, created = tweet_serializer.save()
        return tweet, created
    else:
        raise ValidationError(tweet_serializer.errors)


@shared_task
def create_scrapping_requests(usernames, periods, include_replies=False):
    from .models import ScrappingRequest

    created_requests = []
    for period in periods:
        since = timezone.make_aware(datetime.strptime(period["since"], "%Y-%m-%d"))
        until = timezone.make_aware(datetime.strptime(period["until"], "%Y-%m-%d"))

        for username in usernames:
            if not ScrappingRequest.objects.filter(
                username=username,
                since=since,
                until=until,
                include_replies=include_replies,
            ).exists():
                req = ScrappingRequest.objects.create(
                    username=username, since=since, until=until
                )
                req.save()
                created_requests.append(req)
                logger.info(
                    f"Criando ScrappingRequest(username={username}, since={period['since']}, until={period['until']}, include_replies={include_replies})"
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
