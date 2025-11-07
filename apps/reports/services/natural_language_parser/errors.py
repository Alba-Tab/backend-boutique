from rest_framework.exceptions import ValidationError

class UnknownReportError(ValidationError):
    def __init__(self, intent):
        super().__init__({
            "detail": f"Tipo de reporte no reconocido: '{intent}'",
            "available_reports": ["ventas", "clientes", "productos"]
        })