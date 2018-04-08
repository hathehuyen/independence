# from mongoengine import *
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.zenbot4

s_col = db.sessions
trades = db.trades

# trades = t_col.find()
# print(t_col.find_one({'selector': 'bitfinex.BTC-USD'}))

# connect('zenbot4')
#
#
# class Trades(DynamicDocument):
#     meta = {
#         'collection': 'trades'
#     }
#     trade_id = IntField()
#     time = FloatField()
#     size = FloatField()
#     price = FloatField()
#     side = StringField()
#     id = StringField()
#     selector = StringField()





