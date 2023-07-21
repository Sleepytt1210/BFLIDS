import os
from dotenv import load_dotenv

load_dotenv('../../.env')

WORK_ENV = os.environ.get('WORK_ENV', 'TEST')
S_HOST = os.environ['FL_S_HOST']
S_PORT = os.environ['FL_S_PORT']
S_ADDR = f'{S_HOST}:{S_PORT}'

NUM_CLIENTS = int(os.environ['NUM_CLIENTS'])
NUM_ROUNDS = int(os.environ.get('NUM_ROUNDS', 1))
EXPRESS_PORT = os.environ['EXPRESS_PORT']

CID = os.environ.get('CLIENT_ID', 1)

IPFS_SWARM_TARGET = os.environ['IPFS_SWARM_TARGET']