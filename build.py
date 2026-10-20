#!/usr/bin/env python3
"""从书稿 Markdown 生成在线阅读页 index.html（GitHub Pages 用）。

用法：python3 build.py
输入：同目录下的《北京七年，终将离开.md》
输出：index.html（单文件，正文全部内嵌）
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
BOOK_MD = ROOT / "北京七年，终将离开.md"

INLINE = re.compile(r"(\*\*.+?\*\*|!\[([^\]]*)\]\(([^)]+)\)|\[([^\]]+)\]\(([^)]+)\))")


def inline_md(text: str) -> str:
    out, pos = [], 0
    for m in INLINE.finditer(text):
        out.append(html.escape(text[pos:m.start()]))
        if m.group(0).startswith("**"):
            out.append(f"<strong>{html.escape(m.group(0)[2:-2])}</strong>")
        elif m.group(0).startswith("!["):
            alt, src = html.escape(m.group(2)), html.escape(m.group(3))
            out.append(
                f'<figure><img src="{src}" alt="{alt}" loading="lazy">'
                f"<figcaption>{alt}</figcaption></figure>"
            )
        else:
            out.append(f'<a href="{html.escape(m.group(5))}" target="_blank" rel="noopener">'
                       f"{html.escape(m.group(4))}</a>")
        pos = m.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def body_to_html(body: str) -> str:
    blocks, buf = [], []
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("## "):
            if buf:
                blocks.append("<p>" + inline_md("".join(buf)) + "</p>")
                buf = []
            blocks.append("<h2>" + inline_md(s[3:]) + "</h2>")
        elif s == "---":
            if buf:
                blocks.append("<p>" + inline_md("".join(buf)) + "</p>")
                buf = []
            blocks.append('<div class="sep" aria-hidden="true">· · ·</div>')
        elif not s:
            if buf:
                blocks.append("<p>" + inline_md("".join(buf)) + "</p>")
                buf = []
        else:
            buf.append(s)
    if buf:
        blocks.append("<p>" + inline_md("".join(buf)) + "</p>")
    return "\n".join(blocks)


def parse_chapters(md: str):
    chapters = []
    for part in re.split(r"(?m)^# ", md)[1:]:
        title, _, body = part.partition("\n")
        chapters.append((title.strip(), body_to_html(body)))
    return chapters


def toc_item(idx: int, title: str) -> str:
    if "｜" in title:
        no, _, rest = title.partition("｜")
        return (f'<a class="toc-item" href="#c{idx}" id="ti{idx}">'
                f'<span class="no">{html.escape(no)}</span>'
                f'<span class="ti">{html.escape(rest)}</span></a>')
    return (f'<a class="toc-item" href="#c{idx}" id="ti{idx}">'
            f'<span class="no">◇</span><span class="ti">{html.escape(title)}</span></a>')


def article(idx: int, title: str, body_html: str) -> str:
    if "｜" in title:
        no, _, rest = title.partition("｜")
        head = f'<div class="ch-no">{html.escape(no)}</div><h1>{html.escape(rest)}</h1>'
    else:
        head = f"<h1>{html.escape(title)}</h1>"
    return f'<article class="ch" id="c{idx}" data-title="{html.escape(title)}">{head}\n{body_html}</article>'


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>北京七年，终将离开 · 在线阅读</title>
<meta name="description" content="七帅自传：一个设计师的七年北漂全记录，9.8 万字，24 章，开源全书。">
<meta property="og:title" content="北京七年，终将离开">
<meta property="og:description" content="一个设计师的七年北漂全记录，开源全书。">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23d68f2e'/%3E%3Ctext x='32' y='44' font-size='34' text-anchor='middle' fill='%23fffdf9' font-family='serif'%3E北%3C/text%3E%3C/svg%3E">
<style>
:root{
  --bg:#f6f3ed; --surface:#fffdf8; --text:#3a352e; --muted:#8b8477;
  --accent:#c98a2b; --accent-soft:#f4e7cf; --line:#e9e3d6;
  --shadow:0 1px 2px rgba(70,58,35,.05),0 6px 20px rgba(70,58,35,.07);
}
[data-theme="dark"]{
  --bg:#1b1a17; --surface:#25231f; --text:#c9c4b8; --muted:#7e7869;
  --accent:#dfa64b; --accent-soft:#38321f; --line:#343029;
  --shadow:0 1px 2px rgba(0,0,0,.35),0 6px 20px rgba(0,0,0,.28);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  background:var(--bg); color:var(--text);
  font-family:Georgia,"Songti SC","Noto Serif CJK SC","STSong",SimSun,serif;
  transition:background .25s,color .25s;
}
button{font-family:inherit;cursor:pointer}
/* ── 顶栏 ─────────────────────────── */
#bar{
  position:fixed;inset:0 0 auto 0;height:56px;z-index:50;
  display:flex;align-items:center;gap:10px;padding:0 16px;
  background:color-mix(in srgb,var(--surface) 88%,transparent);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line);
}
#menu-btn{display:none}
#bar .title{font-weight:700;font-size:16px;letter-spacing:.04em;text-decoration:none;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#bar .spacer{flex:1}
.ctl{
  height:32px;min-width:32px;padding:0 8px;border-radius:8px;
  border:1px solid var(--line);background:var(--surface);color:var(--text);
  font-size:14px;display:inline-flex;align-items:center;justify-content:center;gap:4px;
  white-space:nowrap;flex:none;
}
.ctl:hover{border-color:var(--accent);color:var(--accent)}
#progress{position:absolute;left:0;bottom:-1px;height:2px;background:var(--accent);width:0}
/* ── 目录 ─────────────────────────── */
#toc{
  position:fixed;top:56px;bottom:0;left:0;width:284px;overflow-y:auto;
  padding:18px 14px 40px;border-right:1px solid var(--line);
  background:var(--bg);transition:transform .25s ease;z-index:40;
}
#toc .book{font-size:13px;color:var(--muted);padding:2px 10px 12px;letter-spacing:.06em}
.toc-item{
  display:flex;gap:8px;align-items:baseline;padding:7px 10px;border-radius:9px;
  text-decoration:none;color:var(--text);font-size:13.5px;line-height:1.55;
}
.toc-item .no{flex:none;width:44px;color:var(--muted);font-size:12px}
.toc-item:hover{background:var(--accent-soft)}
.toc-item.active{background:var(--accent-soft);color:var(--accent);font-weight:700}
.toc-item.active .no{color:var(--accent)}
#mask{position:fixed;inset:56px 0 0 0;background:rgba(30,25,15,.35);z-index:35;opacity:0;pointer-events:none;transition:opacity .25s}
/* ── 正文 ─────────────────────────── */
main{margin-left:284px;padding:56px 0 0}
article.ch{
  display:none;max-width:680px;margin:0 auto;padding:48px 24px 32px;
  font-size:var(--fs,18px);line-height:2.05;text-align:justify;
}
article.ch.show{display:block;animation:fadein .35s ease}
@keyframes fadein{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.ch-no{color:var(--accent);font-size:.78em;letter-spacing:.35em;margin-bottom:10px}
article.ch h1{font-size:1.55em;line-height:1.5;margin-bottom:34px;letter-spacing:.02em}
article.ch h2{
  font-size:1.05em;margin:2.2em 0 1em;padding-left:12px;
  border-left:3px solid var(--accent);line-height:1.6;
}
article.ch p{margin:0 0 1.15em}
article.ch .sep{text-align:center;color:var(--muted);letter-spacing:1em;margin:2.4em 0;text-indent:1em}
figure{margin:2em 0;text-align:center}
figure img{
  max-width:100%;border-radius:10px;
  box-shadow:var(--shadow);border:1px solid var(--line);
}
figcaption{margin-top:10px;font-size:.72em;color:var(--muted);letter-spacing:.08em}
/* ── 章末导航 / 页脚 ──────────────── */
#nav{display:none;max-width:680px;margin:0 auto;padding:0 24px 26px}
#nav.show{display:flex;gap:12px}
#nav button{
  flex:1;padding:13px 10px;border-radius:11px;border:1px solid var(--line);
  background:var(--surface);color:var(--text);font-size:13.5px;line-height:1.5;
  box-shadow:var(--shadow);text-align:left;
}
#nav button.next{text-align:right}
#nav button:disabled{opacity:.35;cursor:default;box-shadow:none}
#nav .lab{display:block;font-size:11px;color:var(--muted);margin-bottom:2px}
#nav button:not(:disabled):hover{border-color:var(--accent);color:var(--accent)}
footer{
  max-width:680px;margin:0 auto;padding:26px 24px 60px;
  font-size:12.5px;color:var(--muted);line-height:1.9;
  border-top:1px solid var(--line);
}
footer a{color:var(--muted)}
footer a:hover{color:var(--accent)}
/* ── 移动端 ───────────────────────── */
@media (max-width:920px){
  #menu-btn{display:inline-flex}
  #toc{transform:translateX(-105%);box-shadow:var(--shadow);width:300px}
  body.toc-open #toc{transform:none}
  body.toc-open #mask{opacity:1;pointer-events:auto}
  main{margin-left:0}
}
</style>
</head>
<body>
<header id="bar">
  <button class="ctl" id="menu-btn" aria-label="目录">☰</button>
  <a class="title" href="#c0">北京七年，终将离开</a>
  <span class="spacer"></span>
  <button class="ctl" id="fs-minus" title="减小字号">A−</button>
  <button class="ctl" id="fs-plus" title="增大字号">A＋</button>
  <button class="ctl" id="theme-btn" title="切换夜间模式">☾</button>
  <a class="ctl" href="https://github.com/qishuai6/beijing-qinian-zhongjiang-likai" target="_blank" rel="noopener" title="GitHub 仓库">⌂</a>
  <div id="progress"></div>
</header>
<nav id="toc" aria-label="目录">
  <div class="book">目 录 · 9.8 万字</div>
__TOC__
</nav>
<div id="mask"></div>
<main>
__ARTICLES__
<div id="nav">
  <button id="prev"><span class="lab">← 上一章</span><span class="t"></span></button>
  <button id="next" class="next"><span class="lab">下一章 →</span><span class="t"></span></button>
</div>
<footer>
  《北京七年，终将离开》作者 七帅 · 本书以
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh" target="_blank" rel="noopener">CC BY-NC-SA 4.0</a>
  协议开源 · <a href="https://github.com/qishuai6/beijing-qinian-zhongjiang-likai" target="_blank" rel="noopener">GitHub 仓库</a>
  · <a href="https://qishuai.vip" target="_blank" rel="noopener">qishuai.vip</a>
</footer>
</main>
<script>
(function(){
  var chs=[].slice.call(document.querySelectorAll("article.ch"));
  var tocItems=[].slice.call(document.querySelectorAll(".toc-item"));
  var prev=document.getElementById("prev"),next=document.getElementById("next");
  var cur=-1;

  function titleOf(i){
    var t=chs[i].getAttribute("data-title");
    var p=t.split("｜");
    return p.length>1?p[p.length-1]:t;
  }
  var nav=document.getElementById("nav");
  function show(i){
    if(i<0||i>=chs.length)return;
    if(cur>=0){chs[cur].classList.remove("show");}
    cur=i;
    chs[i].classList.add("show");
    nav.classList.add("show");
    tocItems.forEach(function(a,j){a.classList.toggle("active",j===i);});
    prev.disabled=(i===0);
    prev.querySelector(".t").textContent=i>0?titleOf(i-1):"—";
    next.disabled=(i===chs.length-1);
    next.querySelector(".t").textContent=i<chs.length-1?titleOf(i+1):"—";
    document.body.classList.remove("toc-open");
    localStorage.setItem("syib-last","c"+i);
    window.scrollTo(0,0);
    onScroll();
  }
  function fromHash(){
    var m=(location.hash||"").match(/^#c(\\d+)$/);
    var i=m?Math.min(Math.max(+m[1],0),chs.length-1):0;
    show(i);
  }
  window.addEventListener("hashchange",fromHash);

  prev.addEventListener("click",function(){location.hash="c"+(cur-1);});
  next.addEventListener("click",function(){location.hash="c"+(cur+1);});
  document.addEventListener("keydown",function(e){
    if(e.target.tagName==="INPUT")return;
    if(e.key==="ArrowLeft"&&cur>0)location.hash="c"+(cur-1);
    if(e.key==="ArrowRight"&&cur<chs.length-1)location.hash="c"+(cur+1);
  });

  document.getElementById("menu-btn").addEventListener("click",function(){
    document.body.classList.toggle("toc-open");
  });
  document.getElementById("mask").addEventListener("click",function(){
    document.body.classList.remove("toc-open");
  });

  var root=document.documentElement;
  function setFs(v){
    v=Math.min(Math.max(v,15),22);
    root.style.setProperty("--fs",v+"px");
    localStorage.setItem("syib-fs",v);
  }
  setFs(+localStorage.getItem("syib-fs")||18);
  document.getElementById("fs-plus").addEventListener("click",function(){setFs((+localStorage.getItem("syib-fs")||18)+1);});
  document.getElementById("fs-minus").addEventListener("click",function(){setFs((+localStorage.getItem("syib-fs")||18)-1);});

  function setTheme(t){
    root.setAttribute("data-theme",t);
    document.getElementById("theme-btn").textContent=t==="dark"?"☀":"☾";
    localStorage.setItem("syib-theme",t);
  }
  setTheme(localStorage.getItem("syib-theme")||"light");
  document.getElementById("theme-btn").addEventListener("click",function(){
    setTheme(root.getAttribute("data-theme")==="dark"?"light":"dark");
  });

  var bar=document.getElementById("progress");
  function onScroll(){
    var h=document.documentElement.scrollHeight-window.innerHeight;
    bar.style.width=(h>0?Math.min(window.scrollY/h*100,100):0)+"%";
  }
  window.addEventListener("scroll",onScroll,{passive:true});

  // 恢复上次读到的章节；带 hash 时以 hash 为准
  var last=localStorage.getItem("syib-last");
  if(!location.hash&&last&&/^c\\d+$/.test(last)){location.replace("#"+last);}
  else{fromHash();}
})();
</script>
</body>
</html>
"""


def main():
    md = BOOK_MD.read_text(encoding="utf-8")
    chapters = parse_chapters(md)
    toc = "\n".join(toc_item(i, t) for i, (t, _) in enumerate(chapters))
    arts = "\n".join(article(i, t, b) for i, (t, b) in enumerate(chapters))
    page = TEMPLATE.replace("__TOC__", toc).replace("__ARTICLES__", arts)
    out = ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    chars = sum(len(re.sub(r"<[^>]+>", "", b)) for _, b in chapters)
    print(f"章节 {len(chapters)} 篇，正文约 {chars} 字 → {out}（{out.stat().st_size//1024} KB）")


if __name__ == "__main__":
    main()
