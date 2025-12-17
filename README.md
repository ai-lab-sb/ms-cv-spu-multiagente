# MS-CV-SPU-MULTIAGENTE

Sistema Único de Propuesta (SPU) - Multiagente para ARL Seguros Bolívar.

Este microservicio orquesta múltiples agentes de IA para generar propuestas comerciales personalizadas de ARL (Administradora de Riesgos Laborales).

## Descripción

El sistema recibe información básica de una empresa y genera automáticamente una propuesta comercial completa que incluye:

- **Perfil de riesgo** basado en el código CIIU
- **Productos obligatorios** según obligaciones legales
- **Productos prioritarios** según el enfoque de la empresa
- **Valores agregados** sin costo adicional
- **PDF profesional** listo para enviar al cliente

## Arquitectura

El sistema utiliza una arquitectura de **agentes especializados**:

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTE ORQUESTADOR                       │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Recolector  │→ │   Perfil    │→ │     Selector        │ │
│  │   Datos     │  │   Riesgo    │  │    Productos        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                              ↓              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Documentador + PDF Generator           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Agentes

| Agente | Función |
|--------|---------|
| **Recolector** | Valida los datos de entrada del cliente |
| **Perfil de Riesgo** | Identifica clase de riesgo, riesgos generales y obligaciones legales |
| **Selector de Productos** | Selecciona productos del catálogo según perfil y presupuesto |
| **Documentador** | Consolida toda la información en estructura JSON |
| **PDF Generator** | Genera el documento PDF profesional |


## Estructura del Proyecto

```
ms-cv-spu-multiagente/
├── main.py                 # Aplicación Flask principal
├── load_secrets.py         # Carga de secrets desde GCP
├── requirements.txt        # Dependencias Python
├── Dockerfile              # Configuración Docker
├── cloudbuild.yaml         # CI/CD para Cloud Build
├── src/
│   ├── agents/
│   │   └── orquestador.py  # Agente orquestador principal
│   ├── prompts/
│   │   ├── prompt_recolector.py
│   │   ├── prompt_perfil_riesgo.py
│   │   ├── prompt_selector_productos.py
│   │   └── prompt_documentador.py
│   └── services/
│       ├── llm_service.py      # Servicio de LLM (Gemini)
│       ├── catalogo_service.py # Catálogo de productos Automy
│       └── pdf_generator.py    # Generador de PDFs
└── templates/
    └── propuesta_comercial.html  # Template del PDF
```

## Endpoints

### `GET /health`
Health check del servicio.

```json
{
  "status": "healthy",
  "service": "ms-cv-spu-multiagente",
  "timestamp": "2025-12-17T10:00:00"
}
```

### `POST /run`
Genera una propuesta comercial completa.

**Request:**
```json
{
  "nombre_empresa": "Empresa XYZ S.A.S.",
  "numero_empleados": 200,
  "codigo_ciiu": "1630",
  "aportes_mensuales": 11600000,
  "porcentaje_reinversion": 18,
  "enfoque_prioritario": "Seguridad Industrial",
  "correo_destinatario": "cliente@empresa.com"
}
```

**Response:**
```json
{
  "status": "success",
  "propuesta": {
    "propuesta_comercial": {
      "informacion_cliente": {...},
      "perfil_riesgo": {...},
      "presupuesto": {...},
      "productos_obligatorios": [...],
      "productos_prioritarios": [...],
      "valores_agregados": [...]
    },
    "metadatos": {
      "fecha_generacion": "2025-12-17",
      "version": "1.0"
    }
  },
  "pdf_generado": true,
  "execution_time_seconds": 45.2
}
```

### `POST /generar-pdf`
Genera solo el PDF desde datos ya procesados.

## Configuración

### Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | ID del proyecto GCP | `sb-iacorredores-dev` |
| `GOOGLE_CLOUD_LOCATION` | Región de GCP | `us-central1` |
| `PORT` | Puerto del servidor | `8080` |

### Desarrollo Local

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Autenticarse con Google Cloud:
```bash
gcloud auth application-default login
```

3. Ejecutar localmente:
```bash
python main_local.py
```

## Despliegue

El proyecto se despliega automáticamente en **Google Cloud Run** mediante Cloud Build triggers conectados a las ramas del repositorio.

| Rama | Entorno | Proyecto GCP |
|------|---------|--------------|
| `dev` | Desarrollo | `sb-iacorredores-dev` |

## Catálogo de Productos

El sistema consume el catálogo de productos ARL desde la API de **Automy**, que incluye:

- **DIFERENCIAL** - Programas especializados
- **VALOR AGREGADO** - Servicios sin costo
- **Profesionales** - Servicios especializados
- **Programa de Prevención** - Prevención estructurada
- **HIGIENE** - Higiene industrial
- **Medicina Preventiva** - Servicios médicos
- **Laboratorio Clínico** - Exámenes y análisis

