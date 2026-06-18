import requests
import urllib.parse
import logging

logger = logging.getLogger("JIMI.MapsService")

class MapsService:
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        # User-Agent descritivo para evitar bloqueios na API pública do OpenStreetMap
        self.headers = {"User-Agent": "JIMI_Assistant_Project_Bot"}

    def handle(self, action: str, payload=None):
        """
        Ponto de entrada unificado para o ServicesManager do JIMI.
        Roteia buscas de coordenadas ou geração de rotas.
        """
        if not payload:
            return "Erro: Nenhum endereço ou destino foi informado para a operação de mapas."

        if action == "route":
            return self.get_routing_link(str(payload))
            
        elif action == "search":
            return self.search_place(str(payload))
            
        return f"Ação '{action}' não é suportada pelo módulo de Mapas."

    def search_place(self, query: str) -> dict:
        """Busca informações de endereço e coordenadas (Lat/Lon) de um local."""
        logger.info(f"Buscando coordenadas para: {query}")
        params = {"q": query, "format": "json", "limit": 1}
        
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                location = data[0]
                return {
                    "success": True,
                    "display_name": location.get("display_name"),
                    "lat": location.get("lat"),
                    "lon": location.get("lon")
                }
            return {"success": False, "message": "Local não encontrado nos mapas."}
        except Exception as e:
            logger.error(f"Erro na busca de mapas: {e}")
            return {"success": False, "message": f"Erro de conexão com o serviço de mapas: {e}"}

    def get_routing_link(self, destination: str) -> str:
        """Gera um link universal do Google Maps para navegação/rotas com GPS."""
        encoded_dest = urllib.parse.quote(destination)
        # CORREÇÃO: URL oficial e universal para abrir o GPS direto no destino desejado
        return f"https://www.google.com/maps/dir/?api=1&destination={encoded_dest}"


# Instanciação global necessária para o circuito do ServicesManager
maps_service = MapsService()