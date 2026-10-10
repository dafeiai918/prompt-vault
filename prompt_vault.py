#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prompt-vault · 提示词模板库
本地存、可搜索、带变量占位、一键复制到剪贴板、可导出分享
零依赖单文件
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

__version__ = "1.0.0"

VAULT_PATH = Path.home() / ".prompt-vault" / "vault.json"
REMOTE_URL = "https://raw.githubusercontent.com/dafeiai918/oneclickrelay-remote/main/remote.json"
FALLBACK_RECOMMEND = {"name": "好同根", "url": "https://haotogen.com/"}

VAR_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")

BUILTIN = [
    ("翻译成英文", "把下面的内容翻译成地道的英文，保持专业语气，只输出译文：\n\n{{内容}}", ["翻译", "英语"]),
    ("中文润色", "请润色下面这段中文，使其更通顺、更专业，不改变原意，只输出润色后的文本：\n\n{{内容}}", ["写作", "润色"]),
    ("长文总结", "请把下面的内容总结成 {{要点数}} 个要点，每条不超过 30 字，用无序列表输出：\n\n{{内容}}", ["总结"]),
    ("周报生成", "根据下面的工作记录，生成一份周报，结构为：本周完成 / 遇到的问题 / 下周计划。语气克制、条目化：\n\n{{工作记录}}", ["职场", "周报"]),
    ("邮件回复", "帮我回复这封邮件。要求：语气 {{语气}}，简短，先回应对方诉求再给结论。原邮件：\n\n{{原邮件}}", ["职场", "邮件"]),
    ("代码解释", "逐行解释下面的 {{语言}} 代码做了什么，指出潜在问题，用中文回答：\n\n```\n{{代码}}\n```", ["编程"]),
    ("代码重构", "重构下面这段 {{语言}} 代码，目标是 {{目标}}。只输出重构后的代码和一句话说明：\n\n```\n{{代码}}\n```", ["编程", "重构"]),
    ("SQL 生成", "根据下面的业务需求写一条 SQL（数据库是 {{数据库}}），只输出 SQL：\n\n需求：{{需求}}\n表结构：\n{{表结构}}", ["编程", "SQL"]),
    ("会议纪要", "把下面的会议记录整理成会议纪要，包含：结论、待办（负责人+截止时间）、待确认事项：\n\n{{会议记录}}", ["职场", "会议"]),
    ("检查错别字", "找出下面文本里的错别字、标点和语病，用列表列出「原文 → 建议」，不要改写其他内容：\n\n{{内容}}", ["写作", "校对"]),
    ("小红书文案", "为下面的产品写一篇小红书笔记。要求：标题带emoji、口语化、有使用场景、结尾加 5 个话题标签：\n\n产品：{{产品}}\n卖点：{{卖点}}", ["营销", "小红书"]),
    ("角色扮演面试官", "你是一位 {{岗位}} 岗位的资深面试官。请对我进行模拟面试，每次只问一个问题，我回答后给出点评再问下一个。先从自我介绍开始。", ["学习", "面试"]),
]


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"
    RED = "\033[31m"; GREEN = "\033[32m"; YELLOW = "\033[33m"; CYAN = "\033[36m"; GRAY = "\033[90m"


def _c(code: str, text: str) -> str:
    return f"{code}{text}{C.RESET}"


def enable_ansi() -> None:
    if os.name == "nt":
        os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---------------- 存储 ----------------

def empty_vault() -> dict:
    return {"version": 1, "next_id": 1, "prompts": []}


def load_vault(path: Path | None = None) -> dict:
    target = Path(path) if path else VAULT_PATH
    if target.exists():
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("prompts"), list):
                data.setdefault("next_id", len(data["prompts"]) + 1)
                return data
        except Exception:
            pass
    return empty_vault()


def save_vault(vault: dict, path: Path | None = None) -> None:
    target = Path(path) if path else VAULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(vault, ensure_ascii=False, indent=2), encoding="utf-8")


def find_prompt(vault: dict, key: str) -> dict | None:
    for item in vault["prompts"]:
        if item["id"] == key:
            return item
    key_low = key.lower()
    for item in vault["prompts"]:
        if key_low in item["title"].lower():
            return item
    return None


def variables_of(content: str) -> list[str]:
    seen, out = set(), []
    for name in VAR_RE.findall(content):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def render(content: str, values: dict) -> str:
    def repl(match):
        name = match.group(1).strip()
        return values.get(name, match.group(0))
    return VAR_RE.sub(repl, content)


def copy_to_clipboard(text: str) -> str:
    """返回 '' 表示失败，'tk'/'ps'/'pbcopy'/'xclip' 表示成功方式"""
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return "tk"
    except Exception:
        pass
    try:
        if os.name == "nt":
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", "Set-Clipboard"],
                                  input=text.encode("utf-8"), capture_output=True, timeout=20)
            if proc.returncode == 0:
                return "ps"
        elif sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True, timeout=10)
            return "pbcopy"
        else:
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"),
                           check=True, timeout=10)
            return "xclip"
    except Exception:
        pass
    return ""


