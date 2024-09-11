from Auth.models import User
from Auth.utils import check_valid_request, jwt_decode_handler
from Chatmate.Utility.auth_helpers import create_response
from Chatmate.Utility.processing_documents import update_combined_chunks
from Chatmate.Utility.processing_query import process_query
from Chatmate.models import CombinedChunk, Documents, Query, Rooms
from Chatmate.serializers import CombinedChunkSerializer, DocumentSerializer, QuerySerializer, RoomsSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

class AuthenticatedModelViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def check_auth(self, room, auth_header):
        check = check_valid_request(room, auth_header)
        if not check:
            return create_response(
                False, 
                'Unauthorized request', 
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        return check

class DocumentViewSet(AuthenticatedModelViewSet):
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def handle_document_update(self, document, room, file=None, title=None, link=None):
        if title:
            document.title = title
        if file:
            if document.file:
                document.file.delete()
            document.file = file
            update_combined_chunks(document_ids=[document.id], room=room)
        if link:
            document.link = link
            update_combined_chunks(document_ids=[document.id], room=room)
        if room:
            document.room = room
            update_combined_chunks(document_ids=[document.id], room=room)
        document.save()

    @action(detail=False, methods=['post'])
    def upload_file(self, request):
        try:
            file = request.data.get('file')
            title = request.data.get('title')
            link = request.data.get('link')
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)
            
            document = Documents.objects.create(file=file, title=title, link=link, room=room)
            update_combined_chunks(document_ids=[document.id], room=room)
            
            return create_response(
                True, 
                'Document uploaded successfully', 
                body=DocumentSerializer(document).data, 
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error uploading document: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'])
    def update_document(self, request, pk=None):
        try:
            document = Documents.objects.get(id=pk)
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)
            
            self.handle_document_update(
                document,
                room,
                file=request.data.get('file'),
                title=request.data.get('title'),
                link=request.data.get('link')
            )
            
            return create_response(
                True, 
                'Document updated successfully', 
                body=DocumentSerializer(document).data, 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error updating document: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def delete_document(self, request, pk=None):
        try:
            document = Documents.objects.get(id=pk)
            room = document.room

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)
            
            update_combined_chunks(document_ids=[document.id], delete=True)
            if document.file:
                document.file.delete()
            document.delete()
            
            return create_response(
                True, 
                'Document deleted successfully', 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error deleting document: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def get_documents(self, request, pk=None):
        try:
            room = Rooms.objects.get(name=pk)

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)
            
            documents = Documents.objects.filter(room=room)
            if not documents.exists():
                raise ValidationError('No documents found for this room')
            
            return create_response(
                True, 
                'Documents fetched successfully', 
                body=DocumentSerializer(documents, many=True).data, 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error fetching documents: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )


class QueryViewSet(AuthenticatedModelViewSet):
    serializer_class = QuerySerializer

    @action(detail=False, methods=['post'])
    def process_chat(self, request):
        try:
            query_text = request.data.get('query')
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)

            if not query_text:
                raise ValidationError('Query text is required')
            
            response_text = process_query(query_text, room_name)
            query = Query.objects.create(query_text=query_text, response_text=response_text, room=room)
            
            return create_response(
                True, 
                'Query processed successfully', 
                body=QuerySerializer(query).data, 
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error processing query: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'])
    def edit_query(self, request, pk=None):
        try:
            query = Query.objects.get(id=pk)
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)

            query.query_text = request.data.get('query')
            query.response_text = process_query(query.query_text, room_name)
            query.save()
            
            return create_response(
                True, 
                'Query edited successfully', 
                body=QuerySerializer(query).data, 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error editing query: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def get_queries_by_room_id(self, request, pk=None):
        try:
            room = Rooms.objects.get(name=pk)

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)

            queries = Query.objects.filter(room=room)
            if not queries.exists():
                raise ValidationError('No queries found for this room')
            
            return create_response(
                True, 
                'Queries fetched successfully', 
                body=QuerySerializer(queries, many=True).data, 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error fetching queries: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )


class RoomsViewSet(AuthenticatedModelViewSet):
    serializer_class = RoomsSerializer

    @action(detail=False, methods=['get'])
    def get_rooms(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
            
            if not token:
                return create_response(False, 'Invalid token', status_code=status.HTTP_400_BAD_REQUEST)

            decoded_token = jwt_decode_handler(token)
            user = User.objects.get(id=decoded_token['user_id'])

            rooms = Rooms.objects.filter(user=user)
            if not rooms.exists():
                raise ValidationError('No rooms found')
            
            return create_response(
                True, 
                'Rooms fetched successfully', 
                body=RoomsSerializer(rooms, many=True).data, 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error fetching rooms: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def delete_room(self, request, pk=None):
        try:
            room = Rooms.objects.get(id=pk)
            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)

            Documents.objects.filter(room=room).delete()
            Query.objects.filter(room=room).delete()
            room.delete()
            
            return create_response(
                True, 
                'Room deleted successfully', 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error deleting room: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'])
    def update_room(self, request, pk=None):
        try:
            room = Rooms.objects.get(id=pk)

            auth_header = request.headers.get('Authorization')
            if not self.check_auth(room, auth_header):
                return self.check_auth(room, auth_header)

            room.name = request.data.get('name', room.name)
            user = request.data.get('user', room.user)
            room.user = User.objects.get(id=user)
            queries = Query.objects.filter(room=room)
            for query in queries:
                query.room = room
                query.save()
            room.save()
            
            return create_response(
                True, 
                'Room updated successfully', 
                body=RoomsSerializer(room).data, 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error updating room: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def create_room(self, request):
        try:
            name = request.data.get('name')
            user_id = request.data.get('user')
            user = User.objects.get(id=user_id)

            room = Rooms.objects.create(name=name, user=user)
            
            return create_response(
                True, 
                'Room created successfully', 
                body=RoomsSerializer(room).data, 
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error creating room: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )
