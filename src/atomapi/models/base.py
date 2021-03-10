class BaseModel:
    ''' The base class for all models '''
    def __init__(self, atom):
        self.atom = atom

    def raise_for_json_error(self, json_response, request_url):
        ''' Check json response for error '''
        if 'message' in json_response:
            message = json_response['message']
            message_lower = message.lower()
            if 'endpoint not found' in message_lower:
                raise ConnectionError(f'Endpoint at "{request_url}" does not exist')
            if 'not authorized' in message_lower:
                raise ConnectionError(
                    f'You are not authorized to access "{request_url}" '
                    f'with the API Key "{self.atom.api_key}"'
                )
            raise ConnectionError(f'Error connecting to "{request_url}": {message}')
