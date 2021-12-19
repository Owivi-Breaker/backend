from fastapi import APIRouter, Depends
from routers.api_v1 import game, player, club, league, game_pve, login, next_turn, user
from routers.api_test import test

import utils

api_router = APIRouter()
# router注册
api_router.include_router(
    game.router, prefix='/v1/game', tags=['game api'],
    dependencies=[Depends(utils.verify_token)])

api_router.include_router(
    player.router, prefix='/v1/player', tags=['player api'],
    dependencies=[Depends(utils.verify_token)])

api_router.include_router(
    club.router, prefix='/v1/club', tags=['club api'],
    dependencies=[Depends(utils.verify_token)])

api_router.include_router(
    user.router, prefix='/v1/user', tags=['user api'])

api_router.include_router(
    league.router, prefix='/v1/league', tags=['league api'],
    dependencies=[Depends(utils.verify_token)])

api_router.include_router(
    game_pve.router, prefix='/v1/game-pve', tags=['game pve api'],
    dependencies=[Depends(utils.verify_token)])

api_router.include_router(
    test.router, prefix='/v1/test', tags=['test api'])

api_router.include_router(
    login.router, prefix='/v1/login', tags=['login api'])

api_router.include_router(
    next_turn.router, prefix='/v1/next-turn', tags=['next turn api'],
    dependencies=[Depends(utils.verify_token)])
