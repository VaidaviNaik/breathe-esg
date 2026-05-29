from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Client, IngestionBatch, EmissionRecord, ParseError
from .serializers import *
from .parsers import parse_sap_csv, parse_utility_csv, parse_travel_csv


class ClientListView(APIView):
    def get(self, request):
        clients = Client.objects.all()
        return Response(ClientSerializer(clients, many=True).data)

    def post(self, request):
        s = ClientSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class IngestView(APIView):
    def post(self, request):
        source_type = request.data.get('source_type')
        client_id = request.data.get('client_id')
        file = request.FILES.get('file')

        if not all([source_type, client_id, file]):
            return Response({'error': 'source_type, client_id, and file are required'}, status=400)

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=404)

        content = file.read().decode('utf-8', errors='replace')
        batch = IngestionBatch.objects.create(
            client=client,
            source_type=source_type,
            uploaded_file_name=file.name,
        )

        parser_map = {
            'SAP': parse_sap_csv,
            'UTILITY': parse_utility_csv,
            'TRAVEL': parse_travel_csv,
        }

        parser = parser_map.get(source_type)
        if not parser:
            return Response({'error': 'Unknown source_type'}, status=400)

        records, errors = parser(content, batch, client)

        # Bulk create records
        EmissionRecord.objects.bulk_create([EmissionRecord(**r) for r in records])
        ParseError.objects.bulk_create([ParseError(batch=batch, **e) for e in errors])

        batch.row_count = len(records)
        batch.error_count = len(errors)
        batch.save()

        return Response({
            'batch_id': str(batch.id),
            'rows_ingested': len(records),
            'errors': len(errors),
        }, status=201)


class DashboardView(APIView):
    def get(self, request):
        client_id = request.query_params.get('client_id')
        qs = EmissionRecord.objects.all()
        if client_id:
            qs = qs.filter(client_id=client_id)

        records = EmissionRecordSerializer(qs[:200], many=True).data

        # Summary stats
        total_co2e = sum(r['co2e_kg'] or 0 for r in records)
        by_scope = {}
        for r in records:
            s = str(r['scope'])
            by_scope[s] = by_scope.get(s, 0) + (r['co2e_kg'] or 0)

        status_counts = {}
        for r in records:
            st = r['status']
            status_counts[st] = status_counts.get(st, 0) + 1

        return Response({
            'records': records,
            'summary': {
                'total_co2e_kg': round(total_co2e, 2),
                'by_scope': {k: round(v, 2) for k, v in by_scope.items()},
                'by_status': status_counts,
            }
        })


class RecordReviewView(APIView):
    def patch(self, request, record_id):
        try:
            record = EmissionRecord.objects.get(id=record_id)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        new_status = request.data.get('status')
        note = request.data.get('analyst_note', '')
        reviewer = request.data.get('reviewed_by', 'analyst')

        if new_status not in ['APPROVED', 'FLAGGED', 'REJECTED', 'PENDING']:
            return Response({'error': 'Invalid status'}, status=400)

        record.status = new_status
        record.analyst_note = note
        record.reviewed_by = reviewer
        record.reviewed_at = timezone.now()
        record.save()

        return Response(EmissionRecordSerializer(record).data)


class BatchListView(APIView):
    def get(self, request):
        client_id = request.query_params.get('client_id')
        qs = IngestionBatch.objects.all()
        if client_id:
            qs = qs.filter(client_id=client_id)
        return Response(IngestionBatchSerializer(qs, many=True).data)


class ParseErrorView(APIView):
    def get(self, request, batch_id):
        errors = ParseError.objects.filter(batch_id=batch_id)
        return Response(ParseErrorSerializer(errors, many=True).data)