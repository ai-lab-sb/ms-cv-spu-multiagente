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
                print(f"[OK] Google GenAI configurado con Vertex AI (proyecto: {resolved_project})")
            except Exception as e:
                if resolved_api_key:
                    self._client = genai.Client(api_key=resolved_api_key)
                    print(f"[OK] Google GenAI configurado con API key (fallback)")
                else:
                    raise EnvironmentError(f"Error configurando GenAI: {e}")
        elif resolved_api_key:
            self._client = genai.Client(api_key=resolved_api_key)
            print(f"[OK] Google GenAI configurado con API key")
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
            print(f"[ERROR] Error generando respuesta LLM: {e}")
            raise
    
    def generar_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Genera una respuesta JSON estructurada.
        
        Args:
            system_prompt: Instrucciones del sistema
            user_prompt: Mensaje del usuario
            temperature: Creatividad (menor para respuestas más determinísticas)
            debug: Si True, imprime la respuesta cruda
            
        Returns:
            Diccionario parseado desde JSON
        """
        try:
            respuesta_raw = self.generar_respuesta(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature or 0.2,  # Más bajo para JSON
                max_tokens=65536  # Máximo tokens para respuestas grandes
            )
            
            if debug:
                print(f"\n[DEBUG] Respuesta LLM ({len(respuesta_raw)} chars):")
                print(respuesta_raw[:500] + "..." if len(respuesta_raw) > 500 else respuesta_raw)
            
            resultado = self._limpiar_y_parsear_json(respuesta_raw)
            
            if debug:
                print(f"\n[DEBUG] JSON parseado: {len(resultado)} keys")
            
            return resultado
            
        except Exception as e:
            print(f"[ERROR] Error en generar_json: {e}")
            raise
    
    def _limpiar_y_parsear_json(self, text: str) -> Dict[str, Any]:
        """Limpia y parsea JSON desde respuesta del LLM."""
        if not text:
            return {}
        
        # Limpiar markdown (múltiples formatos)
        cleaned = text.strip()
        
        # Eliminar bloques de código markdown
        if "```json" in cleaned:
            start = cleaned.find("```json") + 7
            end = cleaned.find("```", start)
            if end > start:
                cleaned = cleaned[start:end].strip()
        elif "```" in cleaned:
            start = cleaned.find("```") + 3
            end = cleaned.find("```", start)
            if end > start:
                cleaned = cleaned[start:end].strip()
        
        # Intentar parsear directamente
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Buscar el primer JSON completo (el objeto raíz)
        # Encontrar el primer '{' que NO esté dentro de un array
        first_brace = cleaned.find('{')
        if first_brace == -1:
            print(f"[WARN] No se encontro JSON: {text[:200]}...")
            return {}
        
        # Encontrar el cierre correspondiente
        depth = 0
        end_pos = -1
        for j in range(first_brace, len(cleaned)):
            c = cleaned[j]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end_pos = j
                    break
        
        if end_pos > first_brace:
            candidate = cleaned[first_brace:end_pos+1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
        
        # Fallback: buscar cualquier JSON válido
        for i, char in enumerate(cleaned):
            if char == '{':
                depth = 0
                for j in range(i, len(cleaned)):
                    if cleaned[j] == '{':
                        depth += 1
                    elif cleaned[j] == '}':
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(cleaned[i:j+1])
                            except json.JSONDecodeError:
                                break
        
        print(f"[WARN] No se pudo parsear JSON: {text[:200]}...")
        return {}
