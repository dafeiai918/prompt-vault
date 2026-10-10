# -*- coding: utf-8 -*-
"""prompt-vault 测试：临时库，不发外网请求"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import prompt_vault as pv  # noqa: E402


class PromptVaultTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = pv.VAULT_PATH
        pv.VAULT_PATH = Path(self.tmp.name) / "vault.json"

    def tearDown(self):
        pv.VAULT_PATH = self._orig
        self.tmp.cleanup()

    # ---------- 纯函数 ----------

    def test_variables_extraction(self):
        content = "把 {{内容}} 翻译成 {{ 语言 }}，保留 {{内容}} 的格式"
        self.assertEqual(pv.variables_of(content), ["内容", "语言"])

    def test_render_replaces_known_keeps_unknown(self):
        out = pv.render("你好 {{名字}}，{{未填}}", {"名字": "小明"})
        self.assertEqual(out, "你好 小明，{{未填}}")

    def test_render_empty_values(self):
        self.assertEqual(pv.render("{{a}}", {"a": ""}), "")

    # ---------- 存储 ----------

    def test_init_adds_builtins_idempotent(self):
        self.assertEqual(pv.main(["init"]), 0)
        first = len(pv.load_vault()["prompts"])
        self.assertGreater(first, 5)
        self.assertEqual(pv.main(["init"]), 0)
        self.assertEqual(len(pv.load_vault()["prompts"]), first)

    def test_add_and_find(self):
        pv.main(["init"])
        self.assertEqual(pv.main(["add", "-t", "我的模板", "-c", "写点\\n东西", "-g", "测试"]), 0)
        vault = pv.load_vault()
        item = pv.find_prompt(vault, "我的模板")
        self.assertIsNotNone(item)
        self.assertIn("\n", item["content"])
        self.assertEqual(item["tags"], ["测试"])

    def test_add_from_stdin(self):
        pv.main(["init"])
        import io
        old = sys.stdin
        sys.stdin = io.StringIO("从标准输入来的内容")
        try:
            self.assertEqual(pv.main(["add", "-t", "stdin模板", "-c", "-"]), 0)
        finally:
            sys.stdin = old
        self.assertEqual(pv.find_prompt(pv.load_vault(), "stdin模板")["content"], "从标准输入来的内容")

    def test_find_by_id_and_partial_title(self):
        pv.main(["init"])
        vault = pv.load_vault()
        first = vault["prompts"][0]
        self.assertEqual(pv.find_prompt(vault, first["id"])["id"], first["id"])
        self.assertEqual(pv.find_prompt(vault, "翻译")["title"], "翻译成英文")

    def test_list_and_search(self):
        pv.main(["init"])
        self.assertEqual(pv.main(["list"]), 0)
        self.assertEqual(pv.main(["list", "翻译"]), 0)
        self.assertEqual(pv.main(["list", "绝对不存在的词xyz"]), 1)
        self.assertEqual(pv.main(["list", "-g", "编程"]), 0)

    def test_show_render_edit_remove(self):
        pv.main(["init"])
        self.assertEqual(pv.main(["add", "-t", "T", "-c", "你好 {{谁}}"]), 0)
        item = pv.find_prompt(pv.load_vault(), "T")
        self.assertEqual(pv.main(["show", item["id"]]), 0)
        self.assertEqual(pv.main(["render", item["id"], "-s", "谁=世界"]), 0)
        self.assertEqual(pv.main(["edit", item["id"], "-t", "T2"]), 0)
        self.assertEqual(pv.find_prompt(pv.load_vault(), "T2")["title"], "T2")
        self.assertEqual(pv.main(["remove", item["id"]]), 0)
        self.assertIsNone(pv.find_prompt(pv.load_vault(), "T2"))

    def test_render_missing_variable_with_copy_fails(self):
        pv.main(["init"])
        pv.main(["add", "-t", "T3", "-c", "{{缺}}"])
        item = pv.find_prompt(pv.load_vault(), "T3")
        self.assertEqual(pv.main(["render", item["id"], "--copy"]), 1)

    def test_render_bad_set_format(self):
        pv.main(["init"])
        item = pv.load_vault()["prompts"][0]
        self.assertEqual(pv.main(["render", item["id"], "-s", "格式错误"]), 1)

    def test_unknown_id_returns_error(self):
        pv.main(["init"])
        self.assertEqual(pv.main(["show", "p999"]), 1)
        self.assertEqual(pv.main(["remove", "p999"]), 1)
        self.assertEqual(pv.main(["edit", "p999"]), 1)

    def test_tags(self):
        pv.main(["init"])
        self.assertEqual(pv.main(["tags"]), 0)

    def test_export_import_roundtrip(self):
        pv.main(["init"])
        out = Path(self.tmp.name) / "share.json"
        self.assertEqual(pv.main(["export", "-o", str(out)]), 0)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertIn("prompts", data)

        pv.VAULT_PATH = Path(self.tmp.name) / "fresh.json"
        self.assertEqual(pv.main(["import", "-f", str(out)]), 0)
        self.assertEqual(len(pv.load_vault()["prompts"]), len(data["prompts"]))
        self.assertEqual(pv.main(["import", "-f", str(out)]), 0)
        self.assertEqual(len(pv.load_vault()["prompts"]), len(data["prompts"]))

    def test_import_bad_file(self):
        import tempfile as tf
        p = Path(self.tmp.name) / "bad.json"
        p.write_text("not json", encoding="utf-8")
        self.assertEqual(pv.main(["import", "-f", str(p)]), 1)
        self.assertEqual(pv.main(["import", "-f", str(Path(self.tmp.name) / "missing.json")]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
