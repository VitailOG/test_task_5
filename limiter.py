import os

import redis

from dotenv import load_dotenv

from functools import wraps
from typing import NamedTuple

load_dotenv()


class ParseRateType(NamedTuple):
    num_requests: int
    seconds: int


class RateLimit:
    cache = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), db=0)
    cache_format = 'user_throttle_%(ident)s_%(endpoint)s'

    def __init__(self, rate_limit):
        self.num_requests, self.limit = self._parse_rate_limit(rate_limit)

    def __call__(self, function):
        @wraps(function)
        async def wrapped(*args, **kwargs):
            assert kwargs.get('request') is not None, "Set in argument for endpoint request"
            request = kwargs.get('request')
            if self.allow_request(request.client.host):
                return await function(*args, **kwargs)
            return {"error": True}
        return wrapped

    @staticmethod
    def _parse_rate_limit(rate_limit: str):
        period = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 216000
        }
        duration, rate = rate_limit.lower().split('/')
        return ParseRateType(num_requests=int(rate), seconds=period[duration] * int(rate))

    def allow_request(self, key) -> bool:
        curr_request = self.cache.get(key)

        if curr_request is None:
            self.cache.set(key, 0, self.limit)
            return self.throttle_success(key)

        self.cache.incr(key)

        if int(curr_request) < self.num_requests:
            return self.throttle_success(key)

        elif int(curr_request) == self.num_requests:
            self.cache.expire(key, 60)
        return False

    def throttle_success(self, key: str) -> bool:
        self.cache.incr(key)
        return True
