"""
Carga secrets desde Google Cloud Secret Manager.
"""
import os
import json
from google.cloud import secretmanager


def load_secrets_from_json():
    """
    Carga secrets desde Secret Manager y los establece como variables de entorno.
    El secret debe ser un JSON con pares clave-valor.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "sb-iacorredores-stage")
    secret_id = "spu-multiagente"  # Nombre del secret en Secret Manager
    version_id = "latest"

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        secret_data = response.payload.data.decode("UTF-8")
        
        secrets = json.loads(secret_data)
        
        for key, value in secrets.items():
            if key not in os.environ:
                os.environ[key] = str(value)
                print(f"✅ Secret '{key}' cargado desde Secret Manager")
        
        print(f"✅ Secrets cargados exitosamente desde '{secret_id}'")
        
    except Exception as e:
        print(f"⚠️ Error cargando secrets: {e}")
        raise

