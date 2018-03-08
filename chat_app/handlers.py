import asyncio
import json
import logging
import urllib
import uuid
import websockets

from django.template.defaultfilters import date as dj_date

from chat_app import channels, models, router


logger = logging.getLogger('chat_app')
ws_connections = {}



def fanout_message(connections, payload):

    for conn in connections:
        try:
            yield from conn.send(json.dumps(payload))
        except Exception as e:
            logger.debug('could not send', e)






def users_changed_handler(stream):

    while True:
        yield from stream.get()


        users = [
            {'username': username, 'uuid': uuid_str}
            for username, uuid_str in ws_connections.values()
        ]


        packet = {
            'type': 'users-changed',
            'value': sorted(users, key=lambda i: i['username'])
        }
        logger.debug(packet)
        yield from fanout_message(ws_connections.keys(), packet)



def main_handler(websocket, path):



    username = urllib.parse.unquote(path[1:])


    ws_connections[websocket] = (username, str(uuid.uuid4()))



    try:
        while websocket.open:
            data = yield from websocket.recv()
            if not data: continue
            logger.debug(data)
            try:
                yield from router.MessageRouter(data)()
            except Exception as e:
                logger.error('could not route msg', e)

    except websockets.exceptions.InvalidState:
        pass
    finally:
        del ws_connections[websocket]
