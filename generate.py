#!/usr/bin/env python3
"""
Memory Wiki Site Generator v2 — Full-text search, TOC, backlinks, tag pages.
Usage: python3 generate.py
"""
import os, json, re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

VAULT = "/root/Documents/Obsidian Vault"
OUTPUT = "/root/memory-wiki"
SKIP_DIRS = {"copilot", "Session Summaries"}

session_summaries = {
    "2026-06-18": {"title": "Local AI Image & Video Gen + LLM Research", "date": "2026-06-18", "source": "telegram",
        "summary": "Researched 10 image/video gen models for Strix Halo: Wan 2.2-14B (Sora-quality, 16-37GB VRAM), LTX-Video 2.3 (30-60s clips, 12GB), FLUX.1-dev (Midjourney-quality images, 16-33GB), SD 3.5 Large/Medium, HunyuanVideo 1.5, CogVideoX-5B, Mochi 1. Created LLM models guide covering Llama 4 Scout (18 t/s), DeepSeek R1 distillation, Qwen 3, Mistral Large 2, Command R+. 64GB identified as sweet spot for both text LLMs and creative workloads. Fixed model config to deepseek-v4-pro."},
    "2026-06-05": {"title": "AMD Ryzen AI Mini PCs + Google Trends 2026", "date": "2026-06-05", "source": "telegram",
        "summary": "10 AMD Ryzen AI mini PCs: 5 Strix Halo (HP Z2 Mini G1a, Framework Desktop, Beelink GTR9 Pro, Minisforum AI X1 Pro, GMKtec EVO-X2) with soldered LPDDR5X up to 128GB at 256 GB/s, and 5 Strix Point (Minisforum AI X1, Beelink SER9 Pro, Geekom A9 Max, Lenovo ThinkCentre Neo Ultra, ASUS NUC 14 Pro AI) with upgradeable DDR5 SODIMM at 89 GB/s. Google Trends 2026: 'local ai' avg 60.1 (3x growth Jan-May), 'mini pc' avg 47.1, 'ai pc' avg 37.5. Product images for 9/10 models."},
    "2026-06-01": {"title": "GMKtec EVO-X2 Local LLM Review", "date": "2026-06-01", "source": "telegram",
        "summary": "GMKtec EVO-X2 AI Mini PC: AMD Ryzen AI Max+ 395 (16C/32T, Radeon 8060S 40 CU, 256 GB/s). Pricing: 64GB/$1,499, 128GB/$3,199. Performance: Llama 4 Scout 109B at 15 t/s with Vulkan/ROCm. WordPress draft published (ID 1172)."},
    "2026-05-22": {"title": "AI Mini PCs Blog Post + GPU Supply Chain", "date": "2026-05-22", "source": "telegram",
        "summary": "Draft 'Best Affordable AI Mini PCs of 2026': ASUS NUC 14, Geekom A8, Minisforum AtomMan X7 Ti (96GB), GMKtec K8 Plus, MSI Cubi. Published draft (ID 1159). GPU/VRAM supply chain: 60+ elements, key companies ASML, TSMC, Micron, Applied Materials, Lam Research, Entegris, NVDA, AMD."},
    "2026-06-02": {"title": "Memory OS Stack for Hermes Agent", "date": "2026-06-02", "source": "telegram",
        "summary": "Researched Memory OS: MIT-licensed 6-layer memory stack. Layers: Workspace, Sessions, Structured Facts, Fabric (16 tools), Qdrant vector DB (4096d), LLM Wiki. Features 4-level fallback cascade, social-closer filter, weekly decay scanner."},
    "2026-05-20": {"title": "Local AI Hardware & Context Engineering Blog", "date": "2026-05-20", "source": "telegram",
        "summary": "Context Engineering for LLMs blog post (1,813 words, ID 1166). Minisforum AtomMan X7 Ti (96GB) best for local LLMs. Created SEO/GEO blog writing skill. Email via Himalaya CLI."},
}