def ensure_builtin(vault: dict) -> int:
    existing = {p["title"] for p in vault["prompts"]}
    added = 0
    for title, content, tags in BUILTIN:
        if title in existing:
            continue
        vault["prompts"].append({
            "id": f"p{vault['next_id']:03d}",
            "title": title, "content": content, "tags": list(tags),
            "created": time.time(), "used": 0,
        })
        vault["next_id"] += 1
        added += 1
    return added


# ---------------- 命令 ----------------

def cmd_init(args) -> int:
    vault = load_vault()
    added = ensure_builtin(vault)
    save_vault(vault)
    print(f"已初始化，添加 {added} 个内置模板，当前共 {len(vault['prompts'])} 条")
    print(_c(C.GRAY, f"库文件：{VAULT_PATH}"))
    return 0


def cmd_add(args) -> int:
    vault = load_vault()
    if not vault["prompts"]:
        ensure_builtin(vault)
    content = args.content
    if content == "-":
        content = sys.stdin.read()
    else:
        content = content.replace("\\n", "\n")
    item = {
        "id": f"p{vault['next_id']:03d}",
        "title": args.title,
        "content": content,
        "tags": [t.strip() for t in (args.tags or "").split(",") if t.strip()],
        "created": time.time(),
        "used": 0,
    }
    vault["prompts"].append(item)
    vault["next_id"] += 1
    save_vault(vault)
    print(f"已添加 {item['id']}  {item['title']}")
    vars_ = variables_of(content)
    if vars_:
        print(_c(C.GRAY, f"变量：{', '.join(vars_)}"))
    return 0


def cmd_list(args) -> int:
    vault = load_vault()
    items = vault["prompts"]
    if args.keyword:
        keyword = args.keyword.lower()
        items = [p for p in items
                 if keyword in p["title"].lower()
                 or keyword in p["content"].lower()
                 or any(keyword in t.lower() for t in p["tags"])]
    if args.tag:
        items = [p for p in items if args.tag in p["tags"]]
    if not items:
        print(_c(C.YELLOW, "没有匹配的提示词"))
        return 1
    print()
    print(_c(C.GRAY, "═" * 76))
    print(f"  {'ID':<8}{'标题':<24}{'变量':<16}{'标签':<18}")
    print(_c(C.GRAY, "─" * 76))
    for p in items:
        vars_ = variables_of(p["content"])
        var_text = ", ".join(vars_)[:14] if vars_ else "-"
        tag_text = ",".join(p["tags"])[:16] if p["tags"] else "-"
        print(f"  {p['id']:<8}{p['title'][:22]:<24}{var_text:<16}{tag_text:<18}")
    print(_c(C.GRAY, "═" * 76))
    if args.keyword or args.tag:
        print(_c(C.GRAY, f"  匹配 {len(items)} 条"))
    else:
        print(_c(C.GRAY, f"  共 {len(items)} 条"))
    return 0


def cmd_show(args) -> int:
    vault = load_vault()
    item = find_prompt(vault, args.id)
    if not item:
        print(_c(C.RED, f"未找到：{args.id}"))
        return 1
    print()
    print(_c(C.BOLD, f"  {item['id']}  {item['title']}"))
    if item["tags"]:
        print(_c(C.GRAY, f"  标签：{', '.join(item['tags'])}"))
    vars_ = variables_of(item["content"])
    if vars_:
        print(_c(C.CYAN, f"  变量：{', '.join(vars_)}"))
    print(_c(C.GRAY, "─" * 60))
    print(item["content"])
    print(_c(C.GRAY, "─" * 60))
    return 0


def cmd_render(args) -> int:
    vault = load_vault()
    item = find_prompt(vault, args.id)
    if not item:
        print(_c(C.RED, f"未找到：{args.id}"))
        return 1
    values = {}
    for pair in args.set or []:
        if "=" not in pair:
            print(_c(C.RED, f"格式应为 变量=值，收到 {pair}"))
            return 1
        key, val = pair.split("=", 1)
        values[key.strip()] = val.replace("\\n", "\n")
    missing = [v for v in variables_of(item["content"]) if v not in values]
    if missing:
        if args.copy:
            print(_c(C.RED, f"缺少变量值：{', '.join(missing)}"))
            print(_c(C.GRAY, f'示例：render {item["id"]} -s "{missing[0]}=你的内容" --copy'))
            return 1
        print(_c(C.YELLOW, f"未填变量（保持原样）：{', '.join(missing)}"))
    text = render(item["content"], values)
    if args.copy:
        way = copy_to_clipboard(text)
        if way:
            item["used"] = item.get("used", 0) + 1
            save_vault(vault)
            print(f"已复制到剪贴板（{way}）  {item['id']} {item['title']}")
            print(_c(C.GRAY, "现在可以直接粘贴到任意 AI 客户端"))
            return 0
        print(_c(C.YELLOW, "复制失败，已打印内容："))
    print(text)
    return 0


