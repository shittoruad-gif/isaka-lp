#!/usr/bin/env python3
"""
index.html の日本語テキストに文節区切り(<wbr>)を埋め込む。

なぜ必要か:
  CSSの word-break:auto-phrase は Chrome 系しか対応しておらず、iOS Safari では
  文節を無視した位置で折り返される。そこで BudouX(Googleの日本語文節分割)で
  あらかじめ <wbr> を埋め込み、word-break:keep-all と併用して
  「<wbr> の位置でしか折り返さない」状態を全ブラウザで作る。

使い方:
  index.html の本文テキストを編集したら、このスクリプトを再実行すること。
  既存の <wbr> / <span class="nb"> は自動で除去してから付け直すので何度でも実行可。
    python3 -m venv .venv-budoux && .venv-budoux/bin/pip install budoux
    .venv-budoux/bin/python tools/apply-linebreaks.py
"""
import io, re, sys
from html.parser import HTMLParser
import budoux

P = budoux.load_default_japanese_parser()
JP    = re.compile(r'[぀-ゟ゠-ヿ一-鿿]')
HIRA  = re.compile(r'^[぀-ゟー]+$')
CLOSE = re.compile(r'[」』）】]')
SKIP  = {'script', 'style', 'title', 'textarea'}
is_hira = lambda ch: 'ぁ' <= ch <= 'ゟ'


def segment(text):
    """BudouX の分割を、日本語として不自然な切れ目が出ないよう補正する。"""
    chunks = [c for c in P.parse(text) if c]
    out, i = [], 0
    while i < len(chunks):
        x = chunks[i]; i += 1
        # 行頭に来てはいけない記号は前の文節へ寄せる
        while x and x[0] in '・、。' and out:
            out[-1] += x[0]; x = x[1:]
        if not x:
            continue
        # 3文字以下の純ひらがな断片は次と結合（「ほぐ」+「しても、」対策）
        while HIRA.fullmatch(x) and len(x) <= 3 and i < len(chunks) and len(x) + len(chunks[i]) <= 14:
            x += chunks[i]; i += 1
        if out and re.fullmatch(r'[、。・]+', x):
            out[-1] += x; continue
        # ひらがな同士の境界は語中の可能性が高いので結合（「と」+「して」対策）
        if out and is_hira(out[-1][-1]) and is_hira(x[0]) and len(out[-1]) + len(x) <= 16:
            out[-1] += x; continue
        out.append(x)
    return out


class Rewriter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.buf, self.skip = [], 0
        self.nodes = self.wbr = self.nb = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP: self.skip += 1
        self.buf.append(self.get_starttag_text())
    def handle_startendtag(self, tag, attrs): self.buf.append(self.get_starttag_text())
    def handle_endtag(self, tag):
        if tag in SKIP and self.skip: self.skip -= 1
        self.buf.append(f'</{tag}>')
    def handle_comment(self, d): self.buf.append(f'<!--{d}-->')
    def handle_decl(self, d): self.buf.append(f'<!{d}>')
    def handle_entityref(self, n): self.buf.append(f'&{n};')
    def handle_charref(self, n): self.buf.append(f'&#{n};')

    def handle_data(self, data):
        if self.skip or not JP.search(data) or len(data.strip()) < 6:
            self.buf.append(data); return
        lead  = data[:len(data) - len(data.lstrip())]
        trail = data[len(data.rstrip()):]
        parts = segment(data.strip())
        if len(parts) < 2:
            self.buf.append(data); return
        self.nodes += 1; self.wbr += len(parts) - 1

        def wrap(p):
            # 閉じ括弧の直後はブラウザが勝手に折り返すので、短い文節だけ nowrap で保護
            if CLOSE.search(p) and len(p) <= 14:
                self.nb += 1
                return f'<span class="nb">{p}</span>'
            return p

        self.buf.append(lead + '<wbr>'.join(wrap(p) for p in parts) + trail)


def main(path='index.html'):
    src = io.open(path, encoding='utf-8').read()
    # 前回の結果を除去してから付け直す（何度実行しても同じ結果になるように）
    src = src.replace('<wbr>', '')
    src = re.sub(r'<span class="nb">(.*?)</span>', r'\1', src, flags=re.S)

    r = Rewriter(); r.feed(src)
    io.open(path, 'w', encoding='utf-8').write(''.join(r.buf))
    print(f'{path}: {r.nodes}箇所に適用 / <wbr> {r.wbr}個 / nowrap {r.nb}個')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
