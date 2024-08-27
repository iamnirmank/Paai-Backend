from rest_framework.response import Response
from rest_framework import status

def create_response(success, message, body=None, status_code=status.HTTP_200_OK):
        response_data = {'success': success, 'message': message}
        if body is not None:
            response_data['body'] = body
        return Response(response_data, status=status_code)