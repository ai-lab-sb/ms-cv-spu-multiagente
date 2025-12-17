"""
Agente Orquestador - Coordina el flujo completo de generación de propuestas.
"""
from typing import Dict, Any
from datetime import datetime

from ..services.llm_service import LLMService
from ..services.catalogo_service import CatalogoService
from ..services.pdf_generator import PDFGenerator

from ..prompts.prompt_recolector import SYSTEM_PROMPT_RECOLECTOR, get_prompt_recolector
from ..prompts.prompt_perfil_riesgo import SYSTEM_PROMPT_PERFIL_RIESGO, get_prompt_perfil_riesgo
from ..prompts.prompt_selector_productos import SYSTEM_PROMPT_SELECTOR_PRODUCTOS, get_prompt_selector_productos
from ..prompts.prompt_documentador import SYSTEM_PROMPT_DOCUMENTADOR, get_prompt_documentador


class AgenteOrquestador:
    """
    Orquestador principal del sistema SPU.
    Coordina los 4 sub-agentes para generar propuestas comerciales.
    """
    
    def __init__(self):
        self._llm = LLMService()
        self._catalogo = CatalogoService()
        self._pdf_generator = PDFGenerator()
        
        print("[OK] AgenteOrquestador inicializado con todos los servicios")
    
    def ejecutar(self, datos_entrada: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de generación de propuesta.
        
        Args:
            datos_entrada: Datos del formulario inicial
            
        Returns:
            Resultado con la propuesta comercial y PDF
        """
        print("\n" + "="*60)
        print(">>> INICIANDO GENERACION DE PROPUESTA")
        print("="*60)
        print(f"   Empresa: {datos_entrada.get('nombre_empresa')}")
        print(f"   Empleados: {datos_entrada.get('numero_empleados')}")
        
        try:
            # PASO 1: Recolectar y validar datos
            print("\n[PASO 1] Validando datos del cliente...")
            resultado_recolector = self._ejecutar_recolector(datos_entrada)
            
            if resultado_recolector.get("proximo_paso") == "solicitar_datos_faltantes":
                return {
                    "status": "error",
                    "error": "Datos faltantes",
                    "datos_faltantes": resultado_recolector.get("datos_faltantes"),
                    "mensaje": resultado_recolector.get("mensaje")
                }
            
            print("   [OK] Datos validados correctamente")
            
            # PASO 2: Identificar perfil de riesgo
            print("\n[PASO 2] Identificando perfil de riesgo...")
            resultado_perfil = self._ejecutar_perfil_riesgo(datos_entrada)
            
            if resultado_perfil.get("proximo_paso") == "Error_Perfilamiento":
                return {
                    "status": "error",
                    "error": "No se pudo determinar el perfil de riesgo"
                }
            
            print(f"   [OK] Clase de riesgo: {resultado_perfil.get('clase_riesgo')}")
            
            # PASO 3: Calcular presupuesto anual
            print("\n[PASO 3] Calculando presupuesto...")
            aportes = float(datos_entrada.get("aportes_mensuales", 0))
            porcentaje = float(datos_entrada.get("porcentaje_reinversion", 0))
            presupuesto_anual = aportes * 12 * (porcentaje / 100)
            
            print(f"   [OK] Presupuesto anual: ${presupuesto_anual:,.0f}")
            
            # Combinar datos para el siguiente paso
            datos_combinados = {
                **datos_entrada,
                "presupuesto_anual": presupuesto_anual,
                "clase_riesgo": resultado_perfil.get("clase_riesgo"),
                "riesgos_generales": resultado_perfil.get("riesgos_generales", []),
                "obligaciones_legales": resultado_perfil.get("Obligaciones_legales", [])
            }
            
            # PASO 4: Seleccionar productos
            print("\n[PASO 4] Seleccionando productos...")
            resultado_productos = self._ejecutar_selector_productos(datos_combinados)
            
            print(f"   [OK] Productos obligatorios: {len(resultado_productos.get('productos_obligatorios', []))}")
            print(f"   [OK] Productos prioritarios: {len(resultado_productos.get('productos_prioritarios', []))}")
            print(f"   [OK] Valores agregados: {len(resultado_productos.get('valores_agregados', []))}")
            
            # Combinar con productos seleccionados
            datos_finales = {
                **datos_combinados,
                "productos_obligatorios": resultado_productos.get("productos_obligatorios", []),
                "productos_prioritarios": resultado_productos.get("productos_prioritarios", []),
                "valores_agregados": resultado_productos.get("valores_agregados", []),
                "resumen_presupuesto": resultado_productos.get("resumen_presupuesto", {})
            }
            
            # PASO 5: Generar documento final
            print("\n[PASO 5] Generando propuesta consolidada...")
            propuesta_final = self._ejecutar_documentador(datos_finales)
            
            print("   [OK] Propuesta consolidada generada")
            
            # PASO 6: Generar PDF
            print("\n[PASO 6] Generando PDF...")
            pdf_bytes = self._pdf_generator.generar_pdf(propuesta_final)
            
            print("   [OK] PDF generado exitosamente")
            
            print("\n" + "="*60)
            print("[SUCCESS] PROPUESTA COMERCIAL GENERADA EXITOSAMENTE")
            print("="*60 + "\n")
            
            return {
                "status": "success",
                "propuesta": propuesta_final,
                "pdf_generado": True,
                "pdf_size_bytes": len(pdf_bytes)
            }
            
        except Exception as e:
            print(f"\n[ERROR] Error en orquestador: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _ejecutar_recolector(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el agente recolector de datos."""
        return self._llm.generar_json(
            system_prompt=SYSTEM_PROMPT_RECOLECTOR,
            user_prompt=get_prompt_recolector(datos)
        )
    
    def _ejecutar_perfil_riesgo(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el agente de perfil de riesgo."""
        return self._llm.generar_json(
            system_prompt=SYSTEM_PROMPT_PERFIL_RIESGO,
            user_prompt=get_prompt_perfil_riesgo(datos)
        )
    
    def _ejecutar_selector_productos(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el agente selector de productos."""
        # Obtener catálogo de productos
        catalogo = self._catalogo.obtener_catalogo()
        
        # Limitar catálogo (formato compacto permite más productos)
        catalogo_limitado = catalogo[:80] if len(catalogo) > 80 else catalogo
        print(f"   [INFO] Usando {len(catalogo_limitado)} productos del catalogo")
        
        resultado = self._llm.generar_json(
            system_prompt=SYSTEM_PROMPT_SELECTOR_PRODUCTOS,
            user_prompt=get_prompt_selector_productos(datos, catalogo_limitado),
            temperature=0.5  # Un poco más de creatividad para selección
        )
        
        return resultado
    
    def _ejecutar_documentador(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el agente documentador."""
        # Agregar fecha de generación
        datos["fecha_generacion"] = datetime.now().strftime("%Y-%m-%d")
        
        return self._llm.generar_json(
            system_prompt=SYSTEM_PROMPT_DOCUMENTADOR,
            user_prompt=get_prompt_documentador(datos)
        )

