"""Interface de linha de comando para o projeto TED 03.

Exemplo:
    python main.py csv-para-json dados/clientes.csv saida/clientes.json
"""
import argparse
import json
import sys
from pathlib import Path

from src.persistencia import (
    atualizar_csv, atualizar_json, csv_para_json, json_para_csv, ler_csv, ler_json,
)
from src.persistencia.arquivos import EstruturaInvalida


def configurar_argumentos():
    parser = argparse.ArgumentParser(
        description="TED 03 - Gerenciador seguro de arquivos CSV e JSON"
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    for nome in ("ler-csv", "ler-json"):
        sub = comandos.add_parser(nome, help=f"Exibe os registros do arquivo {nome[4:].upper()}")
        sub.add_argument("arquivo", type=Path, help="Caminho do arquivo de entrada")
    for nome in ("csv-para-json", "json-para-csv"):
        sub = comandos.add_parser(nome, help="Converte preservando dados e informações")
        sub.add_argument("origem", type=Path)
        sub.add_argument("destino", type=Path)
    for nome in ("atualizar-csv", "atualizar-json"):
        sub = comandos.add_parser(nome, help="Atualiza e cria backup automático")
        sub.add_argument("arquivo", type=Path)
        sub.add_argument("indice", type=int, help="Índice do registro, iniciando em 0")
        sub.add_argument("campo", help="Nome da coluna/campo")
        sub.add_argument("valor", help="Novo valor textual")
    return parser


def executar(args):
    if args.comando == "ler-csv":
        registros = ler_csv(args.arquivo)
        print(f"[OK] CSV lido: {args.arquivo} ({len(registros)} registro(s)).")
        print(json.dumps(registros, ensure_ascii=False, indent=2))
    elif args.comando == "ler-json":
        registros = ler_json(args.arquivo)
        print(f"[OK] JSON lido: {args.arquivo}.")
        print(json.dumps(registros, ensure_ascii=False, indent=2))
    elif args.comando == "csv-para-json":
        csv_para_json(args.origem, args.destino)
    elif args.comando == "json-para-csv":
        json_para_csv(args.origem, args.destino)
    elif args.comando == "atualizar-csv":
        atualizar_csv(args.arquivo, args.indice, args.campo, args.valor)
    elif args.comando == "atualizar-json":
        atualizar_json(args.arquivo, args.indice, args.campo, args.valor)


def main():
    parser = configurar_argumentos()
    args = parser.parse_args()
    try:
        executar(args)
    except FileNotFoundError as exc:
        print(f"[ERRO] Arquivo não encontrado: {exc.filename}", file=sys.stderr)
        return 1
    except PermissionError as exc:
        print(f"[ERRO] Permissão negada ao acessar: {exc.filename}", file=sys.stderr)
        return 1
    except UnicodeError:
        print("[ERRO] Codificação incompatível: utilize arquivos UTF-8.", file=sys.stderr)
        return 1
    except (EstruturaInvalida, ValueError, json.JSONDecodeError) as exc:
        print(f"[ERRO] Dados inválidos: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"[ERRO] Falha de entrada/saída: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
