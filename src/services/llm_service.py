"""
Servicio LLM usando Google GenAI (Gemini).
Basado en la implementación de ms-sd-prospector-multiagente.
"""
import os
import json
import re
from typing import Optional, Dict, Any, List, Union

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None


class LLMService:
    """Servicio para interactuar con modelos Gemini via Google GenAI."""
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
    ):
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai no está instalado. Ejecuta: pip install google-genai")
        
        self._model_name = model_name
        self._temperature = temperature
        
        # Obtener configuración
        resolved_project = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
        resolved_location = location or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        resolved_api_key = os.environ.get("GOOGLE_API_KEY")
        
        # Configurar cliente - preferir Vertex AI (ADC), fallback a API key
        if resolved_project:
            try:
                self._client = genai.Client(
                    vertexai=True,
                    project=resolved_project,
                    location=resolved_location
                )
                print(f"✅ Google GenAI configurado con Vertex AI (proyecto: {resolved_project})")
            except Exception as e:
                if resolved_api_key:
                    self._client = genai.Client(api_key=resolved_api_key)
                    print(f"✅ Google GenAI configurado con API key (fallback)")
                else:
                    raise EnvironmentError(f"Error configurando GenAI: {e}")
        elif resolved_api_key:
            self._client = genai.Client(api_key=resolved_api_key)
            print(f"✅ Google GenAI configurado con API key")
        else:
            raise EnvironmentError(
                "No se encontró autenticación para google.genai. "
                "Configura GOOGLE_CLOUD_PROJECT o GOOGLE_API_KEY."
            )
        
        print(f"   Modelo: {self._model_name}")
    
    def generar_respuesta(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: int = 8192
    ) -> str:
        """
        Genera una respuesta usando el modelo LLM.
        
        Args:
            system_prompt: Instrucciones del sistema
            user_prompt: Mensaje del usuario
            temperature: Creatividad (0.0 - 1.0)
            max_tokens: Máximo de tokens en la respuesta
            
        Returns:
            Respuesta del modelo como string
        """
        try:
            # Combinar prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Configuración de generación
            config = types.GenerateContentConfig(
                temperature=temperature or self._temperature,
                max_output_tokens=max_tokens,
                top_p=0.95,
            )
            
            # Generar respuesta
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=full_prompt,
                config=config
            )
            
            return response.text
            
        except Exception as e:
            print(f"❌ Error generando respuesta LLM: {e}")
            raise
    
    def generar_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Genera una respuesta JSON estructurada.
        
        Args:
            system_prompt: Instrucciones del sistema
            user_prompt: Mensaje del usuario
            temperature: Creatividad (menor para respuestas más determinísticas)
            
        Returns:
            Diccionario parseado desde JSON
        """
        try:
            respuesta_raw = self.generar_respuesta(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature or 0.2  # Más bajo para JSON
            )
            
            return self._limpiar_y_parsear_json(respuesta_raw)
            
        except Exception as e:
            print(f"❌ Error en generar_json: {e}")
            raise
    
    def _limpiar_y_parsear_json(self, text: str) -> Dict[str, Any]:
        """Limpia y parsea JSON desde respuesta del LLM."""
        if not text:
            return {}
        
        # Limpiar markdown
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Intentar parsear directamente
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Buscar JSON en el texto
        json_pattern = r'\{[\s\S]*\}'
        matches = re.findall(json_pattern, cleaned)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        print(f"⚠️ No se pudo parsear JSON: {text[:200]}...")
        return {}
