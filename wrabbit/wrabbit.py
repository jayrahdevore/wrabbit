"""

wrabbit.py | wrap pydantic BaseModel with RabbitMQ message queueing

"""

from typing import Callable
import inspect
import pydantic
import pika  # type: ignore


class BaseModel(pydantic.BaseModel):
    """extended pydantic.BaseModel class that adds queue metadata"""

    @classmethod
    def queue_name(cls):
        """string that identifies queue name for type"""
        return cls.__name__

    def send(
        self,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        routing_key_override: str | None = None, publish_kwargs: dict | None = None,):
        """send instance of model to queue

        Example:

        assert isinstance(YourModel, wrabbit.BaseModel)

        YourModel(**kwargs).send(channel)

        """
        if publish_kwargs is None:
            publish_kwargs = {}

        publish_kwargs = {"exchange": ""} | publish_kwargs

        routing_key = (
            routing_key_override if routing_key_override else self.queue_name()
        )

        channel.basic_publish(
            body=self.json(), routing_key=routing_key, **publish_kwargs
        )

    @classmethod
    def run_on_recieve(
        cls,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        routing_key_override=None,
        channel_queue_kwargs: dict | None = None,
        channel_qos_kwargs: dict | None = None,
    ):
        """blocking basemodel decorator to declare queue and attach callback to channel

        Example:
            assert isinstance(channel, pika.adapters.blocking_connection.BlockingChannel)
            assert isinstance(YourModel, wrabbit.BaseModel)

            @YourModel.run_on_recieve(channel)
            def do_something(model: YourModel):
                # gets called whenever the model is recieved in the queue
                print(f"Recieved {model}")

            channel.start_consuming() # begin listening

        """

        if channel_queue_kwargs is None:
            channel_queue_kwargs = {}

        if channel_qos_kwargs is None:
            channel_qos_kwargs = {}

        channel_queue_kwargs = {"exclusive": False, "durable": True, "auto_delete": False} | channel_queue_kwargs
        channel_qos_kwargs = {"prefetch_count": 3} | channel_qos_kwargs

        routing_key = routing_key_override if routing_key_override else cls.queue_name()

        channel.queue_declare(queue=routing_key, **channel_queue_kwargs)
        channel.basic_qos(**channel_qos_kwargs)

        def wrap_func(func: Callable):
            """inner function wrapper for run_on_recieve"""

            def callback(_ch, method, _properties, body):
                """callback to attach function to channel consumer"""
                res = func(cls.parse_raw(body))
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return res

            channel.basic_consume(
                queue=routing_key, auto_ack=False, on_message_callback=callback
            )

        return wrap_func


class Producer:
    """convience class for creating a producer application"""

    def __init__(
        self,
        host: str,
        pika_connection_parameters_kwargs: dict | None = None,
        pika_connection_kwargs: dict | None = None,
        pika_channel_kwargs: dict | None = None,
    ):
        """initalizes a pika.BlockingConnection and channel"""

        if pika_connection_parameters_kwargs is None:
            pika_connection_parameters_kwargs = {}
        if pika_connection_kwargs is None:
            pika_connection_kwargs = {}
        if pika_channel_kwargs is None:
            pika_channel_kwargs = {}

        connection_parameters = pika.ConnectionParameters(
            host, **pika_connection_parameters_kwargs
        )
        connection = pika.BlockingConnection(
            connection_parameters, **pika_connection_kwargs
        )
        self._channel = connection.channel(**pika_channel_kwargs)

    def send(self, model: BaseModel) -> None:
        ''' sends model into the queue
        Example:

        app = Producer()

        assert isinstance(MyModel, wrabbit.BaseModel)

        @app.send
        MyModel('params')

        '''
        model.send(self._channel)


class Consumer:
    """convience class for creating a consumer application

    Note that with wrabbit, there can only be one consumer per model type

    """

    def __init__(
        self,
        host: str,
        pika_connection_parameters_kwargs: dict | None = None,
        pika_connection_kwargs: dict | None = None,
        pika_channel_kwargs: dict | None = None,
    ):
        """initalizes a pika.BlockingConnection and channel"""

        if pika_connection_parameters_kwargs is None:
            pika_connection_parameters_kwargs = {"heartbeat":360}
        if pika_connection_kwargs is None:
            pika_connection_kwargs = {}
        if pika_channel_kwargs is None:
            pika_channel_kwargs = {}

        connection_parameters = pika.ConnectionParameters(
            host, **pika_connection_parameters_kwargs
        )
        connection = pika.BlockingConnection(
            connection_parameters, **pika_connection_kwargs
        )
        self._channel = connection.channel(**pika_channel_kwargs)

    def run(self) -> None:
        """set up blocking listener for callbacks"""
        self._channel.start_consuming()

    def run_on_recieve(
            self,
            **run_on_recieve_kwargs,
            ) -> Callable:
        """set up callable for argument type
        valid functions contained a typed annotation
        for a wrabbit BaseModel, or a union of such
        Overrides are passed into the setup

        For example:

        app = wrabbit.Consumer(HOST)
        assert isinstance(MyModel, wrabbit.BaseModel)

        @app.run_on_recieve()
        def do_something_with_mymodel(data: MyModel) -> None:
            ...
            pass
        """

        def set_up_run(func: Callable) -> None:
            ''' adds run_on_recieve callback '''
            types = inspect.get_annotations(func)

            if 'return' in types:
                if types['return'] is not None:
                    raise ValueError(f"Return value of callback {func.__name__} must be None")
                types.pop('return')

            # check to see if function is valid
            if len(types) != 1:
                raise ValueError(
                    f"wrabbit run_on_recieve function {func.__name__} can only have one argument"
                )

            for model_type in types.values():
                # add callback to each type
                model_type.run_on_recieve(self._channel, **run_on_recieve_kwargs)(func)

        return set_up_run
