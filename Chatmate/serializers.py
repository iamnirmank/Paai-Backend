from rest_framework import serializers
from . import models

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Documents
        fields = '__all__'

class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Query
        fields = '__all__'

class CombinedChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CombinedChunk
        fields = '__all__'

class RoomsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rooms
        fields = '__all__'