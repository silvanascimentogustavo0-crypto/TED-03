"""Utilitários para persistência segura de dados estruturados em CSV e JSON."""

from .servico import (
    ler_csv,
    ler_json,
    csv_para_json,
    json_para_csv,
    atualizar_csv,
    atualizar_json,
)

__all__ = [
    "ler_csv", "ler_json", "csv_para_json", "json_para_csv",
    "atualizar_csv", "atualizar_json",
]
