"""
Servicio para generar PDFs usando WeasyPrint.
Usa el template HTML similar al de Prospektor-pdf.
"""
import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


class PDFGenerator:
    """Generador de PDFs para propuestas comerciales."""
    
    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # Buscar directorio de templates
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            template_dir = os.path.join(base_dir, "templates")
        
        self._template_dir = template_dir
        self._base_dir = os.path.dirname(template_dir)  # Directorio raíz del proyecto
        self._static_dir = os.path.join(self._base_dir, "static")
        self._logo_path = os.path.join(self._static_dir, "bolivar-logo.png")
        
        self._env = Environment(loader=FileSystemLoader(template_dir))
        
        # Registrar filtros personalizados
        self._env.filters['format_currency'] = self._format_currency
        self._env.filters['safe_value'] = self._safe_value
        
        print(f"[OK] PDFGenerator inicializado (templates: {template_dir})")
        print(f"[OK] Logo path: {self._logo_path}")
    
    @staticmethod
    def _format_currency(value, default='$0'):
        """Formatea un número como moneda colombiana."""
        try:
            n = float(value)
            return f"${n:,.0f}".replace(",", ".")
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_value(value, default='N/A'):
        """Retorna un valor por defecto si el valor es vacío o None."""
        if value is None or value == '' or value == 'N/A':
            return default
        return str(value)
    
    def generar_pdf(self, data: Dict[str, Any]) -> bytes:
        """
        Genera un PDF a partir de los datos de la propuesta.
        
        Args:
            data: Diccionario con datos de la propuesta comercial
            
        Returns:
            Bytes del PDF generado
        """
        try:
            # Cargar template
            template = self._env.get_template("propuesta_comercial.html")
            
            # Preparar datos para el template
            template_data = self._preparar_datos_template(data)
            
            # Renderizar HTML
            html_string = template.render(template_data)
            
            # Generar PDF
            pdf_bytes = HTML(
                string=html_string,
                base_url=self._template_dir
            ).write_pdf()
            
            print(f"[OK] PDF generado ({len(pdf_bytes)} bytes)")
            return pdf_bytes
            
        except Exception as e:
            print(f"[ERROR] Error generando PDF: {e}")
            raise
    
    def _preparar_datos_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara los datos para el template HTML."""
        propuesta = data.get("propuesta_comercial", data)
        metadatos = data.get("metadatos", {})
        
        cliente = propuesta.get("informacion_cliente", {})
        perfil = propuesta.get("perfil_riesgo", {})
        presupuesto = propuesta.get("presupuesto", {})
        obligatorios = propuesta.get("productos_obligatorios", [])
        prioritarios = propuesta.get("productos_prioritarios", [])
        valores = propuesta.get("valores_agregados", [])
        
        # Usar file:// para que WeasyPrint pueda acceder al logo
        logo_path = f"file:///{self._logo_path.replace(os.sep, '/')}"
        
        return {
            "cliente": cliente,
            "perfil": perfil,
            "presupuesto": presupuesto,
            "obligatorios": obligatorios,
            "prioritarios": prioritarios,
            "valores": valores,
            "meta": metadatos,
            "nombre_empresa": cliente.get("nombre_empresa", ""),
            "logo_path": logo_path,
        }
    
    def guardar_pdf(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Genera y guarda un PDF en disco.
        
        Args:
            data: Diccionario con datos de la propuesta
            output_path: Ruta donde guardar el PDF
            
        Returns:
            Ruta del archivo guardado
        """
        pdf_bytes = self.generar_pdf(data)
        
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"[OK] PDF guardado en: {output_path}")
        return output_path

