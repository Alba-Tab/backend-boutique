"""
Parser base mejorado con buenas prácticas y arquitectura limpia.
Usa Strategy Pattern para diferentes tipos de extracción (fechas, montos, cantidad, etc.).
"""

import re
import dateparser
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from .config import PATTERNS, ReportIntent, INTENT_KEYWORDS


# ==================== ESTRATEGIAS DE EXTRACCIÓN DE FECHAS ====================

class DateExtractor:
    """Extractor de fechas usando Strategy Pattern."""

    def __init__(self):
        self.strategies: Dict[str, Callable[..., Dict[str, str]]] = {
            "este_mes": self._extract_current_month,
            "mes_anterior": self._extract_previous_month,
            "ultimos_dias": self._extract_last_n_days,
            "ultima_semana": self._extract_last_week,
            "rango_especifico": self._extract_specific_range,
        }

    def extract(self, text: str) -> Dict[str, str]:
        """
        Extrae rangos de fechas del texto usando estrategias predefinidas.

        Args:
            text: Texto en lenguaje natural.

        Returns:
            Dict con fecha_inicio y fecha_fin en formato ISO.
        """
        text_lower = text.lower()

        # Buscar estrategias definidas en PATTERNS['FECHA']
        for pattern_name, pattern_regex in PATTERNS["FECHA"].items():
            match = re.search(pattern_regex, text_lower)
            if not match:
                continue

            # Si el patrón requiere argumento (como rango o últimos N días)
            if pattern_name == "rango_especifico":
                return self.strategies[pattern_name](match)
            if pattern_name == "ultimos_dias":
                dias = int(match.group(1)) if match.groups() else 7
                return self.strategies[pattern_name](dias)
            # Otras estrategias simples
            return self.strategies[pattern_name]()

        return {}

    # -------- Estrategias concretas --------

    def _extract_current_month(self) -> Dict[str, str]:
        """Extrae el mes actual completo."""
        now = datetime.now()
        inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fin_mes = (
            now.replace(month=12, day=31, hour=23, minute=59, second=59)
            if now.month == 12
            else (now.replace(month=now.month + 1, day=1) - timedelta(days=1)).replace(
                hour=23, minute=59, second=59
            )
        )
        return {
            "fecha_inicio": inicio_mes.date().isoformat(),
            "fecha_fin": fin_mes.date().isoformat(),
        }

    def _extract_previous_month(self) -> Dict[str, str]:
        """Extrae el mes anterior completo."""
        now = datetime.now()
        primer_dia_mes_anterior = (now.replace(day=1) - timedelta(days=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        ultimo_dia_mes_anterior = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(seconds=1)
        return {
            "fecha_inicio": primer_dia_mes_anterior.date().isoformat(),
            "fecha_fin": ultimo_dia_mes_anterior.date().isoformat(),
        }

    def _extract_last_n_days(self, dias: int = 7) -> Dict[str, str]:
        """Extrae los últimos N días."""
        now = datetime.now()
        fecha_inicio = now - timedelta(days=dias)
        return {
            "fecha_inicio": fecha_inicio.date().isoformat(),
            "fecha_fin": now.date().isoformat(),
        }

    def _extract_last_week(self) -> Dict[str, str]:
        """Extrae la última semana (7 días)."""
        return self._extract_last_n_days(7)

    def _extract_specific_range(self, match: re.Match) -> Dict[str, str]:
        """Extrae un rango específico como '1 al 15 de enero'."""
        d1, d2, mes = match.groups()
        fecha1 = dateparser.parse(f"{d1} de {mes} 2025")
        fecha2 = dateparser.parse(f"{d2} de {mes} 2025")
        if fecha1 and fecha2:
            return {
                "fecha_inicio": fecha1.date().isoformat(),
                "fecha_fin": fecha2.date().isoformat(),
            }
        return {}


# ==================== EXTRACTORES FUNCIONALES ====================

def extract_dates(text: str) -> Dict[str, str]:
    """Extrae rangos de fechas del texto usando DateExtractor."""
    extractor = DateExtractor()
    return extractor.extract(text)


def extract_amount_filters(text: str) -> Dict[str, float]:
    """Extrae filtros de montos usando expresiones regulares."""
    text_lower = text.lower()
    filters = {}

    extraction_strategies = {
        "entre": lambda m: {"monto_min": float(m.group(1)), "monto_max": float(m.group(2))},
        "mayor_a": lambda m: {"monto_min": float(m.group(1))},
        "menor_a": lambda m: {"monto_max": float(m.group(1))},
    }

    for pattern_name, pattern_regex in PATTERNS["MONTO"].items():
        match = re.search(pattern_regex, text_lower)
        if match and pattern_name in extraction_strategies:
            filters.update(extraction_strategies[pattern_name](match))
            if pattern_name == "entre":
                break
    return filters


def extract_quantity_filters(text: str) -> Dict[str, int]:
    """Extrae filtros de cantidad vendida."""
    text_lower = text.lower()
    filters = {}

    extraction_map = {"mayor_a": "cantidad_min", "menor_a": "cantidad_max"}

    for pattern_name, filter_key in extraction_map.items():
        if pattern_name in PATTERNS["CANTIDAD"]:
            match = re.search(PATTERNS["CANTIDAD"][pattern_name], text_lower)
            if match:
                filters[filter_key] = int(match.group(1))
    return filters


def extract_limit(text: str) -> Optional[int]:
    """Extrae el límite de resultados del texto."""
    text_lower = text.lower()

    match = re.search(PATTERNS["LIMITE"]["top_n"], text_lower)
    if match:
        return int(match.group(1))

    for palabra, numero in PATTERNS["LIMITE"]["numeros_texto"].items():
        if palabra in text_lower:
            return numero

    if "más vendidos" in text_lower or "mas vendidos" in text_lower:
        return 10
    if "menos vendidos" in text_lower:
        return 10
    return None


def extract_order(text: str) -> Optional[str]:
    """Extrae el orden de clasificación del texto."""
    text_lower = text.lower()
    order_mapping = {
        "descendente": {"monto|total|precio": "-total", "cantidad|vendido": "-cantidad"},
        "ascendente": {"monto|total|precio": "total", "cantidad|vendido": "cantidad"},
    }

    for direction, patterns in order_mapping.items():
        if re.search(PATTERNS["ORDEN"][direction], text_lower):
            for field_pattern, order_value in patterns.items():
                if re.search(field_pattern, text_lower):
                    return order_value
            return "-total" if direction == "descendente" else "total"

    if "monto" in text_lower or "total" in text_lower:
        return "-total"
    if "cantidad" in text_lower:
        return "-cantidad"
    return None


def detect_report_type(text: str) -> Optional[ReportIntent]:
    """Detecta el tipo de reporte basándose en palabras clave usando diccionario."""
    text_lower = text.lower()

    for intent, patterns in INTENT_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent

    if "venta" in text_lower:
        if re.search(r"mayor(?:es)?\s+(?:a|que)\s+\d+", text_lower) and re.search(
            r"menor(?:es)?\s+(?:a|que)\s+\d+", text_lower
        ):
            return ReportIntent.VENTAS_ENTRE_MONTOS
        elif re.search(r"mayor(?:es)?\s+(?:a|que)\s+\d+", text_lower):
            return ReportIntent.VENTAS_MAYORES_A
        elif re.search(r"menor(?:es)?\s+(?:a|que)\s+\d+", text_lower):
            return ReportIntent.VENTAS_MENORES_A
        return ReportIntent.VENTAS

    return None
