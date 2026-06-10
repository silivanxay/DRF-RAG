from rest_framework import serializers


class QueryRequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    collection_name = serializers.CharField(default="documents")
    top_k = serializers.IntegerField(default=4, min_value=1, max_value=20)


class SourceSerializer(serializers.Serializer):
    page_content = serializers.CharField()
    source = serializers.CharField()
    page = serializers.IntegerField()


class QueryResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    sources = SourceSerializer(many=True)
