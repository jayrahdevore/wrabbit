### wrabbit
# Wrap pydantic types into RabbitMQ queues
---

## Design 




## Example type definition
To define a common type, simply create a `wrabbit.BaseModel` as you would with pydantic:
```
from wrabbit import BaseModel

class Name(BaseModel):
    first: str
    last: str
```
Now we can import this type and send/recieve it with pika!

## Example consumer
With this type defined, we can now set up a consumer by wrapping the callback function and listening to the channel
```
from wrabbit import Consumer

consumer = Consumer('localhost')

@consumer.run_on_recieve() # here we wrap our callback function
def say_name(name: Name):
    ''' this function run when ever the type 'name' is recieved from the queue '''
    print(f"Hello!  My name is {name.first} {name.last}")

# start listening...
consumer.run()
```

## Example producer
Producers are nice and simple:

```
from wrabbit import Producer

producer = Producer('localhost')

# instantiate the type and send though to the queue
producer(Name(first="John", last="Doe"))

```


## Why this package?
**wrabbit** bakes both the producer and consumer configuration into the type and abstracts pika into basic producer/consumer types

## Looking for something else?
- [pika-pydantic](https://github.com/ttamg/pika-pydantic) 
- [pikantic](https://github.com/tomgrin10/pikantic)
