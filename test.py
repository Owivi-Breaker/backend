from modules import next_turn_app
from core.db import get_session
import time

calendar_game = {
    'club_id': '1,2',
    'game_name': 'test',
    'game_type': 'test'
}

s = time.time()
next_turner = next_turn_app.NextTurner(db=get_session(), save_id=1)
for _ in range(50):
    next_turner.play_game(calendar_game=calendar_game)
e = time.time()
print('共耗时{}s'.format(e - s))
