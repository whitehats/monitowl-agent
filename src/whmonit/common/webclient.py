# -*- coding: utf-8 -*-
'''
Websockets request manager for WebAPI.
'''

import json
from websocket import create_connection

from .error import Error


class AuthenticationError(Error):
    '''
    Raised on authorization failure.
    '''
    params = 'username'
    text = ('Supplied username [`{username}`] and/or password are incorrect.')


class ComputationError(Error):
    '''
    Raised on computation failure.
    '''
    params = 'reason'
    text = 'Computation failed with response: `{reason}`'


class RequestManager(object):
    '''
    Request manager for websockets.
    '''
    def __init__(self, address):
        '''
        Constructor.

        :param address: Websocket address to connect to.
        '''
        self.req_id = 1

        self.websocket = create_connection(address)

    def _make_request(self, component, action, params):
        '''
        Creates stringified JSON request object.
        '''
        request = json.dumps({
            'component': component,
            'action': action,
            'params': params,
            'id': str(self.req_id),
        })
        self.req_id += 1
        return request

    def auth(self, username, password):
        '''
        Shortcut method used to authenticate user to the host.
        '''
        success = self.request(
            'auth', 'authenticate',
            {'username': username, 'password': password},
        )

        if success != 'OK':
            raise AuthenticationError(username)

    def request(self, component, action, params):
        '''
        Makes request on a websocket a waits for the response.
        '''
        self.websocket.send(self._make_request(component, action, params))

        while True:
            response = json.loads(self.websocket.recv())

            if response['status'] == 'success':
                return response['data']
            elif response['status'] == 'error':
                raise ComputationError(response['data']['message'])

    def close(self):
        '''
        Closes the websocket.
        '''
        self.websocket.close()