subjects = {
    "ai-mini-pcs": {"title": "AI Mini PCs \u2014 Hardware Reviews", "description": "AMD Ryzen AI mini PC reviews: Strix Halo (256 GB/s, soldered LPDDR5X up to 128GB) vs Strix Point (89 GB/s, upgradeable DDR5 up to 64GB). Pricing, NPU TOPS, memory bandwidth, and local AI benchmarks.", "tags": ["hardware", "AI", "AMD", "mini-pc"], "sessions": ["2026-06-05", "2026-06-01", "2026-05-22", "2026-05-20"]},
    "local-llm-models": {"title": "Local LLM Models \u2014 VRAM Tier Guide", "description": "Text LLMs on AI mini PCs at 32GB, 64GB, 96GB, 128GB unified memory. Llama 4 Scout (109B MoE, 18 t/s), DeepSeek R1, Qwen 3, Mistral, Command R+. GGUF quantization sizing, tokens/sec estimates.", "tags": ["AI", "LLM", "local-ai", "quantization", "vram"], "sessions": ["2026-06-18", "2026-06-01"]},
    "image-video-gen-models": {"title": "Image & Video Generation \u2014 Local AI", "description": "FLUX.1-dev (Midjourney-quality), Wan 2.2-14B (Sora-quality video), LTX-Video 2.3 (30-60s clips), SD 3.5, HunyuanVideo, CogVideoX locally on AMD Strix Halo. VRAM requirements, gen speeds, ComfyUI setup.", "tags": ["AI", "image-generation", "video-generation", "local-ai", "vram"], "sessions": ["2026-06-18"]},
    "gpu-supply-chain": {"title": "GPU & VRAM Supply Chain", "description": "Raw materials for GPU/VRAM: silicon, rare earths, interconnects. Public companies: ASML, TSMC, Micron, Applied Materials, Lam Research, Entegris, NVIDIA, AMD.", "tags": ["hardware", "GPU", "supply-chain", "investing"], "sessions": ["2026-05-22"]},
    "hermes-agent-setup": {"title": "Hermes Agent Setup & Configuration", "description": "Telegram gateway, GitHub integration, skill management, model configuration, cron jobs, session management.", "tags": ["hermes", "setup", "telegram", "github"], "sessions": []},
    "memory-os": {"title": "Memory OS \u2014 Agent Memory Stack", "description": "MIT-licensed 6-layer open-source memory stack for Hermes Agent: Workspace, Sessions, Structured Facts, Fabric, Qdrant vector DB, LLM Wiki.", "tags": ["hermes", "memory", "open-source", "RAG"], "sessions": ["2026-06-02"]},
    "blog-content": {"title": "Blog Content & WordPress Publishing", "description": "SEO/GEO-optimized blog posts: AI mini PCs, context engineering, local AI guides. WordPress publishing workflow and draft management on freshco.tech.", "tags": ["blog", "WordPress", "SEO", "content"], "sessions": ["2026-05-22", "2026-06-01", "2026-05-20"]},
    "sessions-archive": {"title": "Session Archives", "description": "Complete archive of all research sessions, daily logs, and knowledge consolidation across projects.", "tags": ["archive", "sessions", "daily-logs"], "sessions": []},
}

