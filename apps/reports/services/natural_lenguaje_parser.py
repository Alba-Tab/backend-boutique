import re
from datetime import datetime

def parse_query(text: str):
    result = {
        "intent": "ventas" if "venta" in text.lower() else "general",
        "filters": {},
        "order_by": None,
        "limit": None,
    }

    rango = re.search(r"(\d{1,2}) al (\d{1,2}) de (\w+)", text.lower())
    if rango:
        dia_ini, dia_fin, mes = rango.groups()
        meses = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
        }
        mes_num = meses.get(mes, "01")
        result["filters"]["fecha_inicio"] = f"2025-{mes_num}-{int(dia_ini):02d}"
        result["filters"]["fecha_fin"] = f"2025-{mes_num}-{int(dia_fin):02d}"

    # Orden
    if "monto" in text.lower():
        result["order_by"] = "monto"
    elif "cantidad" in text.lower():
        result["order_by"] = "cantidad"

    # Top N
    top = re.search(r"top\s?(\d+)|más vendidos", text.lower())
    if top:
        result["limit"] = int(top.group(1)) if top.group(1) else 10

    return result
