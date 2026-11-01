"""Testes automatizados com arquivos temporários (sem alterar os dados de exemplo)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.persistencia import (  # noqa: E402
    atualizar_csv, atualizar_json, csv_para_json, json_para_csv, ler_csv, ler_json,
)
from src.persistencia.arquivos import EstruturaInvalida  # noqa: E402


class TestesPersistencia(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def arquivo(self, nome, conteudo):
        caminho = self.dir / nome
        with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
            arquivo.write(conteudo)
        return caminho

    def backups(self, nome):
        return [p for p in self.dir.glob(f"{nome}.*.bak") if not p.name.startswith(nome + ".tipos.json.")]

    def test_csv_para_json_preserva_textos_e_zeros_iniciais(self):
        original = self.arquivo("entrada.csv", "id,nome\n001,João\n002,Ana\n")
        saida = self.dir / "saida.json"
        csv_para_json(original, saida)
        self.assertEqual(ler_json(saida), [{"id": "001", "nome": "João"}, {"id": "002", "nome": "Ana"}])

    def test_json_csv_json_preserva_tipos_e_estrutura(self):
        registros = [
            {"id": 1, "preco": 2.5, "ativo": True, "nome": "Érica", "tags": ["a", "b"], "extra": None},
            {"id": 2, "preco": 0.0, "ativo": False, "nome": "", "tags": [], "objeto": {"a": 1}},
        ]
        original = self.arquivo("original.json", json.dumps(registros, ensure_ascii=False))
        intermediario = self.dir / "saida.csv"
        resultado = self.dir / "volta.json"
        json_para_csv(original, intermediario)
        self.assertTrue((self.dir / "saida.csv.tipos.json").exists())
        csv_para_json(intermediario, resultado)
        self.assertEqual(ler_json(resultado), registros)

    def test_json_objeto_unico_preservado(self):
        origem = self.arquivo("um.json", '{"nome":"Teste","n":4}')
        csv = self.dir / "um.csv"
        json_para_csv(origem, csv)
        saida = self.dir / "volta.json"
        csv_para_json(csv, saida)
        self.assertEqual(ler_json(saida), {"nome": "Teste", "n": 4})

    def test_backup_precede_atualizacao_csv(self):
        origem = self.arquivo("clientes.csv", "nome,cidade\nAna,Balsas\n")
        atualizar_csv(origem, 0, "cidade", "Imperatriz")
        self.assertEqual(ler_csv(origem)[0]["cidade"], "Imperatriz")
        backups = self.backups("clientes.csv")
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "nome,cidade\nAna,Balsas\n")

    def test_backup_precede_atualizacao_json(self):
        origem = self.arquivo("original.json", '[{"nome":"Ana"}]')
        atualizar_json(origem, 0, "nome", "João")
        self.assertEqual(ler_json(origem)[0]["nome"], "João")
        self.assertEqual(len(self.backups("original.json")), 1)

    def test_backup_antes_de_substituir_saida_existente(self):
        origem = self.arquivo("dados.csv", "id\n1\n")
        saida = self.arquivo("saida.json", '{"antigo":true}')
        csv_para_json(origem, saida)
        self.assertEqual(len(self.backups("saida.json")), 1)

    def test_csv_editado_sem_metadados_atualizados_e_bloqueado(self):
        original = self.arquivo("origem.json", '[{"n":12}]')
        intermediario = self.dir / "saida.csv"
        json_para_csv(original, intermediario)
        with open(intermediario, "a", encoding="utf-8") as arquivo:
            arquivo.write("13\n")
        with self.assertRaisesRegex(EstruturaInvalida, "alterado"):
            csv_para_json(intermediario, self.dir / "outra.json")

    def test_atualizacao_csv_com_metadados_mantem_integridade(self):
        origem = self.arquivo("origem.json", '[{"id":1,"nome":"Ana"}]')
        csv = self.dir / "saida.csv"
        json_para_csv(origem, csv)
        atualizar_csv(csv, 0, "nome", "Maria")
        saida = self.dir / "volta.json"
        csv_para_json(csv, saida)
        self.assertEqual(ler_json(saida), [{"id": 1, "nome": "Maria"}])
        self.assertEqual(len(self.backups("saida.csv")), 1)
        self.assertEqual(len(self.backups("saida.csv.tipos.json")), 1)

    def test_arquivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            ler_csv(self.dir / "nao_existe.csv")

    def test_codificacao_invalida(self):
        caminho = self.dir / "latin1.csv"
        with open(caminho, "wb") as arquivo:
            arquivo.write(b"nome\nJo\xe3o\n")
        with self.assertRaises(UnicodeDecodeError):
            ler_csv(caminho)

    def test_csv_com_colunas_a_mais_e_rejeitado(self):
        caminho = self.arquivo("invalido.csv", "a,b\n1,2,3\n")
        with self.assertRaises(EstruturaInvalida):
            ler_csv(caminho)

    def test_json_invalido(self):
        caminho = self.arquivo("invalido.json", "{JSON incompleto")
        with self.assertRaises(json.JSONDecodeError):
            ler_json(caminho)

    def test_registro_fora_do_intervalo_nao_altera_arquivo(self):
        origem = self.arquivo("entrada.csv", "id\n1\n")
        with self.assertRaises(EstruturaInvalida):
            atualizar_csv(origem, 10, "id", "x")
        self.assertEqual(len(self.backups("entrada.csv")), 0)
        self.assertEqual(origem.read_text(encoding="utf-8"), "id\n1\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
