# twitter-scrapping

Projeto para realizar scraping de tweets abertos, com filtros por usuário e data.

# Setup

Primeiro crie um arquivo `.env` na mesma pasta e com o mesmo conteúdo do arquivo `.env.sample`.

A aplicação pode ser rodada localmente através do Docker, ou iniciando os processos manualmente

## Rodando com Docker

Primeiro certifique-se de estar com o [Docker](https://docs.docker.com/engine/) instalado e rodando. Caso esteja usando Windows, você pode usar o [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/).

Crie as imagens necessárias para a aplicação com o comando:
```
docker compose build
```

Depois inicie aplicação com:
```
docker compose up -d
```
ou então, se quiser acompanhar as saídas da aplicação, use:
```
docker compose up
```

Por fim, você precisa criar um usuario local.
Rode os comandos abaixo para acessar a pasta do Django e iniciar a criação do usuario
```
docker exec -it django /bin/bash
python manage.py createsuperuser
```
Preencha os dados do usuario, e então digite `exit` para voltar a pasta do projeto


Quando quiser encerrar a aplicação use:
```
docker compose down
```

## Rodando manualmente
Caso não queira usar o Docker, você também pode rodar os componentes da aplicação manualmente. 
Os passos abaixo são específicos para Linux.

Primeiro vá para a pasta do `manage.py` e execute as migrações
```
cd twitter_scrapping/
python manage.py migrate
```

Inicie o Rabbit MQ pelo Docker
```
sudo service docker start
docker run -d -p 5672:5672 rabbitmq
```

Inicie o Worker Celery e o Flower
```
celery -A twitter_scrapping worker -l INFO -f celery.log
celery flower
```

Por fim inicie o Django
```
python manage.py runserver
```

Acesse o admin em `http://localhost:8000/admin/` para se certificar que a aplicação está funcionando

# Como usar

## Executando raspagens
- Acesse `http://localhost:8000/admin/` e clique em `Scraping Requests`, ou acesse diretamente pelo link `http://localhost:8000/admin/tweets/scrapingrequest/`
- Clique em `ADD SCRAPING REQUEST`, no canto superior direito
- Preencha somente os campos `Username`, `Since` e `Until`
    - Caso queira realizar uma raspagem recursiva, marque a opção `Recurse` (mas lembre-se que este modo é significativamente mais demorado)
- Clique em `SAVE` para criar a solicitação de raspagem, e então você será direcionado de volta para a listagem de Scraping Requests
- Na tela de listagem, selecione a raspagem que acabou de criar clicando no checkbox
- Clique em `Action` (acima da listagem), selecione a opção `Start scraping tasks`, e então clique em `Go`
- Com isso a raspagem será iniciada, e seu status mudará de `Created` para `Started`
- Quando ela terminar, seu status será atualizado para `Finished`

## Exportando tweets

Os tweets podem ser exportados de duas formas diferentes pelo admin: pela listagem de Tweets ou de Scraping Requests

### Exportando tweets pela listagem de Tweets
Você pode exportar um arquivo selecionando os tweets que deseja

- Vá para a listagem de Tweets (`http://localhost:8000/admin/tweets/tweet/`)
- Se quiser, aplique algum filtro de tweet na coluna da direita
- Selecione os tweets desejados
    - Para selecionar todos da página, clique no checkbox do header da tabela de tweets
    - Para selecionar todos da sua busca, clique no checkbox do header da tabela de tweets e então no texto `Select all {total} tweets`
- Clique em `Action` (acima da listagem), selecione a opção `Export selected tweets`, e então clique em `Go`
- O arquivo será salvo em `twitter_scraping/exports/`
    - O título do arquivo será formado pela data e hora da geração, seguidos do termo `tweets` e os filtros aplicados (caso haja algum)

**ATENÇÃO:** Caso tenha aplicado algum filtro, é fundamental clicar para selecionar todos os tweets antes de mandar exportar, caso contrário ele gerará um arquivo com os filtros no nome, mas sem os tweets

### Exportando tweets pela listagem de ScrapingRequests

Você também pode exportar tweets através da raspagem que os criou
- Vá para a listagem de Scraping Requests (`http://localhost:8000/admin/tweets/scrapingrequest/`)
- Selecione uma ou mais raspagens das quais deseja exportar os tweets
- Clique em `Action` (acima da listagem), selecione a opção `Export scraping results`, e então clique em `Go`
- O arquivo será salvo em `twitter_scraping/exports/`
    - O título do arquivo será formado pela data e hora da geração, seguidos do termo `scraping_requests` e os IDs das raspagens selecionadas

**ATENÇÃO:** Atualmente cada tweet só mantém a referência para raspagem mais recente que o encontrou. Isso significa que se uma raspagem mais recente encontrar um tweet já raspado, ele perderá a referencia para a sua raspagem inicial, e por isso não será mais incluído na exportação dela.


## Executando comandos pelo shell

Também é possível realizar operações direto pelo shell do Django, que pode ser iniciado com:
```
python manage.py shell
```

### Iniciando uma task de scraping manualmente

Precisamos criar um objeto `ScrapingRequest` com os parâmetros do scraping, e então chamar o método para iniciar a task
```
from tweets.models import ScrapingRequest
username = 'andreawerner_'
since = '2022-09-01'
until = '2022-09-02'
req = ScrapingRequest.objects.create(
    username=username, since=since, until=until
)
req.create_scraping_task()
```

Para raspar todas as respostas e conversas derivadas dos tweets, podemos usar `recurse=True`.
Porém este parâmetro pode aumentar significativamente o tempo de raspagem.
```
from tweets.models import ScrapingRequest
username = 'andreawerner_'
since = '2022-09-01'
until = '2022-09-02'
req = ScrapingRequest.objects.create(
    username=username, since=since, until=until, recurse=True
)
req.create_scraping_task()
```

### Raspar um único tweet e validar os dados
```
from tweets.serializers import SnscrapeTwitterUserSerializer, SnscrapeTweetSerializer
from tweets.tasks import scrape_tweet

tweet_id = '1636295637187584000'
tweet = scrape_tweet.delay(tweet_id)
user_serializer = SnscrapeTwitterUserSerializer(data=tweet.user.__dict__)
if not user_serializer.is_valid():
    print(user_serializer.errors)

tweet_kwargs = tweet.__dict__
tweet_kwargs['user_twitter_id'] = tweet.user.id
tweet_serializer = SnscrapeTweetSerializer(data=tweet_kwargs)
if not tweet_serializer.is_valid():
    print(tweet_serializer.errors)
```

### Exportar para CSV os tweets de um usuario
```
from tweets.models import Tweet, TwitterUser
from tweets.utils import export_csv

user = TwitterUser.objects.last()
tweets = Tweet.objects.filter(user=user)
export_csv(tweets)
```

### Criando scraping requests para um conjunto de usuarios e periodos 
```
from tweets.values import TOTAL_SP_STATE_DEP, SCRAPING_PERIODS
from tweets.tasks import create_scraping_requests

create_scraping_requests(TOTAL_SP_STATE_DEP, SCRAPING_PERIODS)
```

# Pendencias

- Scraping
    - Tweets que estavam quotando algum tweet falharam, e suas requests precisam ser refeitas
        - celery11.log
        - reqs_to_retry = [1407, 1408, 1410, 1424, 1427, 1446, 1447, 1448, 1449, 1450, 1452, 1454, 1455, 1457, 1464, 1466, 1468, 1471, 1478, 1485, 1492, 1493, 1499, 1500, 1506, 1522, 1523, 1525, 1552, 1558, 1560, 1570, 1576, 1589, 1597, 1630, 1644, 1655, 1659, 1660, 1662, 1663, 1666, 1667, 1668, 1669, 1670, 1671, 1672, 1673, 1674, 1676, 1680, 1681, 1683, 1684, 1685, 1686, 1687, 1690, 1691, 1693, 1694, 1695, 1697, 1699, 1701, 1715, 1716, 1718, 1719, 1733, 1737, 1743, 1744, 1748, 1749, 1756, 1770, 1776, 1793, 1796, 1805, 1808, 1813, 1815, 1824, 1825, 1826, 1827, 1828, 1829, 1841, 1843, 1848, 1854, 1857]
    - Chamar o TwitterTweetScraper em um tweet que gere erros, criar fixtures dos resultados e então escrever os testes
    - Revisar username dos Requests que falharam com 0 tweets criados
    - Checar execuções seguidas de scrape_tweet_replies com resultados diferentes. Exemplos:
        - {'tweet_id': '1578369571924639745', 'req_id': 8593}
            - {'created_tweets': 14, 'updated_tweets': 188}
            - {'created_tweets': 201, 'updated_tweets': 2}
        - {'tweet_id': '1580261253976842240', 'req_id': 8592}
            - {'created_tweets': 37, 'updated_tweets': 164}
            - {'created_tweets': 202, 'updated_tweets': 2}
        - {'tweet_id': '1581859962648952834', 'req_id': 8591}
            - {'created_tweets': 5, 'updated_tweets': 87}	
            - {'created_tweets': 6, 'updated_tweets': 82}
        - Mais casos listados nas tasks executadas no Flower

- Infra
    - Tasks rodando em um worker que foi encerrado ficam para sempre como STARTED no Flower
    - Configurar logs rotativos para o Celery
    - Configurar logs para o Flower
    - Testar pipelines de scraping no Prefect
        - Permite melhor visualização das etapas de scraping

- Performance
    - Colocar writes em transactions para evitar erros de locked database
        - https://stackoverflow.com/questions/54998/how-scalable-is-sqlite

- Usabilidade e Manutenção
    - Mudar campo ScrapingRequest.include_replies para category
    - Renomear tudo de "scrapping" para "scraping"