# --- CSS ---
CSS = """:root{--bg:#0a0a0f;--bg-card:#13131a;--bg-hover:#1a1a24;--border:#222233;--text:#d4d4d8;--text-muted:#71717a;--accent:#22d3ee;--accent2:#34d399;--accent3:#a78bfa;--accent4:#fbbf24}*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.7;min-height:100vh}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}nav{background:var(--bg-card);border-bottom:1px solid var(--border);padding:.75rem 1.5rem;position:sticky;top:0;z-index:100;display:flex;align-items:center;gap:1.5rem;backdrop-filter:blur(12px)}nav .logo{font-weight:700;font-size:1.1rem;color:var(--accent)}nav a{color:var(--text-muted);font-size:.9rem;transition:color .2s}nav a:hover{color:var(--text)}nav .search-wrap{margin-left:auto;position:relative}nav .search-wrap input{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:.4rem .75rem;color:var(--text);font-size:.85rem;width:220px}.container{max-width:1000px;margin:0 auto;padding:2rem 1.5rem}.hero{text-align:center;padding:3rem 0 2rem}.hero h1{font-size:2.2rem;font-weight:800;margin-bottom:.5rem;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}.hero p{color:var(--text-muted);font-size:1.05rem;max-width:600px;margin:0 auto}.subject-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem;margin:2rem 0}.subject-card{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1.25rem;transition:border-color .2s,transform .15s}.subject-card:hover{border-color:var(--accent);transform:translateY(-2px)}.subject-card h3{font-size:1.05rem;margin-bottom:.5rem;color:var(--accent)}.subject-card p{color:var(--text-muted);font-size:.85rem;margin-bottom:.75rem}.subject-card .meta{font-size:.75rem;color:var(--text-muted)}.tag{display:inline-block;background:rgba(34,211,238,.12);color:var(--accent);padding:.15rem .5rem;border-radius:4px;font-size:.75rem;margin-right:.3rem}.daily-list{margin:2rem 0}.daily-entry{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1.25rem;margin-bottom:.75rem;transition:border-color .2s}.daily-entry:hover{border-color:var(--accent2)}.daily-entry .date{color:var(--accent2);font-weight:600;font-size:.9rem;margin-bottom:.25rem}.daily-entry h3{font-size:1.05rem;margin-bottom:.5rem}.daily-entry p{color:var(--text-muted);font-size:.85rem}.section-title{font-size:1.3rem;font-weight:700;margin:2rem 0 1rem;display:flex;align-items:center;gap:.5rem}.section-title::after{content:'';flex:1;height:1px;background:var(--border)}.content-page{max-width:800px;margin:0 auto}.content-page h1{font-size:1.8rem;margin:1rem 0}.content-page h2{font-size:1.3rem;margin:2rem 0 .75rem;color:var(--accent2)}.content-page h3{font-size:1.05rem;margin:1.5rem 0 .5rem;color:var(--accent3)}.content-page p{margin-bottom:1rem}.content-page ul,.content-page ol{margin:.5rem 0 1rem 1.5rem}.content-page li{margin-bottom:.3rem}.content-page code{background:rgba(255,255,255,.08);padding:.15rem .4rem;border-radius:3px;font-size:.85rem}.content-page pre{background:#1a1a24;padding:1rem;border-radius:8px;overflow-x:auto;margin:1rem 0;font-size:.85rem;white-space:pre-wrap}.content-page table{border-collapse:collapse;width:100%;margin:1rem 0}.content-page th{background:rgba(255,255,255,.08);padding:.5rem .75rem;text-align:left;font-size:.85rem}.content-page td{padding:.4rem .75rem;border-bottom:1px solid var(--border);font-size:.85rem}.content-page hr{border:none;border-top:1px solid var(--border);margin:2rem 0}.content-page blockquote{border-left:3px solid var(--accent);padding-left:1rem;margin:1rem 0;color:var(--text-muted)}.content-page .session-card{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:1rem;margin:.75rem 0}.content-page .s-date{color:var(--accent2);font-size:.8rem;font-weight:600}.content-page .s-source{color:var(--text-muted);font-size:.75rem;margin-left:.5rem}.back-link{display:inline-block;margin-bottom:1.5rem;color:var(--text-muted);font-size:.85rem}.back-link:hover{color:var(--accent)}.search-results{position:absolute;top:100%;right:0;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;width:350px;max-height:400px;overflow-y:auto;z-index:200;display:none;margin-top:4px}.search-results.active{display:block}.search-results a{display:block;padding:.6rem .75rem;border-bottom:1px solid var(--border);color:var(--text);font-size:.85rem}.search-results a:hover{background:var(--bg-hover);text-decoration:none}.search-results a .match-title{font-weight:600}.search-results a .match-preview{color:var(--text-muted);font-size:.75rem;margin-top:.15rem}.search-results .no-results{padding:.75rem;color:var(--text-muted)}footer{text-align:center;padding:3rem 1.5rem;color:var(--text-muted);font-size:.8rem;border-top:1px solid var(--border);margin-top:3rem}.toc{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:1rem 1.25rem;margin-bottom:2rem}.toc h3{font-size:.95rem;color:var(--accent2);margin-bottom:.75rem}.toc ul{list-style:none}.toc ul ul{padding-left:1.25rem}.toc li{margin-bottom:.3rem}.toc a{color:var(--text-muted);font-size:.85rem}.toc a:hover{color:var(--accent)}.backlinks{margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--border)}.backlinks h2{font-size:1.1rem;margin-bottom:.75rem;color:var(--accent3)}.backlinks ul{list-style:none;display:flex;flex-wrap:wrap;gap:.5rem}.backlinks li a{display:inline-block;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:.3rem .75rem;font-size:.85rem;transition:border-color .2s}.backlinks li a:hover{border-color:var(--accent);text-decoration:none}.tag-cloud{display:flex;flex-wrap:wrap;gap:.5rem;margin:1.5rem 0}.tag-cloud a{display:inline-block;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:.4rem .85rem;font-size:.85rem;transition:all .2s}.tag-cloud a:hover{border-color:var(--accent);background:var(--bg-hover);text-decoration:none}.tag-cloud a .count{color:var(--text-muted);font-size:.7rem;margin-left:.3rem}.content-page h2[id],.content-page h3[id]{scroll-margin-top:80px}.content-page h2[id]::after,.content-page h3[id]::after{content:' #';color:var(--text-muted);font-size:.7rem;opacity:0;transition:opacity .2s}.content-page h2[id]:hover::after,.content-page h3[id]:hover::after{opacity:1}.subject-header{margin-bottom:2rem}nav a.tag-link{font-size:.8rem;color:var(--accent3)}"""

