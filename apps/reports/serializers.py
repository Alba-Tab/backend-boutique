from rest_framework import serializers

class ReportQueryInputSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=2000)

class ReportQueryOutputSerializer(serializers.Serializer):
    query_original = serializers.CharField()
    parsed_query = serializers.DictField()
    report = serializers.DictField()