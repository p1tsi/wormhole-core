from pymongo import MongoClient

from .base import BaseConnector


class Mongodb(BaseConnector):

    # TODO: create buffers of messages by plugin and load them when reached max capacity
    #  (instead of insert 1 doc each request)

    def __init__(self):
        super(Mongodb, self).__init__()
        self.mongo_client = MongoClient('127.0.0.1', 27017)
        print(self.mongo_client)
        self.db = self.mongo_client.test_db
        print(self.db)
        print(self.db.list_collection_names())
        try:
            self.db.create_collection('network')
            self.db.create_collection('xpc')
            self.db.create_collection('io')
            self.db.create_collection('sqlite')
            self.db.create_collection('notifications')
            print(self.db.list_collection_names())
        except:
            pass

    def forward(self, message, **kwargs):
        try:
            document = message.to_dict()
            # document.update(kwargs)
            # del document['plugin']
            self.db[kwargs.get('plugin')].insert_one(document)
        except Exception as e:
            print(e)
