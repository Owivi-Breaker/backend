from fastapi import APIRouter
from routers.api_v1 import games, players, clubs, leagues, game_pve
from routers.api_test import test

api_router = APIRouter()
# router注册
api_router.include_router(games.router, prefix='/v1/games', tags=['game api'])
api_router.include_router(players.router, prefix='/v1/players', tags=['player api'])
api_router.include_router(clubs.router, prefix='/v1/clubs', tags=['club api'])
api_router.include_router(leagues.router, prefix='/v1/leagues', tags=['league api'])
api_router.include_router(game_pve.router, prefix='/v1/game-pve', tags=['game pve api'])

api_router.include_router(test.router, prefix='/test', tags=['test api'])
