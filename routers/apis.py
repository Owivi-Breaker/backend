from fastapi import APIRouter
from routers.api_v1 import games, player, clubs, leagues, game_pve, login, next_turn
from routers.api_test import test

api_router = APIRouter()
# router注册
api_router.include_router(games.router, prefix='/v1/game', tags=['game api'])
api_router.include_router(player.router, prefix='/v1/player', tags=['player api'])
api_router.include_router(clubs.router, prefix='/v1/club', tags=['club api'])
api_router.include_router(leagues.router, prefix='/v1/league', tags=['league api'])
api_router.include_router(game_pve.router, prefix='/v1/game-pve', tags=['game pve api'])

api_router.include_router(test.router, prefix='/test', tags=['test api'])
api_router.include_router(login.router, prefix='/v1/login', tags=['login api'])
api_router.include_router(next_turn.router, prefix='/next-turn', tags=['next turn api'])
