from Chatmate.Utility.auth_helpers import create_response
from Chatmate.Utility.processing_documents import update_combined_chunks
from Chatmate.Utility.processing_query import process_query
from Chatmate.models import CombinedChunk, Documents, Query, Rooms
from Chatmate.serializers import CombinedChunkSerializer, DocumentSerializer, QuerySerializer, RoomsSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Documents.objects.all()
    serializer_class = DocumentSerializer

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_file(self, request):
        try:
            file = request.data.get('file')
            title = request.data.get('title')
            link = request.data.get('link')
            rooms = request.data.get('room')
            room = Rooms.objects.get(name=rooms)
            document = Documents.objects.create(file=file, title=title, link=link, room=room)
            update_combined_chunks(document_ids=[document.id])
            
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
            if title:
                document.title = title
            if file:
                if document.file:
                    document.file.delete
                document.file = file
                update_combined_chunks(document_ids=[document.id])
            if link:
                document.link = link
                update_combined_chunks(document_ids=[document.id])
            if room:
                document.room = room
                update_combined_chunks(document_ids=[document.id])

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

    @action(detail=False, methods=['delete'])
    def delete_all_documents(self, request):
        try:
            documents = Documents.objects.all()
            update_combined_chunks(document_ids=[doc.id for doc in documents], delete=True)
            for document in documents:
                if document.file:
                    document.file.delete()
                document.delete()
            return create_response(
                True, 
                'All documents deleted successfully', 
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return create_response(
                False, 
                f'Error deleting all documents: {str(e)}', 
                status_code=status.HTTP_400_BAD_REQUEST
            )


class QueryViewSet(viewsets.ModelViewSet):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer

    @action(detail=False, methods=['post'])
    def process_chat(self, request):
        try:
            query_text = request.data.get('query')
            room_id = request.data.get('room')
            if not query_text or not room_id:
                raise ValidationError('Query text and room ID are required')
            
            response_text = process_query(query_text, room_id)
            query = Query.objects.create(query_text=query_text, response_text=response_text, room_id=room_id)
            
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
            room_id = request.data.get('room')
            query.query_text = query_text
            query.response_text = process_query(query_text, room_id)
            if room_id:
                query.room_id = room_id
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
            queries = Query.objects.filter(room_id=pk)
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


class CombinedChunkViewSet(viewsets.ModelViewSet):
    queryset = CombinedChunk.objects.all()
    serializer_class = CombinedChunkSerializer


class RoomsViewSet(viewsets.ModelViewSet):
    queryset = Rooms.objects.all()
    serializer_class = RoomsSerializer