NAV = """<nav>
  <span class="logo">\U0001f9e0 Memory Wiki</span>
  <a href="ROOT/">Home</a>
  <a href="ROOT/subjects/">Subjects</a>
  <a href="ROOT/tags/">Tags</a>
  <a href="ROOT/daily/">Daily</a>
  <div class="search-wrap">
    <input type="text" id="search-input" placeholder="Full-text search..." oninput="doSearch(this.value)">
    <div class="search-results" id="search-results"></div>
  </div>
</nav>"""

FOOTER = """<footer><p>Memory Wiki &mdash; Knowledge base of conversations and work with Hermes Agent<br>Last updated: {updated}</p></footer>"""

SEARCH_JS = """<script>
var SI=[];
fetch('ROOT/search-index.json').then(x=>x.json()).then(idx=>{SI=idx});
function doSearch(q){
  var r=document.getElementById('search-results');
  if(!q||q.length<2){r.classList.remove('active');return}
  var ql=q.toLowerCase(), qw=ql.split(/\\s+/);
  var m=SI.filter(i=>{
    var txt=(i.title+' '+(i.preview||'')+' '+(i.content||'')+' '+(i.tags||[]).join(' ')).toLowerCase();
    return qw.every(w=>txt.includes(w));
  }).slice(0,10);
  if(m.length===0)r.innerHTML='<div class="no-results">No matches</div>';
  else r.innerHTML=m.map(i=>{
    var ctx='',c=(i.content||''),idx=c.toLowerCase().indexOf(ql);
    if(idx>=0)ctx=c.substring(Math.max(0,idx-40),idx+80);
    return '<a href="'+i.url+'"><div class="match-title">'+i.title+'</div><div class="match-preview">'+(ctx||(i.preview||'').substring(0,100))+'</div></a>';
  }).join('');
  r.classList.add('active');
}
document.addEventListener('click',e=>{if(!e.target.closest('.search-wrap'))document.getElementById('search-results').classList.remove('active')});
</script>"""

