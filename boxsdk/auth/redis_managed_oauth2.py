# coding: utf-8
from typing import Any, Tuple, Optional
from uuid import uuid4

from redis import StrictRedis, Redis
from redis.lock import Lock

from .oauth2 import OAuth2


class RedisManagedOAuth2Mixin(OAuth2):
    """
    Box SDK OAuth2 subclass.
    Allows for storing auth tokens in redis.
    """
    def __init__(self, unique_id: str = uuid4(), redis_server: Redis = None, *args: Any, **kwargs: Any):
        """
        :param unique_id:
            An identifier for this auth object. Auth instances which wish to share tokens must use the same ID.
        :param redis_server:
            An instance of a Redis server, configured to talk to Redis.
        """
        # pylint:disable=keyword-arg-before-vararg
        self._unique_id = unique_id
        self._redis_server = redis_server or StrictRedis()
        refresh_lock = Lock(redis=self._redis_server, name=f'{self._unique_id}_lock')
        super().__init__(*args, refresh_lock=refresh_lock, **kwargs)
        if self._access_token is None:
            self._get_and_update_current_tokens()

    @property
    def unique_id(self) -> str:
        """
        Get the unique ID used by this auth instance. Other instances can share tokens with this instance
        if they share the ID with this instance.
        """
        return self._unique_id

    def _get_tokens(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Base class override.
        Gets the latest tokens from redis before returning them.
        """
        return self._redis_server.hvals(self._unique_id) or (None, None)

    def _store_tokens(self, access_token: str, refresh_token: str) -> None:
        """
        Base class override.
        Saves the refreshed tokens in redis.
        """
        super()._store_tokens(access_token, refresh_token)
        self._redis_server.hmset(self._unique_id, {'access': access_token, 'refresh': refresh_token})


class RedisManagedOAuth2(RedisManagedOAuth2Mixin):
    """
    OAuth2 subclass which uses Redis to manage tokens.
    """
