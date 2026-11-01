"""Conversão de arquivos e atualização com proteção contra perda de dados.

O CSV guarda texto; o JSON tem tipos. Um arquivo auxiliar .tipos.json permite
reconstruir exatamente os tipos do JSON original na conversão de volta.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .arquivos import (
    EstruturaInvalida, cabecalho_csv, gravar_csv, gravar_json,
    ler_csv, ler_json,
)


def _metadados_csv(caminho: Path) -> Path:
    return Path(str(caminho) + ".tipos.json")


def _hash_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(65536), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def _carregar_metadados(caminho: Path):
    arquivo_meta = _metadados_csv(caminho)
    if not arquivo_meta.exists():
        return None
    meta = ler_json(arquivo_meta)
    if not isinstance(meta, dict) or meta.get("versao") != 1:
        raise EstruturaInvalida("Metadados de tipos ausentes ou em formato inválido.")
    if meta.get("sha256_csv") != _hash_arquivo(caminho):
        raise EstruturaInvalida(
            "O CSV foi alterado sem atualizar os metadados de tipos; "
            "conversão cancelada para evitar perda de informações."
        )
    return meta


def _serializar_celula(valor):
    if isinstance(valor, str):
        return valor, "str"
    if valor is None:
        return "null", "null"
    if isinstance(valor, bool):
        return json.dumps(valor), "bool"
    if isinstance(valor, int):
        return json.dumps(valor), "int"
    if isinstance(valor, float):
        return json.dumps(valor, allow_nan=False), "float"
    if isinstance(valor, list):
        return json.dumps(valor, ensure_ascii=False, allow_nan=False), "list"
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False, allow_nan=False), "dict"
    raise EstruturaInvalida(f"Valor JSON não suportado: {type(valor).__name__}")


def _reconstruir_celula(texto: str, tipo: str):
    if tipo == "str":
        return texto
    if tipo == "ausente":
        return None
    if tipo not in ("null", "bool", "int", "float", "list", "dict"):
        raise EstruturaInvalida(f"Tipo desconhecido nos metadados: {tipo}")
    valor = json.loads(texto)
    tipos_validos = {
        "null": lambda v: v is None,
        "bool": lambda v: type(v) is bool,
        "int": lambda v: type(v) is int,
        "float": lambda v: type(v) is float,
        "list": lambda v: isinstance(v, list),
        "dict": lambda v: isinstance(v, dict),
    }
    if not tipos_validos[tipo](valor):
        raise EstruturaInvalida(f"Valor incompatível com o tipo {tipo} nos metadados.")
    return valor


def _validar_lista_registros(dados):
    eh_objeto = isinstance(dados, dict)
    if eh_objeto:
        registros = [dados]
    elif isinstance(dados, list):
        registros = dados
    else:
        raise EstruturaInvalida("O JSON precisa conter um objeto ou uma lista de objetos.")
    if not registros:
        raise EstruturaInvalida("Lista JSON vazia: não há colunas para exportar ao CSV.")
    if any(not isinstance(registro, dict) for registro in registros):
        raise EstruturaInvalida("Todos os itens da lista JSON precisam ser objetos.")
    campos = list(dict.fromkeys(chave for reg in registros for chave in reg))
    if not campos or any(not isinstance(chave, str) or not chave for chave in campos):
        raise EstruturaInvalida("Os objetos precisam conter campos com nomes válidos.")
    return registros, campos, "objeto" if eh_objeto else "lista"


def json_para_csv(origem: Path, destino: Path):
    origem, destino = Path(origem), Path(destino)
    if origem.resolve() == destino.resolve():
        raise EstruturaInvalida("Os caminhos de origem e destino devem ser diferentes.")
    dados = ler_json(origem)
    registros, colunas, raiz = _validar_lista_registros(dados)
    linhas, tipos = [], []
    for registro in registros:
        linha, tipo_linha = {}, {}
        for coluna in colunas:
            if coluna not in registro:
                linha[coluna], tipo_linha[coluna] = "", "ausente"
            else:
                linha[coluna], tipo_linha[coluna] = _serializar_celula(registro[coluna])
        linhas.append(linha)
        tipos.append(tipo_linha)

    gravar_csv(destino, colunas, linhas)
    metadados = {
        "versao": 1, "origem_raiz": raiz, "colunas": colunas,
        "tipos": tipos, "sha256_csv": _hash_arquivo(destino),
    }
    arquivo_meta = _metadados_csv(destino)
    gravar_json(arquivo_meta, metadados)
    print(f"[OK] JSON convertido para CSV: {destino} ({len(linhas)} registro(s)).")
    print(f"[INFO] Metadados para preservação de tipos: {arquivo_meta}")
    return destino


def csv_para_json(origem: Path, destino: Path):
    origem, destino = Path(origem), Path(destino)
    if origem.resolve() == destino.resolve():
        raise EstruturaInvalida("Os caminhos de origem e destino devem ser diferentes.")
    registros = ler_csv(origem)
    metadados = _carregar_metadados(origem)
    dados = registros
    if metadados is not None:
        colunas = cabecalho_csv(origem)
        if metadados.get("colunas") != colunas or len(metadados.get("tipos", [])) != len(registros):
            raise EstruturaInvalida("Cabeçalho ou quantidade de linhas difere dos metadados.")
        dados = []
        for linha, tipos in zip(registros, metadados["tipos"]):
            if set(tipos) != set(colunas):
                raise EstruturaInvalida("Tipos não correspondem às colunas CSV.")
            reconstruido = {}
            for campo in colunas:
                if tipos[campo] != "ausente":
                    reconstruido[campo] = _reconstruir_celula(linha[campo], tipos[campo])
            dados.append(reconstruido)
        if metadados.get("origem_raiz") == "objeto":
            if len(dados) != 1:
                raise EstruturaInvalida("Um objeto JSON deve corresponder a uma linha CSV.")
            dados = dados[0]
        elif metadados.get("origem_raiz") != "lista":
            raise EstruturaInvalida("Formato de raiz inválido nos metadados.")
    gravar_json(destino, dados)
    print(f"[OK] CSV convertido para JSON: {destino} ({len(registros)} registro(s)).")
    if metadados is None:
        print("[INFO] CSV não possui metadados; os valores foram preservados como texto.")
    else:
        print("[INFO] Tipos e estrutura JSON reconstituídos a partir dos metadados.")
    return destino


def atualizar_csv(caminho: Path, indice: int, campo: str, valor: str):
    caminho = Path(caminho)
    linhas = ler_csv(caminho)
    metadados = _carregar_metadados(caminho)
    colunas = cabecalho_csv(caminho)
    if indice < 0 or indice >= len(linhas):
        raise EstruturaInvalida("Índice da linha fora do intervalo permitido (começa em 0).")
    if campo not in colunas:
        raise EstruturaInvalida(f"Coluna não encontrada no CSV: {campo}")
    linhas[indice][campo] = valor
    gravar_csv(caminho, colunas, linhas)  # backup automático ANTES da substituição
    if metadados is not None:
        metadados["tipos"][indice][campo] = "str"
        metadados["sha256_csv"] = _hash_arquivo(caminho)
        gravar_json(_metadados_csv(caminho), metadados)
    print(f"[OK] CSV atualizado: registro {indice}, campo '{campo}' = '{valor}'.")
    return caminho


def atualizar_json(caminho: Path, indice: int, campo: str, valor: str):
    caminho = Path(caminho)
    dados = ler_json(caminho)
    registros, _, _ = _validar_lista_registros(dados)
    if indice < 0 or indice >= len(registros):
        raise EstruturaInvalida("Índice do registro fora do intervalo permitido (começa em 0).")
    if campo not in registros[indice]:
        raise EstruturaInvalida(f"Campo não encontrado no registro JSON: {campo}")
    registros[indice][campo] = valor
    gravar_json(caminho, dados)  # backup automático ANTES da substituição
    print(f"[OK] JSON atualizado: registro {indice}, campo '{campo}' = '{valor}'.")
    return caminho
