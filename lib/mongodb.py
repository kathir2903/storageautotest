"""
Establish connection to MongoDB
"""

from pymongo.errors import AutoReconnect
from pymongo import MongoClient as connect
import pymongo
from bson.objectid import ObjectId
from ns.src.lib.common.utils import singleton_var
import json
import pdb
from threading import Lock
_conn_lock = Lock()
RECONNECT_DELAY = 10
asc = pymongo.ASCENDING # ASCENDING is 1
desc = pymongo.DESCENDING # DESCENDING is -1

#MONGODB_URI = 'mongodb://mongodb01.stg.local:27017/test'
@singleton_var('ref', None)
def Connection(dbhost, dbname, port=27017):
    #MONGODB_URI = 'mongodb://%s:%s/%s' %(dbhost, port, dbname)
    MONGODB_URI = 'mongodb://%s:%s' %(dbhost, port)
    print MONGODB_URI
    with _conn_lock:
        if Connection.ref:
            return Connection.ref
        
        while True:
            try:
                Connection.ref = connect(MONGODB_URI)
                break
            except AutoReconnect:
                time.sleep(RECONNECT_DELAY)
        return Connection.ref

def queryrunner(func):
    def wrapper(*args, **kwargs):
        try:
            post_res, req = func(*args, **kwargs)
            #return True if req in post_res else False
            return True if any ([req in [post_res], req == post_res]) else False
        except Exception as e:
            raise Exception(e.message)
    return wrapper

class dbutils(object):
    # https://docs.mongodb.org/manual/reference/operator/query/
    
    def __init__(self, db, dbname):
        self.dbname = db[dbname]
    
    @staticmethod 
    def close(db):
        return db.close()
    
    @staticmethod
    def dbnames(db):
        return db.databasenames()

    def collection_count(self):
        return len(self.dbname.collection_names())

    def collection_names(self, include_system_collections=False):
        self.collections = self.dbname.collection_names()
        return self.collections
    """ 
    def create_collection(self, colname):
        try:
            self.dbname.create_collection(colname)
            return True if colname in self.collection_names() else False
        except Exception as e:
            raise Exception(e.message)
    """
    @queryrunner
    def create_collection(self, colname):
        self.dbname.create_collection(colname)
        return self.collection_names(), colname
    
    def drop_collection(self, colname):
        self.dbname.drop_collection(colname)
    
    def remove_entries(self, col):
        self.dbname[col].remove()
        
    @queryrunner
    def insert_one(self, col, _filter):
        write = self.dbname[col].insert_one(_filter)
        read = self.find_one(col, {'_id' : ObjectId(write.inserted_id)})
        return str(write.inserted_id), str(read['_id'])

    @queryrunner    
    def insert_many(self, col, _filter):
        """
        more than one document
        [{'company': 'netskope', 'location': 'los altos'}]
        
        """
        write = self.dbname[col].insert_many([{k:v} for k, v in _filter.iteritems()])
        return len(write.inserted_ids), len(_filter)
        
    def replace_one(self, col, _filter, upsert=True):
        write = self.dbname[col].replace_one(_filter, upsert)
        read = self.find_one(col, {'_id' : ObjectId(write.modified_id)})
        return str(write.inserted_id), str(read['_id'])
    
    def delete_one(self, col, _filter):
        total = self.dbname[col].find(_filter).count()
        delete = self.dbname[col].delete_one(_filter)
        _minus_one = self.dbname[col].find(_filter).count()
        return total-1 == _minus_one

    @queryrunner
    def delete_many(self, col, _filter):
        total = self.dbname[col].find(_filter).count()
        delete = self.dbname[col].delete_many(_filter)
        return delete.deleted_count, total

    def update_one(self, col, 
                    _filter, 
                    update, 
                    upsert=True):
        """
        update a document matching given fileter
        usage: _filter should have query including filter
        and data to be updated
        ex: {'x': 1}, {'x':3}
        """
        write = self.dbname[col].update_one(_filter, update, upsert)
        return True if write.modified_count==1 else False
    
    @queryrunner
    def update_many(self, col, 
                    _filter,
                    update, 
                    upsert=True):
        total = self.dbname[col].find(_filter).count()
        write = self.dbname[col].update_many(_filter, update, upsert)
        return write.modified_count, total
        
    def find(self, col, _filter, sort=None):
        
        """
        example filters: _filter = {$and: 
                [{'appname': 'google'}, 
                {'instance': 'nammazone.com'}]}
        >>> slist = []
        >>> for i in sort:
        ...     slist.extend([(k, eval(v)) for k, v in i.iteritems()])
        """
        if sort:
            cursor = self.dbname[col].find(_filter).sort(slist)
        else:
            cursor = self.dbname[col].find(_filter)
        return [x for x in cursor]

    def data_count(self, col, _filter):
        return len(self.find(col, _filter))

    def find_one(self, col, _filter):
        """
        example filters: _filter = {$and: 
                [{'appname': 'google'}, 
                {'instance': 'nammazone.com'}]}
        """
        return self.dbname[col].find_one(_filter)
    
    def find_one_and_delete(self, col, _filter):
        total = self.dbname[col].count(_filter) #count
        self.dbname[col].find_one_and_delete(_filter)
        _minus_one = self.dbname[col].count(_filter)
        return total-_minus_one == 1
        
    def find_one_and_replace(self, col, _filter, update):
        res = self.dbname[col].find_one_and_replace(_filter, update)
        post_res = self.dbname[col].find_one({'_id': res['_id']})
        #pdb.set_trace()
        return 
    
    @staticmethod
    def set(db, obj, items):
        return db.update({'_id': obj['_id']}, {'$set': items}, safe=True)

    @staticmethod
    def append(db, obj, items):
        return db.update({'_id': obj['_id']}, {'$addToSet': items}, safe=True)

    @staticmethod
    def remove(db, obj, items):
        return db.update({'_id': obj['_id']}, {'$pullAll': items}, safe=True)
    
if __name__ == "__main__":
    pass