def slugify(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

def page_head(title, root):
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{title} \u2014 Memory Wiki</title><link rel="stylesheet" href="{root}style.css"></head><body>{NAV.replace("ROOT/",root)}<div class="container">'

def page_foot(root):
    return f'</div>{FOOTER.format(updated=datetime.now().strftime("%B %d, %Y at %I:%M %p"))}{SEARCH_JS.replace("ROOT/",root)}</body></html>'

def read_vault_file(filepath):
    """Read Obsidian markdown file, extract frontmatter, full body, and headings."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        lines = text.split('\n')
        tags = []
        body_start = 0
        if lines and lines[0].strip() == '---':
            for i, line in enumerate(lines[1:30], 1):
                if line.strip() == '---':
                    body_start = i + 1
                    break
                if line.startswith('tags:'):
                    raw = line.split(':',1)[1].strip()
                    tags = [t.strip().lstrip('- ').strip() for t in raw.replace('[','').replace(']','').split(',') if t.strip()]
        title = Path(filepath).stem.replace('-',' ').title()
        if body_start < len(lines) and body_start > 0:
            for l in lines[body_start:]:
                if l.startswith('#'):
                    title = l.lstrip('# ').strip()
                    break
        full_body = '\n'.join(lines[body_start:]) if body_start else text
        headings = []
        for line in lines[body_start:]:
            m = re.match(r'^(#{1,3})\s+(.+)$', line)
            if m:
                level = len(m.group(1))
                htext = m.group(2).strip()
                anchor = slugify(htext)
                headings.append({'level': level, 'text': htext, 'anchor': anchor})
        return {"path": filepath, "title": title, "tags": tags, "body": full_body, "headings": headings,
                "rel": os.path.relpath(filepath, VAULT)}
    except Exception as e:
        return {"path": filepath, "title": Path(filepath).stem.replace('-',' ').title(),
                "tags": [], "body": str(e)[:200], "headings": [],
                "rel": os.path.relpath(filepath, VAULT)}

def anchorify_body(body):
    """Add id attributes to ## and ### headings in markdown body rendered as HTML."""
    def repl(m):
        htext = m.group(1).strip()
        anchor = slugify(htext)
        tag = 'h2' if m.group(0).startswith('## ') else 'h3' if m.group(0).startswith('### ') else 'h' + str(len(m.group(0).split()[0]))
        return f'<{tag} id="{anchor}">{htext}</{tag}>'
    # Simple HTML conversion for headings
    lines = body.split('\n')
    out = []
    for line in lines:
        m2 = re.match(r'^##\s+(.+)$', line)
        m3 = re.match(r'^###\s+(.+)$', line)
        if m2:
            htext = m2.group(1).strip()
            out.append(f'<h2 id="{slugify(htext)}">{htext}</h2>')
        elif m3:
            htext = m3.group(1).strip()
            out.append(f'<h3 id="{slugify(htext)}">{htext}</h3>')
        else:
            out.append(line)
    return '\n'.join(out)

def simple_md_to_html(text):
    """Basic markdown to HTML for note previews."""
    lines = text.split('\n')
    out = []
    in_code = False
    for line in lines:
        if line.startswith('```'):
            if in_code:
                out.append('</pre>')
                in_code = False
            else:
                out.append('<pre>')
                in_code = True
            continue
        if in_code:
            out.append(line.replace('<','&lt;').replace('>','&gt;'))
            continue
        if re.match(r'^###\s+', line):
            htext = re.sub(r'^###\s+', '', line).strip()
            out.append(f'<h3 id="{slugify(htext)}">{htext}</h3>')
        elif re.match(r'^##\s+', line):
            htext = re.sub(r'^##\s+', '', line).strip()
            out.append(f'<h2 id="{slugify(htext)}">{htext}</h2>')
        elif re.match(r'^#\s+', line):
            htext = re.sub(r'^#\s+', '', line).strip()
            out.append(f'<h1>{htext}</h1>')
        elif line.startswith('|'):
            out.append(line.replace('<','&lt;').replace('>','&gt;'))
        elif line.startswith('-'):
            out.append(f'<li>{line[1:].strip()}</li>')
        elif line.startswith('>'):
            out.append(f'<blockquote>{line[1:].strip()}</blockquote>')
        elif line.strip() == '':
            out.append('<br>')
        else:
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
            line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
            out.append(line.replace('<','&lt;').replace('>','&gt;'))
    if in_code: out.append('</pre>')
    return '\n'.join(out)

def build_toc_html(files):
    """Build table of contents from all file headings."""
    seen = set()
    items = []
    for ff in files:
        for h in ff.get('headings', []):
            if h['anchor'] not in seen and h['level'] <= 3:
                seen.add(h['anchor'])
                items.append(h)
    if len(items) < 2:
        return ''
    html = '<nav class="toc"><h3>\U0001f4d1 On This Page</h3><ul>'
    for h in items:
        indent = ' style="padding-left:' + str((h['level']-1)*1.25) + 'rem"' if h['level'] > 1 else ''
        html += f'<li{indent}><a href="#{h["anchor"]}">{h["text"]}</a></li>'
    html += '</ul></nav>'
    return html

def build_backlinks(sid, subjects, all_files):
    """Find other subjects whose notes reference this subject."""
    this_subj = subjects.get(sid, {})
    this_keywords = set(sid.split('-'))
    this_keywords.update(this_subj.get('title','').lower().split())
    backlinks = []
    for other_sid, other_subj in subjects.items():
        if other_sid == sid:
            continue
        for ff in other_subj.get('files', []):
            body_lower = ff.get('body','').lower()
            if any(kw in body_lower for kw in this_keywords if len(kw) > 2):
                backlinks.append(other_sid)
                break
    return backlinks

def build_tag_index(subjects, files_data):
    """Build tag -> {subjects, files} mapping."""
    ti = defaultdict(lambda: {"subjects": [], "files": [], "count": 0})
    for sid, subj in subjects.items():
        for tag in subj.get('tags', []):
            ti[tag]["subjects"].append(sid)
            ti[tag]["count"] += 1
    for ff in files_data:
        for tag in ff.get('tags', []):
            if tag not in ti:
                ti[tag] = {"subjects": [], "files": [], "count": 0}
            ti[tag]["files"].append(ff)
            ti[tag]["count"] += 1
    return dict(sorted(ti.items(), key=lambda x: x[1]['count'], reverse=True))

def generate():
    os.makedirs(OUTPUT, exist_ok=True)
    os.makedirs(f"{OUTPUT}/subjects", exist_ok=True)
    os.makedirs(f"{OUTPUT}/daily", exist_ok=True)
    os.makedirs(f"{OUTPUT}/tags", exist_ok=True)

    with open(f"{OUTPUT}/style.css", "w") as f: f.write(CSS)

    # Walk vault
    files_data = []
    for rootdir, dirs, filenames in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.md'):
                fp = os.path.join(rootdir, fn)
                fd = read_vault_file(fp)
                files_data.append(fd)
    print(f"Found {len(files_data)} vault files")

    # Auto-map files to subjects
    for subj in subjects.values():
        subj["files"] = []
    for f in files_data:
        name = Path(f["rel"]).stem.lower()
        for sid, subj in subjects.items():
            keywords = sid.split("-")
            if any(kw in name for kw in keywords):
                subj["files"].append(f)

    for sid, subj in subjects.items():
        fnames = [Path(ff["rel"]).name for ff in subj["files"]]
        print(f"  {sid}: {len(fnames)} files")

    # Tag index
    tag_index = build_tag_index(subjects, files_data)
    print(f"  {len(tag_index)} unique tags")

    # --- SEARCH INDEX (with full-text content) ---
    search_index = []
    for sid, subj in subjects.items():
        all_content = " ".join(ff.get("body","")[:2000] for ff in subj.get("files",[]))
        search_index.append({"title": subj["title"], "url": f"subjects/{slugify(sid)}.html",
            "type": "subject", "preview": subj["description"],
            "content": all_content[:3000], "tags": subj.get("tags", [])})
    for sid, sess in sorted(session_summaries.items(), key=lambda x: x[1]["date"], reverse=True):
        search_index.append({"title": f"{sess['date']} \u2014 {sess['title']}",
            "url": f"daily/{sess['date']}.html#{sid}", "type": "daily",
            "preview": sess["summary"], "content": sess["summary"], "date": sess["date"]})
    with open(f"{OUTPUT}/search-index.json", "w") as f: json.dump(search_index, f)

    # --- HOME PAGE ---
    cards = ""
    for sid, subj in subjects.items():
        tags_html = " ".join(f'<a href="../tags/{slugify(t)}.html" class="tag">{t}</a>' for t in subj.get("tags", [])[:3])
        nf = len(subj.get("files", [])); ns = len(subj.get("sessions", []))
        meta = " ".join([f'<span>{nf} notes</span>' if nf else '', f'<span>{ns} sessions</span>' if ns else ''])
        cards += f'<a href="subjects/{slugify(sid)}.html" style="text-decoration:none"><div class="subject-card"><h3>{subj["title"]}</h3><p>{subj["description"][:150]}</p><div>{tags_html}</div><div class="meta">{meta}</div></div></a>'

    daily_p = ""
    for sid, sess in sorted(session_summaries.items(), key=lambda x: x[1]["date"], reverse=True)[:6]:
        daily_p += f'<a href="daily/{sess["date"]}.html#{sid}" style="text-decoration:none"><div class="daily-entry"><div class="date">{sess["date"]}</div><h3>{sess["title"]}</h3><p>{sess["summary"][:120]}...</p></div></a>'

    home = page_head("Memory Wiki", "") + f'<div class="hero"><h1>Memory Wiki</h1><p>Every subject we\'ve explored, every day we\'ve worked together \u2014 searchable and organized.</p></div><div class="section-title">Subjects <a href="subjects/" style="font-size:.8rem;font-weight:400;margin-left:.5rem">View all</a></div><div class="subject-grid">{cards}</div><div class="section-title">Recent Sessions <a href="daily/" style="font-size:.8rem;font-weight:400;margin-left:.5rem">View all</a></div><div class="daily-list">{daily_p}</div>' + page_foot("")
    with open(f"{OUTPUT}/index.html", "w") as f: f.write(home)

    # --- SUBJECT PAGES (with TOC + backlinks + clickable tags) ---
    for sid, subj in subjects.items():
        slug = slugify(sid)
        toc_html = build_toc_html(subj.get("files", []))
        sessions_html = ""
        for s_sid in subj.get("sessions", []):
            sess = session_summaries.get(s_sid)
            if sess:
                sessions_html += f'<div class="session-card" id="{s_sid}"><div class="s-date">{sess["date"]}<span class="s-source"> via {sess["source"]}</span></div><h3>{sess["title"]}</h3><p>{sess["summary"]}</p></div>'
        files_html = ""
        for ff in subj.get("files", []):
            body_html = simple_md_to_html(ff.get("body", "")[:1500])
            files_html += f'<div class="session-card"><h3>{ff["title"]}</h3><p style="font-size:.8rem;color:var(--text-muted)">{ff["rel"]}</p><div style="font-size:.85rem;margin-top:.5rem">{body_html}</div></div>'
        tags_html = " ".join(f'<a href="../tags/{slugify(t)}.html" class="tag">{t}</a>' for t in subj.get("tags", []))
        bl = build_backlinks(sid, subjects, files_data)
        backlinks_html = ""
        if bl:
            backlinks_html = '<div class="backlinks"><h2>\U0001f517 Referenced By</h2><ul>'
            for other_sid in bl:
                backlinks_html += f'<li><a href="{slugify(other_sid)}.html">{subjects[other_sid]["title"]}</a></li>'
            backlinks_html += '</ul></div>'

        page = page_head(subj["title"], "../") + f'<a href="../subjects/" class="back-link">&larr; All Subjects</a><div class="content-page subject-header"><h1>{subj["title"]}</h1><div style="margin-top:.5rem">{tags_html}</div><p style="color:var(--text-muted);margin-top:.75rem">{subj["description"]}</p></div><div class="content-page"><h2>Vault Notes ({len(subj.get("files", []))})</h2>{files_html or "<p style=color:var(--text-muted)>No vault notes linked yet.</p>"}<h2>Related Sessions ({len(subj.get("sessions", []))})</h2>{sessions_html or "<p style=color:var(--text-muted)>No sessions recorded yet.</p>"}{backlinks_html}</div>' + page_foot("../")
        with open(f"{OUTPUT}/subjects/{slug}.html", "w") as f: f.write(page)

    # Subjects index
    sidx_html = ""
    for sid, subj in subjects.items():
        tags_html = " ".join(f'<a href="../tags/{slugify(t)}.html" class="tag">{t}</a>' for t in subj.get("tags", [])[:3])
        sidx_html += f'<a href="{slugify(sid)}.html" style="text-decoration:none"><div class="subject-card"><h3>{subj["title"]}</h3><p>{subj["description"][:120]}...</p><div>{tags_html}</div></div></a>'
    sidx = page_head("All Subjects", "../") + f'<a href="../" class="back-link">&larr; Home</a><div class="content-page"><h1>All Subjects</h1><div class="subject-grid">{sidx_html}</div></div>' + page_foot("../")
    with open(f"{OUTPUT}/subjects/index.html", "w") as f: f.write(sidx)

    # --- TAG PAGES ---
    tag_cloud_html = ""
    for tag, ti in tag_index.items():
        tag_cloud_html += f'<a href="{slugify(tag)}.html">{tag}<span class="count">{ti["count"]}</span></a>'
    tidx = page_head("Tags", "../") + f'<a href="../" class="back-link">&larr; Home</a><div class="content-page"><h1>All Tags</h1><div class="tag-cloud">{tag_cloud_html}</div></div>' + page_foot("../")
    with open(f"{OUTPUT}/tags/index.html", "w") as f: f.write(tidx)

    for tag, ti in tag_index.items():
        tslug = slugify(tag)
        subj_links = "".join(f'<li><a href="../subjects/{slugify(s)}.html">{subjects[s]["title"]}</a></li>' for s in ti["subjects"] if s in subjects)
        file_cards = ""
        for ff in ti["files"][:10]:
            body_html = simple_md_to_html(ff.get("body", "")[:500])
            file_cards += f'<div class="session-card"><h3>{ff["title"]}</h3><p style="font-size:.8rem;color:var(--text-muted)">{ff["rel"]}</p><div style="font-size:.85rem;margin-top:.5rem">{body_html}</div></div>'
        tpage = page_head(f"Tag: {tag}", "../") + f'<a href="../tags/" class="back-link">&larr; All Tags</a><div class="content-page"><h1>Tag: {tag}</h1><p style="color:var(--text-muted)">{ti["count"]} items</p><h2>Subjects</h2><ul>{subj_links or "<li style=color:var(--text-muted)>No subjects</li>"}</ul><h2>Notes ({len(ti["files"])})</h2>{file_cards or "<p style=color:var(--text-muted)>No notes</p>"}</div>' + page_foot("../")
        with open(f"{OUTPUT}/tags/{tslug}.html", "w") as f: f.write(tpage)

    # --- DAILY PAGES ---
    daily_groups = defaultdict(list)
    for sid, sess in session_summaries.items(): daily_groups[sess["date"]].append((sid, sess))
    didx = page_head("Daily Logs", "../") + '<a href="../" class="back-link">&larr; Home</a><div class="content-page"><h1>Daily Logs</h1><div class="daily-list">'
    for date in sorted(daily_groups.keys(), reverse=True):
        sessions = daily_groups[date]
        titles = "; ".join(s[1]["title"] for s in sessions)[:120]
        didx += f'<a href="{date}.html" style="text-decoration:none"><div class="daily-entry"><div class="date">{date}</div><h3>{titles}</h3><p>{len(sessions)} session{"s" if len(sessions)>1 else ""}</p></div></a>'
    didx += '</div></div>' + page_foot("../")
    with open(f"{OUTPUT}/daily/index.html", "w") as f: f.write(didx)

    for date in sorted(daily_groups.keys(), reverse=True):
        sessions = daily_groups[date]
        day_html = page_head(f"Daily Log \u2014 {date}", "../") + f'<a href="../daily/" class="back-link">&larr; All Daily Logs</a><div class="content-page"><h1>{date}</h1>'
        for sid, sess in sessions:
            day_html += f'<div class="session-card" id="{sid}"><div class="s-date">{sess["date"]}<span class="s-source"> via {sess["source"]}</span></div><h3>{sess["title"]}</h3><p>{sess["summary"]}</p></div>'
        day_html += '</div>' + page_foot("../")
        with open(f"{OUTPUT}/daily/{date}.html", "w") as f: f.write(day_html)

    with open(f"{OUTPUT}/.nojekyll", "w") as f: f.write("")

    n_subjects = len(subjects)
    n_dailies = len(daily_groups)
    n_tags = len(tag_index)
    print(f"\nGenerated: {n_subjects} subjects, {n_dailies} daily logs, {n_tags} tag pages, {len(search_index)} search entries")
    print(f"Output: {OUTPUT}")

if __name__ == "__main__":
    generate()