from rest_framework import serializers

class LocationSerializer(serializers.Serializer):
    """
    Sérialiseur pour les lieux
    """
    name = serializers.CharField(max_length=255)
    coordinates = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )

class RouteRequestSerializer(serializers.Serializer):
    """
    Sérialiseur pour les requêtes d'itinéraire
    """
    start_point = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    end_point = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    start_name = serializers.CharField(max_length=255, required=False)
    end_name = serializers.CharField(max_length=255, required=False)

class RouteResponseSerializer(serializers.Serializer):
    """
    Sérialiseur pour les réponses d'itinéraire
    """
    path = serializers.ListField(
        child=serializers.ListField(
            child=serializers.FloatField(),
            min_length=2,
            max_length=2
        )
    )
    distance = serializers.FloatField()  # en mètres
    duration = serializers.FloatField()  # en secondes
    duration_text = serializers.CharField(max_length=50, required=False)  # format texte (ex: "5 min 30 sec")
    start_point = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    end_point = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )

class SearchLocationSerializer(serializers.Serializer):
    """
    Sérialiseur pour la recherche de lieux
    """
    query = serializers.CharField(max_length=255)

