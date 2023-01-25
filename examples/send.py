'''

send.py | example producer

'''

from wrabbit import Producer

from example_types import MyModel

sender = Producer('localhost')

sender.send(MyModel(name="Jones"))
