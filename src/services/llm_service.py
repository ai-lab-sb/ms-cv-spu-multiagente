"""
Servicio LLM usando Vertex AI (Gemini)
Similar al usado en ms-sd-prospector-multiagente
"""
import os
import json
from typing import Optional
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig


class LLMService:
    """Servicio para interactuar con modelos Gemini via Vertex AI."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: str = "gemini-2.5-flash"
    ):
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT", "sb-iacorredores-stage")
        self._location = location or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        self._model_name = model_name
        
        # Inicializar Vertex AI
        vertexai.init(project=self._project_id, location=self._location)
        
        # Crear modelo
        self._model = GenerativeModel(self._model_name)
        
        print(f"✅ LLMService inicializado con modelo {self._model_name}")
    
    def generar_respuesta(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
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
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.95,
            )
            
            # Generar respuesta
            response = self._model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"❌ Error generando respuesta LLM: {e}")
            raise
    
    def generar_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> dict:
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
                temperature=temperature
            )
            
            # Limpiar respuesta (quitar markdown si existe)
            respuesta_limpia = respuesta_raw.strip()
            if respuesta_limpia.startswith("```json"):
                respuesta_limpia = respuesta_limpia[7:]
            if respuesta_limpia.startswith("```"):
                respuesta_limpia = respuesta_limpia[3:]
            if respuesta_limpia.endswith("```"):
                respuesta_limpia = respuesta_limpia[:-3]
            respuesta_limpia = respuesta_limpia.strip()
            
            # Parsear JSON
            return json.loads(respuesta_limpia)
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"   Respuesta raw: {respuesta_raw[:500]}...")
            raise
        except Exception as e:
            print(f"❌ Error en generar_json: {e}")
            raise

