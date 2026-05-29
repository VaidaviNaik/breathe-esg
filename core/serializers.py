from rest_framework import serializers
from .models import Client, IngestionBatch, EmissionRecord, ParseError

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class IngestionBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionBatch
        fields = '__all__'

class EmissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionRecord
        fields = '__all__'

class ParseErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParseError
        fields = '__all__'