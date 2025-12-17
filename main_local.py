#!/usr/bin/env python
"""
Script para pruebas locales del sistema SPU Multiagente.

Para ejecutar:
1. Asegúrate de tener las dependencias instaladas: pip install -r requirements.txt
2. Configura autenticación:
   - Opción A (recomendada): Usa ADC con: gcloud auth application-default login
   - Opción B: Crea un archivo .env con GOOGLE_API_KEY
3. Ejecuta: python main_local.py
"""
import os
import sys
import json
from datetime import datetime

# Cargar variables de entorno desde .env si existe
from dotenv import load_dotenv
load_dotenv()

# Configurar proyecto si no está definido (para pruebas locales)
# Estos valores son solo para desarrollo local, en Cloud Run vienen del cloudbuild.yaml
if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    os.environ["GOOGLE_CLOUD_PROJECT"] = os.environ.get("GCP_PROJECT", "sb-iacorredores-dev")
if not os.environ.get("GOOGLE_CLOUD_LOCATION"):
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ.get("GCP_LOCATION", "us-central1")

print("=" * 60)
print("🚀 MS-CV-SPU-MULTIAGENTE - Prueba Local")
print("=" * 60)
print(f"   Proyecto: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
print(f"   Ubicación: {os.environ.get('GOOGLE_CLOUD_LOCATION')}")
print("=" * 60)


def test_catalogo():
    """Prueba la conexión al catálogo de Automy."""
    print("\n📦 Probando conexión al catálogo de productos...")
    from src.services.catalogo_service import CatalogoService
    
    catalogo = CatalogoService()
    productos = catalogo.obtener_catalogo()
    
    if productos:
        print(f"   ✅ Catálogo cargado: {len(productos)} productos")
        # Mostrar algunas categorías
        categorias = set(p.get("categoria_de_programas", "Sin categoría") for p in productos)
        print(f"   📁 Categorías disponibles: {len(categorias)}")
        for cat in list(categorias)[:5]:
            print(f"      - {cat}")
        return True
    else:
        print("   ❌ Error cargando catálogo")
        return False


def test_llm():
    """Prueba la conexión al LLM."""
    print("\n🤖 Probando conexión al LLM (Gemini)...")
    from src.services.llm_service import LLMService
    
    try:
        llm = LLMService()
        respuesta = llm.generar_respuesta(
            system_prompt="Eres un asistente útil.",
            user_prompt="Responde solo con: 'Conexión exitosa'",
            temperature=0.1
        )
        if "exitosa" in respuesta.lower():
            print(f"   ✅ LLM respondió: {respuesta.strip()}")
            return True
        else:
            print(f"   ⚠️ Respuesta inesperada: {respuesta[:100]}")
            return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_flujo_completo():
    """Ejecuta el flujo completo con datos de prueba."""
    print("\n📋 Ejecutando flujo completo...")
    from src.agents.orquestador import AgenteOrquestador
    
    # Datos de prueba
    datos_prueba = {
        "nombre_empresa": "EMPRESA DE PRUEBA S.A.S.",
        "numero_empleados": 150,
        "codigo_ciiu": "4530",  # Comercio de partes y piezas
        "aportes_mensuales": 8000000,  # $8 millones
        "porcentaje_reinversion": 20,
        "enfoque_prioritario": "Seguridad Industrial",
        "correo_destinatario": "cliente@empresa.com"
    }
    
    print(f"\n   📌 Datos de entrada:")
    for key, value in datos_prueba.items():
        print(f"      - {key}: {value}")
    
    try:
        orquestador = AgenteOrquestador()
        resultado = orquestador.ejecutar(datos_prueba)
        
        if resultado.get("status") == "success":
            print("\n   ✅ Flujo completado exitosamente!")
            print(f"   📄 PDF generado: {resultado.get('pdf_generado')}")
            print(f"   📊 Tamaño PDF: {resultado.get('pdf_size_bytes', 0):,} bytes")
            
            # Guardar resultado JSON
            output_file = f"output/resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("output", exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2, default=str)
            print(f"   💾 Resultado guardado en: {output_file}")
            
            return True
        else:
            print(f"\n   ❌ Error: {resultado.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n   ❌ Error ejecutando flujo: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Menú principal de pruebas."""
    print("\n¿Qué deseas probar?")
    print("1. Solo catálogo de productos")
    print("2. Solo conexión LLM")
    print("3. Flujo completo")
    print("4. Todas las pruebas")
    print("0. Salir")
    
    try:
        opcion = input("\nSelecciona una opción (0-4): ").strip()
    except KeyboardInterrupt:
        print("\n\nCancelado por el usuario.")
        return
    
    if opcion == "0":
        print("Saliendo...")
        return
    elif opcion == "1":
        test_catalogo()
    elif opcion == "2":
        test_llm()
    elif opcion == "3":
        test_flujo_completo()
    elif opcion == "4":
        print("\n" + "=" * 60)
        print("EJECUTANDO TODAS LAS PRUEBAS")
        print("=" * 60)
        
        resultados = {
            "Catálogo": test_catalogo(),
            "LLM": test_llm(),
            "Flujo completo": test_flujo_completo()
        }
        
        print("\n" + "=" * 60)
        print("RESUMEN DE PRUEBAS")
        print("=" * 60)
        for nombre, resultado in resultados.items():
            status = "✅ PASÓ" if resultado else "❌ FALLÓ"
            print(f"   {nombre}: {status}")
    else:
        print("Opción no válida")


if __name__ == "__main__":
    main()

