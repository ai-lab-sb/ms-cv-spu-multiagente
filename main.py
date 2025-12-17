#!/usr/bin/env python
"""
MS-CV-SPU-MULTIAGENTE
Sistema Único de Propuesta - Multiagente para ARL Seguros Bolívar

Este servicio orquesta múltiples agentes de IA para generar propuestas
comerciales personalizadas de ARL.
"""
from flask import Flask, request, jsonify
from datetime import datetime
import os

from dotenv import load_dotenv
load_dotenv()

# Cargar secrets desde Secret Manager
try:
    from load_secrets import load_secrets_from_json
    load_secrets_from_json()
except Exception as e:
    print(f"[WARN] No se pudieron cargar secrets desde Secret Manager: {e}")
    print("   Usando variables de entorno locales...")

app = Flask(__name__)

# Importar el orquestador después de cargar secrets
from src.agents.orquestador import AgenteOrquestador

# Inicializar orquestador globalmente
_orquestador = None
try:
    _orquestador = AgenteOrquestador()
    print("[OK] AgenteOrquestador inicializado correctamente")
except Exception as e:
    print(f"[WARN] Error inicializando AgenteOrquestador: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check."""
    return jsonify({
        "status": "healthy",
        "service": "ms-cv-spu-multiagente",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/run', methods=['POST'])
def run():
    """
    Endpoint principal para generar propuestas comerciales.
    
    Body JSON esperado:
    {
        "nombre_empresa": "Empresa XYZ",
        "numero_empleados": 100,
        "codigo_ciiu": "4530",
        "aportes_mensuales": 5000000,
        "porcentaje_reinversion": 20,
        "enfoque_prioritario": "Seguridad Industrial",
        "correo_destinatario": "cliente@empresa.com"
    }
    """
    if not _orquestador:
        return jsonify({"error": "Orquestador no disponible"}), 503
    
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        campos_requeridos = [
            "nombre_empresa",
            "numero_empleados", 
            "codigo_ciiu",
            "aportes_mensuales",
            "porcentaje_reinversion",
            "enfoque_prioritario",
            "correo_destinatario"
        ]
        
        campos_faltantes = [c for c in campos_requeridos if c not in data or not data[c]]
        if campos_faltantes:
            return jsonify({
                "error": "Campos requeridos faltantes",
                "campos_faltantes": campos_faltantes
            }), 400
        
        # Ejecutar orquestador
        start_time = datetime.now()
        resultado = _orquestador.ejecutar(data)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        resultado["execution_time_seconds"] = execution_time
        resultado["timestamp"] = datetime.now().isoformat()
        
        return jsonify(resultado)
    
    except Exception as e:
        print(f"[ERROR] Error en /run: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    """
    Endpoint para generar solo el PDF sin ejecutar todo el flujo.
    Útil para regenerar PDFs de propuestas ya procesadas.
    """
    try:
        data = request.get_json()
        
        from src.services.pdf_generator import PDFGenerator
        pdf_generator = PDFGenerator()
        
        pdf_bytes = pdf_generator.generar_pdf(data)
        
        from flask import send_file
        import io
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Propuesta_{data.get('nombre_empresa', 'ARL')}.pdf"
        )
    
    except Exception as e:
        print(f"[ERROR] Error generando PDF: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

