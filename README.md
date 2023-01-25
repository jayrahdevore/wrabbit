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
import pika

connection_parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_parameters)
channel = connection.channel()

@Name.run_on_recieve(channel) # here we wrap our callback function
def say_name(name: Name):
    ''' this function run when ever the type 'name' is recieved from the queue '''
    print(f"Hello!  My name is {name.first} {name.last}")

# start listening...
channel.start_consuming()
```

## Example producer
Producers are nice and simple: simply create a channel and send the type through the pipeline

```
import pika

connection_parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_parameters)
channel = connection.channel()

# instantiate the type and send though to the queue
Name(first="John", last="Doe").send(channel)

```


## Limitations/Design considerations
- Currently, **wrabbit** is designed around the assumption that each model will have one consumer (many-to-one producer-consumer design).
Custom queue labels can be used, but by design this module attempts to abstract the need to handle queue names

## Why this package?
**wrabbit** bakes both the producer and consumer configuration into the type.

## Looking for something else?
- [pika-pydantic](https://github.com/ttamg/pika-pydantic) 
- [pikantic](https://github.com/tomgrin10/pikantic)
