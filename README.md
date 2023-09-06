# twitter-scraping

Projeto para realizar scraping de tweets abertos, com filtros por usuário e data.

**Atenção**: Com as mudanças recentes feitas no Twitter, o scraping não está mais funcionando.
Mais detalhes em: https://github.com/JustAnotherArchivist/snscrape/issues/996

# Setup

Primeiro crie um arquivo `.env` na mesma pasta e com o mesmo conteúdo do arquivo `.env.sample`.

A aplicação pode ser rodada localmente através do Docker, ou iniciando os processos manualmente

## Rodando com Docker

Primeiro certifique-se de estar com o [Docker](https://docs.docker.com/engine/) instalado e rodando. Caso esteja usando Windows, você pode usar o [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/).

Crie as imagens necessárias para a aplicação com o comando:

```bash
docker compose build
```

Depois inicie aplicação com:

```bash
docker compose up -d
```

ou então, se quiser acompanhar as saídas da aplicação, use:

```bash
docker compose up
```

Por fim, você precisa criar um usuario local.
Rode os comandos abaixo para acessar a pasta do Django e iniciar a criação do usuario

```bash
docker exec -it twitter-scraping-django-1 python3 manage.py createsuperuser
```

Preencha os dados do usuario, e então digite `exit` para voltar a pasta do projeto

Acesse o admin em `http://localhost:8000/admin/` para se certificar que a aplicação está funcionando

Quando quiser encerrar a aplicação use:
```bash
docker compose down
```

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
```bash
python manage.py shell
```

### Iniciando uma task de scraping manualmente

Precisamos criar um objeto `ScrapingRequest` com os parâmetros do scraping, e então chamar o método para iniciar a task

```python
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

```python
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
```python
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
```python
from tweets.models import Tweet, TwitterUser
from tweets.utils import export

user = TwitterUser.objects.last()
tweets = Tweet.objects.filter(user=user)
export(tweets)
```

### Criando scraping requests para um conjunto de usuarios e periodos 
```python
from tweets.values import TOTAL_SP_STATE_DEP, SCRAPING_PERIODS
from tweets.tasks import create_scraping_requests

create_scraping_requests(TOTAL_SP_STATE_DEP, SCRAPING_PERIODS)
```

### Testando aplicação

```bash
docker exec -it twitter-scraping-django-1 python manage.py test tweets/tests/
```


# Melhorias futuras

- Tasks rodando em um worker que foi encerrado ficam para sempre como STARTED no Flower
- Configurar logs rotativos para o Celery
- Configurar logs para o Flower
- Testar pipelines de scraping no Prefect pra visualizar melhor as etapas
