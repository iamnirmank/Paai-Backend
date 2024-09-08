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

class DocumentViewSet(AuthenticatedModelViewSet):
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_file(self, request):
        try:
            file = request.data.get('file')
            title = request.data.get('title')
            link = request.data.get('link')
            rooms = request.data.get('room')
            room = Rooms.objects.get(name=rooms)

            auth_header = request.headers.get('Authorization')
            check = check_valid_request(room, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
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

    @action(detail=True, methods=['put'], parser_classes=[MultiPartParser, FormParser])
    def update_document(self, request, pk=None):
        try:
            document = self.get_object()
            file = request.data.get('file')
            title = request.data.get('title')
            link = request.data.get('link')
            rooms = request.data.get('room')
            room = Rooms.objects.get(name=rooms)

            auth_header = request.headers.get('Authorization')
            check = check_valid_request(room, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            if title:
                document.title = title
            if file:
                if document.file:
                    document.file.delete
                document.file = file
                update_combined_chunks(document_ids=[document.id], room=room)
            if link:
                document.link = link
                update_combined_chunks(document_ids=[document.id], room=room)
            if room:
                document.room = room
                update_combined_chunks(document_ids=[document.id], room=room)

            document.save()
            
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
            document = self.get_object()
            rooms = Rooms.documents.filter(name=document.room)
            auth_header = request.headers.get('Authorization')
            check = check_valid_request(rooms, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
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
    # get documents by id
    @action(detail=True, methods=['get'])
    def get_documents(self, request, pk=None):
        try:
            rooms = Rooms.objects.get(name=pk)
            auth_header = request.headers.get('Authorization')
            check = check_valid_request(rooms, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            documents = Documents.objects.filter(room=pk)
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

    # @action(detail=False, methods=['delete'])
    # def delete_all_documents(self, request): ## Caution: This is only for testing purposes
    #     try:
    #         documents = Documents.objects.all()
    #         update_combined_chunks(document_ids=[doc.id for doc in documents], delete=True)
    #         for document in documents:
    #             if document.file:
    #                 document.file.delete()
    #             document.delete()
    #         return create_response(
    #             True, 
    #             'All documents deleted successfully', 
    #             status_code=status.HTTP_200_OK
    #         )
    #     except Exception as e:
    #         return create_response(
    #             False, 
    #             f'Error deleting all documents: {str(e)}', 
    #             status_code=status.HTTP_400_BAD_REQUEST
    #         )

class QueryViewSet(AuthenticatedModelViewSet):
    @action(detail=False, methods=['post'])
    def process_chat(self, request):
        try:
            query_text = request.data.get('query')
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)
            auth_header = request.headers.get('Authorization')
            check = check_valid_request(room, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            if not query_text or not room_name:
                raise ValidationError('Query text and room ID are required')
            
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
    # edit query by id
    @action(detail=True, methods=['put'])
    def edit_query(self, request, pk=None):
        try:
            query = self.get_object()
            query_text = request.data.get('query')
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)
            auth_header = request.headers.get('Authorization')
            check = check_valid_request(room, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            query.query_text = query_text
            query.response_text = process_query(query_text, room_name)
            if room_name:
                query.room_name = room_name
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
            check = check_valid_request(room, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            queries = Query.objects.filter(room=pk)
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
    @action(detail=False, methods=['get'])
    def get_rooms(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                parts = auth_header.split(' ')
            if len(parts) == 2:
                token = parts[1]
            
            if not token:
                return None
            
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
            room = self.get_object()
            auth_header = request.headers.get('Authorization')
            check = check_valid_request(room, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            documents = Documents.objects.filter(room=room)
            documents.delete()
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
            room = self.get_object()
            name = request.data.get('name')
            user = request.data.get('user')
            auth_header = request.headers.get('Authorization')
            check = check_valid_request(room, auth_header)
            if not check:
                return create_response(
                    False, 
                    'Unauthorized request', 
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            if name:
                room.name = name
            if user:
                room.user = user
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
