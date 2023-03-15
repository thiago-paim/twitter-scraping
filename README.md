# twitter-scrapping


### Iniciando o Django

```
python manage.py runserver
```


### Iniciando um worker Celery local

```
celery -A twitter_scrapping worker -l INFO -f celery.log
```


### Iniciando uma task de scrapping

```
python manage.py shell
from tweets.tasks import scrape_tweets
username = 'ErikakHilton'
since = '2023-03-01'
until = '2023-03-15'
scrape_tweets.delay(username, since, until)
```