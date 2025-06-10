from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    LocationSerializer, 
    RouteRequestSerializer, 
    RouteResponseSerializer,
    SearchLocationSerializer
)
from .utils import GeocodingService, RoutingService, TrafficDataService
from .models import MongoDBManager, PreExtractedLocation
from .ml_integration import MLIntegration
from datetime import datetime
import traceback
from django.db.models import Q

class SearchLocationView(APIView):
    """
    API pour rechercher des lieux par nom dans les données pré-extraites
    """
    def post(self, request):
        serializer = SearchLocationSerializer(data=request.data)
        
        if serializer.is_valid():
            query = serializer.validated_data['query']
            
            # Recherche dans les lieux pré-extraits avec une recherche insensible à la casse
            # et qui contient le terme de recherche
            locations = PreExtractedLocation.objects.filter(
                Q(name__icontains=query)
            ).order_by('name')[:10]  # Limiter à 10 résultats
            
            if locations:
                # Formater les résultats
                results = []
                for location in locations:
                    results.append({
                        'name': location.name,
                        'coordinates': location.coordinates
                    })
                return Response(results)
            
            return Response({'message': 'Aucun lieu trouvé'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RouteView(APIView):
    """
    API pour calculer un itinéraire entre deux points
    """
    def post(self, request):
        try:
            serializer = RouteRequestSerializer(data=request.data)
            
            if serializer.is_valid():
                start_point = serializer.validated_data['start_point']
                end_point = serializer.validated_data['end_point']
                
                # Vérifier si l'itinéraire existe déjà dans MongoDB
                existing_route = MongoDBManager.find_route(start_point, end_point)
                
                if existing_route and 'duration_text' in existing_route:
                    # Si l'itinéraire existe et contient le format de durée, le retourner
                    return Response({
                        'path': existing_route['path'],
                        'distance': existing_route['distance'],
                        'duration': existing_route['duration'],
                        'duration_text': existing_route['duration_text'],
                        'start_point': existing_route['start_point'],
                        'end_point': existing_route['end_point']
                    })
                
                # Sinon, calculer l'itinéraire avec l'API OSRM
                route = RoutingService.get_route(start_point, end_point)
                
                # Sauvegarder l'itinéraire dans MongoDB
                MongoDBManager.save_route(
                    start_point,
                    end_point,
                    route['path'],
                    route['distance'],
                    route['duration'],
                    route.get('duration_text', '')
                )
                
                return Response(route)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur dans RouteView: {str(e)}")
            traceback.print_exc()
            return Response(
                {'error': f"Une erreur s'est produite lors du calcul de l'itinéraire: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OptimizedRouteView(APIView):
    """
    API pour calculer un itinéraire optimisé entre deux points
    en utilisant le modèle de machine learning
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ml_integration = MLIntegration()
    
    def post(self, request):
        try:
            serializer = RouteRequestSerializer(data=request.data)
            
            if serializer.is_valid():
                start_point = serializer.validated_data['start_point']
                end_point = serializer.validated_data['end_point']
                
                # Utiliser le modèle de machine learning pour optimiser l'itinéraire
                route = self.ml_integration.predict_optimal_route(start_point, end_point)
                
                # Sauvegarder l'itinéraire optimisé dans MongoDB
                MongoDBManager.save_route(
                    start_point,
                    end_point,
                    route['path'],
                    route['distance'],
                    route['duration'],
                    route.get('duration_text', '')
                )
                
                # Filtrer les champs supplémentaires qui ne sont pas dans le sérialiseur
                response_data = {
                    'path': route['path'],
                    'distance': route['distance'],
                    'duration': route['duration'],
                    'duration_text': route.get('duration_text', ''),
                    'start_point': route['start_point'],
                    'end_point': route['end_point']
                }
                
                return Response(response_data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Erreur dans OptimizedRouteView: {str(e)}")
            traceback.print_exc()
            return Response(
                {'error': f"Une erreur s'est produite lors du calcul de l'itinéraire optimisé: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

