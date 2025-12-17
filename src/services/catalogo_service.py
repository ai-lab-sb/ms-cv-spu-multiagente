"""
Servicio para obtener el catálogo de productos desde la API de Automy.
"""
import requests
from typing import List, Dict, Any


class CatalogoService:
    """Servicio para interactuar con el catálogo de productos ARL."""
    
    AUTOMY_URL = "https://apis.automy.global/entity/external/read/ZjlmNjY2N2ItNDc2YS00ZThmLTgxNzctNjdiNmJlNTFiMDQ3"
    
    def __init__(self):
        self._catalogo_cache = None
        print("✅ CatalogoService inicializado")
    
    def obtener_catalogo(self, page: int = 1, page_size: int = 400) -> List[Dict[str, Any]]:
        """
        Obtiene el catálogo de productos desde Automy.
        
        Args:
            page: Número de página
            page_size: Cantidad de registros por página
            
        Returns:
            Lista de productos del catálogo
        """
        # Usar cache si está disponible
        if self._catalogo_cache:
            return self._catalogo_cache
        
        try:
            url = f"{self.AUTOMY_URL}?page={page}&pageSize={page_size}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extraer items del catálogo
            if isinstance(data, dict) and "items" in data:
                self._catalogo_cache = data["items"]
            elif isinstance(data, list):
                self._catalogo_cache = data
            else:
                self._catalogo_cache = []
            
            print(f"✅ Catálogo cargado: {len(self._catalogo_cache)} productos")
            return self._catalogo_cache
            
        except Exception as e:
            print(f"❌ Error obteniendo catálogo: {e}")
            return []
    
    def filtrar_por_categoria(self, categoria: str) -> List[Dict[str, Any]]:
        """
        Filtra productos por categoría.
        
        Args:
            categoria: Nombre de la categoría a filtrar
            
        Returns:
            Lista de productos de esa categoría
        """
        catalogo = self.obtener_catalogo()
        return [
            p for p in catalogo 
            if p.get("categoria_de_programas", "").upper() == categoria.upper()
        ]

