from collections import namedtuple

Item = namedtuple('Item', ['id', 'title', 'genres', 'players', 'is_serie', 'poster_url'])
Episode = namedtuple('Episode', ['id', 'season', 'episode', 'url'])
Season = namedtuple('Seasons', ['serie_id', 'season_number', 'episodes'])
