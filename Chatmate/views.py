from Auth.models import User
from Auth.utils import check_auth, create_response, jwt_decode_handler
from Chatmate.Utility.processing_documents import update_combined_chunks
from Chatmate.Utility.processing_query import process_query
from Chatmate.models import Documents, Query, Rooms
from Chatmate.serializers import DocumentSerializer, QuerySerializer, RoomsSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

class AuthenticatedModelViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

class DocumentViewSet(AuthenticatedModelViewSet):
    """
    ViewSet for managing Documents. Provides upload, update, delete, and retrieval functionalities.
    """
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def handle_document_update(self, document, room, file=None, title=None, link=None):
        """
        Helper method to handle document updates based on provided data.
        """
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
        """
        Upload a new document to the specified room.
        """
        try:
            file = request.data.get('file')
            title = request.data.get('title')
            link = request.data.get('link')
            room_name = request.data.get('room')

            room = Rooms.objects.get(name=room_name)
            auth_header = request.headers.get('Authorization')

            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            document = Documents.objects.create(file=file, title=title, link=link, room=room)
            update_combined_chunks(document_ids=[document.id], room=room)

            return create_response(
                success=True, 
                message='Document uploaded successfully', 
                body=DocumentSerializer(document).data, 
                status_code=status.HTTP_201_CREATED
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Room not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error uploading document: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'])
    def update_document(self, request, pk=None):
        """
        Update the document based on the provided document ID.
        """
        try:
            document = Documents.objects.get(id=pk)
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)

            auth_header = request.headers.get('Authorization')
            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            self.handle_document_update(
                document, 
                room, 
                file=request.data.get('file'), 
                title=request.data.get('title'), 
                link=request.data.get('link')
            )

            return create_response(
                success=True, 
                message='Document updated successfully', 
                body=DocumentSerializer(document).data, 
                status_code=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Document or Room not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error updating document: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def delete_document(self, request, pk=None):
        """
        Delete the document based on the provided document ID.
        """
        try:
            document = Documents.objects.get(id=pk)
            room = document.room

            auth_header = request.headers.get('Authorization')
            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            update_combined_chunks(document_ids=[document.id], delete=True)
            if document.file:
                document.file.delete()
            document.delete()

            return create_response(
                success=True, 
                message='Document deleted successfully', 
                status_code=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Document not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error deleting document: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def get_documents(self, request, pk=None):
        """
        Retrieve all documents associated with the specified room name.
        """
        try:
            room = Rooms.objects.get(name=pk)

            auth_header = request.headers.get('Authorization')
            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            documents = Documents.objects.filter(room=room)
            if not documents.exists():
                raise ValidationError('No documents found for this room')

            return create_response(
                success=True, 
                message='Documents fetched successfully', 
                body=DocumentSerializer(documents, many=True).data, 
                status_code=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Room not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error fetching documents: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

class QueryViewSet(AuthenticatedModelViewSet):
    serializer_class = QuerySerializer

    @action(detail=False, methods=['post'])
    def process_chat(self, request):
        """
        Process a chat query and generate a response.
        """
        try:
            query_text = request.data.get('query')
            room_name = request.data.get('room')

            if not query_text:
                raise ValidationError('Query text is required')

            room = Rooms.objects.get(name=room_name)
            auth_header = request.headers.get('Authorization')

            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            response_text = process_query(query_text, room_name)
            query = Query.objects.create(query_text=query_text, response_text=response_text, room=room)

            return create_response(
                success=True, 
                message='Query processed successfully', 
                body=QuerySerializer(query).data, 
                status_code=status.HTTP_201_CREATED
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Room not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error processing query: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'])
    def edit_query(self, request, pk=None):
        """
        Edit an existing query by its ID.
        """
        try:
            query = Query.objects.get(id=pk)
            room_name = request.data.get('room')
            room = Rooms.objects.get(name=room_name)

            auth_header = request.headers.get('Authorization')
            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            query.query_text = request.data.get('query')
            query.response_text = process_query(query.query_text, room_name)
            query.save()

            return create_response(
                success=True, 
                message='Query edited successfully', 
                body=QuerySerializer(query).data, 
                status_code=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Query or Room not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error editing query: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def get_queries_by_room_id(self, request, pk=None):
        """
        Retrieve all queries associated with a specific room.
        """
        try:
            room = Rooms.objects.get(name=pk)

            auth_header = request.headers.get('Authorization')
            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            queries = Query.objects.filter(room=room)
            if not queries.exists():
                raise ValidationError('No queries found for this room')

            return create_response(
                success=True, 
                message='Queries fetched successfully', 
                body=QuerySerializer(queries, many=True).data, 
                status_code=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Room not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error fetching queries: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

class RoomsViewSet(AuthenticatedModelViewSet):
    serializer_class = RoomsSerializer

    @action(detail=False, methods=['get'])
    def get_rooms(self, request):
        """
        Retrieve all rooms associated with the authenticated user.
        """
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
                success=True, 
                message='Rooms fetched successfully', 
                body=RoomsSerializer(rooms, many=True).data, 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error fetching rooms: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def delete_room(self, request, pk=None):
        """
        Delete a room along with its associated documents and queries.
        """
        try:
            room = Rooms.objects.get(id=pk)
            auth_header = request.headers.get('Authorization')

            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            Documents.objects.filter(room=room).delete()
            Query.objects.filter(room=room).delete()
            room.delete()

            return create_response(
                success=True, 
                message='Room deleted successfully', 
                status_code=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Room not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error deleting room: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'])
    def update_room(self, request, pk=None):
        """
        Update a room's information such as name and associated user.
        """
        try:
            room = Rooms.objects.get(id=pk)

            auth_header = request.headers.get('Authorization')
            if not check_auth(room, auth_header):
                return check_auth(room, auth_header)

            room.name = request.data.get('name', room.name)
            user_id = request.data.get('user')
            room.user = User.objects.get(id=user_id) if user_id else room.user
            Documents.objects.filter(room=room).update(room=room)
            Query.objects.filter(room=room).update(room=room)
            room.save()

            return create_response(
                success=True, 
                message='Room updated successfully', 
                body=RoomsSerializer(room).data, 
                status_code=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='Room or User not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error updating room: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def create_room(self, request):
        """
        Create a new room and associate it with a user.
        """
        try:
            name = request.data.get('name')
            user_id = request.data.get('user')

            user = User.objects.get(id=user_id)
            room = Rooms.objects.create(name=name, user=user)

            return create_response(
                success=True, 
                message='Room created successfully', 
                body=RoomsSerializer(room).data, 
                status_code=status.HTTP_201_CREATED
            )
        except ObjectDoesNotExist:
            return create_response(
                success=False, 
                message='User not found', 
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return create_response(
                success=False, 
                message=f'Error creating room: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )
