"""
Establish and run queries on Redis
"""
import redis
from contextlib import contextmanager
import time
from ns.src.lib.common import utils
# http://redis.io/topics/data-types-intro

@contextmanager
def connect(host='redismpvip.stg.local',
            port=6379):
    try:
        conn = redis.Redis(host=host, port=port)
        yield conn
    except Exception as exc:
        raise exc
    finally:
        if conn:
            del conn

def retry(func):
    def wrap(*args, **kw):
        cnt = 3
        while cnt:
            cnt -= 1
            try:
                return func(*args, **kw)
            except (redis.ConnectionError, Exception) as exc:
                print "Connection failed, retrying last time" # replace with logger
                time.sleep(10)
        return wrap

class redisutils(object):
    """ redis queries """
    def set_keyvalue(self, conn, key, value):
        """ create a new {key:value} entry in redis """
        conn.set(key, value)
    
    def get_value(self, conn, key):
        """ return value of a given key """
        if self.exists(conn, key):
            return conn.get(key)
        else:
            raise Exception, "No key (%s) exists" %key

    def insert_value(self, key, value, score=None):
        """ insert value to existing list """
        if not score:
            conn.sadd(key, value)
            return
        #else:
            #assert type(score) == int
            #conn.zadd(key, value, score)

    def count(self, conn, key):
        """ get count of given key """
        return conn.llen(key)

    def insert_many(self, conn, key, **kwargs):
        """ insert many to the given list """
        conn.zadd(key, **kwargs)

    def retrieve(self, conn, key):
        """ retrieve from list """
        return conn.lpop(key)

    def delete(self, conn, key):
        """ delete the entry """
        return conn.delete(key)
    
    def exists(self, conn, key):
        """ check if the given key exists """
        return conn.exists(key)
        
if __name__ == "__main__":
    """ self test """
    rutils = redisutils()
    with connect(host='redismpvip.stg.local') as conn: 
        print "HI"
        rutils.set_keyvalue(conn, "NAME", "Kathir")
        print rutils.get_value(conn, "NAME")
        rutils.insert_value(conn, "ZNAME", "ZKathir")
        print rutils.delete(conn, "NAME")
