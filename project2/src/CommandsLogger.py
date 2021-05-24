import redis


class CommandsLogger:
    __KEY: str = 'commands_history'

    def __init__(self):
        self._rdb = redis.Redis(host='localhost', port=6379, db=1)

    def log_command(self, command: str):
        self._rdb.rpush(self.__KEY, command)
        self._rdb.ltrim(self.__KEY, -20, -1)

    def get_logs(self) -> list:
        return self._rdb.lrange(self.__KEY, 0, -1)
