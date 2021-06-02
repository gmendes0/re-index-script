import re
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

def main():
    load_dotenv()

    try:
        es = Elasticsearch(
            [os.environ.get('ELASTICSEARCH_HOST', '')],
            http_auth=(os.environ.get('ELASTICSEARCH_USER', ''),
                       os.environ.get('ELASTICSEARCH_SECRET', ''))
        )
    except Exception as e:
        print('\033[31m{}\033[m'.format('Erro ao conectar'))
        raise e

    try:
        vehicles = es.search(index=os.environ.get('ELASTICSEARCH_INDEX', ''), body={
                             'query': {'match_all': {}}, 'from': 0, 'size': 10_000})
    except Exception as e:
        print('\033[31m{}\033[m'.format('Erro ao buscar'))
        raise e

    command = '!#/bin/bash'

    for hit in vehicles['hits']['hits']:
        vehicle = hit['_source']
        user = vehicle['user_id']
        slug = vehicle['slug']

        try:
            unit = re.sub(
                '^-', '', re.search(r'-[A-z]{1,}$', vehicle['slug']).group()
            )
        except Exception as e:
            print('\033[31m{}\033[m'.format('Erro ao pegar a unidade'))
            raise e

        try:
            payload = {
                'identity': str(user),
                'exp': datetime.utcnow() + timedelta(seconds=int(os.environ.get('JWT_EXPIRATION_IN_SECONDS', '300')))
            }

            token = jwt.encode(payload, os.environ.get('JWT_SECRET', ''), algorithm='HS256')
        except Exception as e:
            print('\033[31m{}\033[m'.format('Falha ao gerar o token'))
            raise e

        try:
            command = '{}\n{}'.format(
                command, 'curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer {}" -H "X-Unity: {}" {}users/{}/vehicles/{}/index'.format(
                    token, unit, os.environ.get('VEHICLES_API_URL', ''), user, slug
                )
            )
        except Exception as e:
            print('\033[31m{}\033[m'.format('Falha ao gerar o comando'))
            raise e

    try:
        with open('out/reindex.sh', 'w') as file:
            file.write(command)
    except Exception as e:
        print('\033[31m{}\033[m'.format('Falha ao salvar o arquivo'))
        raise e

    print('\033[32m{}\033[m'.format('Done.'))


if __name__ == '__main__':
    main()
