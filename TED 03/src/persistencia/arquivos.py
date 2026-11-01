"""Leitura, escrita atômica e cópias de segurança de arquivos."""
from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class EstruturaInvalida(ValueError):
    """Dados incompatíveis com a estrutura esperada."""


def criar_backup(caminho: Path) -> Path | None:
    """Copia um arquivo existente ANTES de alterá-lo. Falhas impedem a escrita."""
    caminho = Path(caminho)
    if not caminho.exists():
        return None  # Criação de arquivo novo não destrói dados anteriores.
    if not caminho.is_file():
        raise EstruturaInvalida(f"O destino não é um arquivo: {caminho}")

    data = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino = caminho.with_name(f"{caminho.name}.{data}.{uuid4().hex[:8]}.bak")
    try:
        with open(caminho, "rb") as origem, open(destino, "xb") as copia:
            shutil.copyfileobj(origem, copia)
    except OSError:
        destino.unlink(missing_ok=True)
        raise
    print(f"[BACKUP] Cópia anterior preservada em: {destino}")
    return destino


def _escrever_atomicamente(caminho: Path, escritor) -> Path | None:
    """Cria backup, grava arquivo temporário e publica com troca atômica."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(f".{caminho.name}.{uuid4().hex}.tmp")
    try:
        backup = criar_backup(caminho)
        with open(temporario, "w", encoding="utf-8", newline="") as arquivo:
            escritor(arquivo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
        return backup
    finally:
        temporario.unlink(missing_ok=True)


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    caminho = Path(caminho)
    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        cabecalho = leitor.fieldnames
        if cabecalho is None:
            raise EstruturaInvalida("CSV sem cabeçalho. Informe um arquivo CSV válido.")
        if len(set(cabecalho)) != len(cabecalho) or any(not x for x in cabecalho):
            raise EstruturaInvalida("CSV com nomes de colunas vazios ou repetidos.")
        linhas = []
        for numero, registro in enumerate(leitor, start=2):
            if None in registro or any(valor is None for valor in registro.values()):
                raise EstruturaInvalida(
                    f"CSV com quantidade incorreta de colunas na linha {numero}."
                )
            linhas.append(dict(registro))
        return linhas


def ler_json(caminho: Path):
    caminho = Path(caminho)
    with open(caminho, "r", encoding="utf-8-sig") as arquivo:
        def rejeitar_constante(valor):
            raise EstruturaInvalida(f"Número JSON não permitido: {valor}")
        return json.load(arquivo, parse_constant=rejeitar_constante)


def gravar_json(caminho: Path, conteudo) -> Path | None:
    def escritor(arquivo):
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2, allow_nan=False)
        arquivo.write("\n")
    return _escrever_atomicamente(Path(caminho), escritor)


def gravar_csv(caminho: Path, colunas: list[str], linhas: list[dict[str, str]]) -> Path | None:
    if not colunas or len(colunas) != len(set(colunas)):
        raise EstruturaInvalida("É necessário um cabeçalho CSV não vazio e sem repetições.")

    def escritor(arquivo):
        escritor_csv = csv.DictWriter(arquivo, fieldnames=colunas, extrasaction="raise")
        escritor_csv.writeheader()
        escritor_csv.writerows(linhas)
    return _escrever_atomicamente(Path(caminho), escritor)


def cabecalho_csv(caminho: Path) -> list[str]:
    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        try:
            return next(leitor)
        except StopIteration as exc:
            raise EstruturaInvalida("CSV sem cabeçalho.") from exc
