'''

listen.py | example queue consumer for wrabbit type

'''

from wrabbit import Consumer
from example_types import MyModel

app = Consumer("localhost")

@app.run_on_recieve
def when_i_get_mymodel(data: MyModel) -> None:
    ''' callback for model receive '''
    print(data)


if __name__ == "__main__":
    app.run()