def cmd_edit(args) -> int:
    vault = load_vault()
    item = find_prompt(vault, args.id)
    if not item:
        print(_c(C.RED, f"未找到：{args.id}"))
        return 1
    if args.title:
        item["title"] = args.title
    if args.content is not None:
        item["content"] = args.content.replace("\\n", "\n")
    if args.tags is not None:
        item["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    save_vault(vault)
    print(f"已更新 {item['id']}  {item['title']}")
    return 0


def cmd_remove(args) -> int:
    vault = load_vault()
    item = find_prompt(vault, args.id)
    if not item:
        print(_c(C.RED, f"未找到：{args.id}"))
        return 1
    vault["prompts"] = [p for p in vault["prompts"] if p["id"] != item["id"]]
    save_vault(vault)
    print(f"已删除 {item['id']}  {item['title']}")
    return 0


def cmd_tags(args) -> int:
    vault = load_vault()
    counter: dict[str, int] = {}
    for p in vault["prompts"]:
        for tag in p["tags"]:
            counter[tag] = counter.get(tag, 0) + 1
    if not counter:
        print("还没有标签")
        return 0
    for tag, count in sorted(counter.items(), key=lambda kv: -kv[1]):
        print(f"  {tag:<20}{count}")
    return 0


def cmd_export(args) -> int:
    vault = load_vault()
    out = Path(args.out)
    payload = {"version": 1, "exported": time.time(), "prompts": vault["prompts"]}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已导出 {len(vault['prompts'])} 条到 {out}")
    return 0


def cmd_import(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(_c(C.RED, f"文件不存在：{path}"))
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(_c(C.RED, f"解析失败：{type(exc).__name__}"))
        return 1
    incoming = data.get("prompts") if isinstance(data, dict) else data
    if not isinstance(incoming, list):
        print(_c(C.RED, "格式不对：应为 {prompts: [...]} 或数组"))
        return 1
    vault = load_vault()
    existing = {p["title"] for p in vault["prompts"]}
    added = 0
    for item in incoming:
        title = str(item.get("title", "")).strip()
        content = item.get("content")
        if not title or not isinstance(content, str) or title in existing:
            continue
        vault["prompts"].append({
            "id": f"p{vault['next_id']:03d}",
            "title": title, "content": content,
            "tags": [str(t) for t in (item.get("tags") or [])],
            "created": time.time(), "used": 0,
        })
        vault["next_id"] += 1
        existing.add(title)
        added += 1
    save_vault(vault)
    print(f"已导入 {added} 条（跳过重名 {len(incoming) - added} 条）")
    return 0


def fetch_recommend(timeout: float = 5.0) -> dict | None:
    import urllib.request
    try:
        req = urllib.request.Request(REMOTE_URL, headers={"User-Agent": f"prompt-vault/{__version__}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        rec = data.get("recommend")
        if isinstance(rec, dict) and isinstance(rec.get("url"), str):
            return rec
    except Exception:
        pass
    return FALLBACK_RECOMMEND


def main(argv: list[str] | None = None) -> int:
    enable_ansi()
    parser = argparse.ArgumentParser(
        prog="prompt-vault", description="提示词模板库：本地存 / 搜索 / 变量填充 / 一键复制")
    parser.add_argument("-V", "--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="初始化并写入内置模板").set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="添加提示词")
    p_add.add_argument("-t", "--title", required=True)
    p_add.add_argument("-c", "--content", required=True, help="内容，用 \\n 换行，或传 - 从标准输入读")
    p_add.add_argument("-g", "--tags", default="")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="列出/搜索")
    p_list.add_argument("keyword", nargs="?", default="")
    p_list.add_argument("-g", "--tag", default="")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="查看")
    p_show.add_argument("id")
    p_show.set_defaults(func=cmd_show)

    p_render = sub.add_parser("render", help="填充变量输出/复制")
    p_render.add_argument("id")
    p_render.add_argument("-s", "--set", action="append", default=[],
                          help='变量赋值，如 -s "内容=你好"')
    p_render.add_argument("--copy", action="store_true", help="复制到剪贴板")
    p_render.set_defaults(func=cmd_render)

    p_edit = sub.add_parser("edit", help="修改")
    p_edit.add_argument("id")
    p_edit.add_argument("-t", "--title")
    p_edit.add_argument("-c", "--content")
    p_edit.add_argument("-g", "--tags")
    p_edit.set_defaults(func=cmd_edit)

    p_rm = sub.add_parser("remove", help="删除")
    p_rm.add_argument("id")
    p_rm.set_defaults(func=cmd_remove)

    sub.add_parser("tags", help="标签统计").set_defaults(func=cmd_tags)

    p_exp = sub.add_parser("export", help="导出分享")
    p_exp.add_argument("-o", "--out", default="prompts.json")
    p_exp.set_defaults(func=cmd_export)

    p_imp = sub.add_parser("import", help="导入")
    p_imp.add_argument("-f", "--file", required=True)
    p_imp.set_defaults(func=cmd_import)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        rec = fetch_recommend()
        if rec:
            print()
            print(_c(C.CYAN, f"  推荐中转站  {rec.get('name', '')}  {rec.get('url', '')}"))
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
