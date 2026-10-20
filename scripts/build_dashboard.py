#!/usr/bin/env python3
"""GeoGov DQ 裁决台账看板 — 单文件 HTML 构建器.

数据权威（全部实时读取，零外部依赖，生成物可浏览器直开）:
  protocol/dq_verdict_protocol_v1.json  GateDecision 契约 + 五不变量 + 四仓词汇对照
  rules/dq_rules_v1_frozen.json         31 条冻结规则 (V1-FROZEN) + HardGate + 批次三态
  rules/rule_samples_v1.jsonl           31 组正反例行对 (positive_trigger / negative_pass)

用法:  python3 scripts/build_dashboard.py [输出路径]
默认输出 docs/reports/geogov_dashboard.html
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build() -> str:
    protocol = json.loads((ROOT / "protocol" / "dq_verdict_protocol_v1.json").read_text(encoding="utf-8"))
    rules_doc = json.loads((ROOT / "rules" / "dq_rules_v1_frozen.json").read_text(encoding="utf-8"))
    samples = [json.loads(line) for line in (ROOT / "rules" / "rule_samples_v1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

    data = {
        "protocol_version": protocol["protocol_version"],
        "authored": protocol.get("authored"),
        "gate_props": protocol["$defs"]["GateDecision"]["properties"],
        "gate_required": protocol["$defs"]["GateDecision"]["required"],
        "invariants": protocol["invariants"],
        "vocab": protocol["vocabulary_alignment"],
        "enums": {
            "admission": protocol["$defs"]["AdmissionAction"]["enum"],
            "disposition": protocol["$defs"]["GovernanceDisposition"]["enum"],
            "severity": protocol["$defs"]["Severity"]["enum"],
        },
        "rules": rules_doc["rules"],
        "hard_gates": rules_doc["hard_gates"],
        "severity_levels": rules_doc["severity_levels"],
        "batch_verdict": rules_doc["batch_verdict"],
        "frozen_at": rules_doc.get("frozen_at"),
        "basis": rules_doc.get("basis"),
        "samples": {s["rule_id"]: s for s in samples},
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    return HTML_TEMPLATE.replace("__DATA__", payload)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GeoGov · DQ 裁决台账看板</title>
<style>
:root{--ink:#1a2332;--paper:#f7f5f0;--card:#fff;--line:#d8d3c8;--accent:#0f4c81;
--c0:#b42318;--c1:#d97706;--c2:#0e7490;--c3:#6b7280;--ok:#15803d;--warn:#b45309;--bad:#b42318}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.55}
header{background:var(--ink);color:#fff;padding:18px 28px}
header h1{font-size:19px;font-weight:600;letter-spacing:.5px}
header .meta{font-size:12px;opacity:.75;margin-top:4px}
nav{display:flex;gap:2px;background:#e9e5db;border-bottom:1px solid var(--line);padding:0 20px;position:sticky;top:0;z-index:5}
nav button{border:none;background:none;padding:11px 16px;font-size:14px;cursor:pointer;border-bottom:3px solid transparent;color:#5a6270}
nav button.active{border-bottom-color:var(--accent);color:var(--accent);font-weight:600;background:#fff}
main{max-width:1180px;margin:0 auto;padding:22px 20px 60px}
section{display:none}section.show{display:block}
h2{font-size:16px;margin:6px 0 14px;color:var(--accent)}
h3{font-size:13.5px;margin:18px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin-bottom:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#efeadf;font-weight:600;white-space:nowrap}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11.5px;font-weight:600;color:#fff}
.bC0{background:var(--c0)}.bC1{background:var(--c1)}.bC2{background:var(--c2)}.bC3{background:var(--c3)}
.hg{color:var(--bad);font-weight:700}
.chip{display:inline-block;border:1px solid var(--line);border-radius:6px;padding:4px 10px;margin:3px 4px 3px 0;background:#fbfaf7;font-size:12.5px}
.chip b{color:var(--accent)}
.req{color:var(--bad);font-weight:700}
.muted{color:#6a7280;font-size:12px}
.inv{border-left:4px solid var(--accent);padding:8px 12px;margin:8px 0;background:#f2f6fa;border-radius:0 6px 6px 0;font-size:13px}
.vmatrix td{text-align:center}.vmatrix th{text-align:center}
.vmatrix td.cell{cursor:pointer;font-weight:700;font-size:15px}
.vmatrix td.cell:hover{outline:2px solid var(--accent)}
select,input[type=search]{font:inherit;padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;width:100%}
.rowpair{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}
.rowcard{border:1px solid var(--line);border-radius:8px;overflow:hidden}
.rowcard .hd{padding:7px 12px;font-weight:600;font-size:12.5px;color:#fff}
.rowcard.bad .hd{background:var(--bad)}.rowcard.good .hd{background:var(--ok)}
.rowcard table td{border-bottom:1px solid #eee;padding:5px 12px}
.rowcard td.k{color:#6a7280;width:130px;font-size:12px}
td.diff{background:#fdeceb;font-weight:700}
.good td.diff{background:#e9f7ee}
pre{background:#0f1720;color:#d7e3ee;padding:14px;border-radius:8px;font-size:12px;overflow:auto;line-height:1.5}
.kv{font-size:12.5px;color:#4a5260}
footer{text-align:center;color:#8a8f98;font-size:11.5px;padding:18px}
@media(max-width:860px){.grid2,.rowpair{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>GeoGov · 数据质量裁决台账看板</h1>
  <div class="meta" id="hdr-meta"></div>
</header>
<nav>
  <button data-t="t1" class="active">① 裁决契约</button>
  <button data-t="t2">② 31 规则注册表</button>
  <button data-t="t3">③ 词汇四仓对照</button>
  <button data-t="t4">④ 正反例浏览</button>
</nav>
<main>

<section id="t1" class="show">
  <h2>GateDecision 裁决对象（协议 v<span id="pv"></span>）</h2>
  <div class="grid2">
    <div class="card"><h3>字段契约（<span class="req">*</span> = 必填）</h3><table id="gate-fields"></table>
      <p class="muted" style="margin-top:8px">决策不可变；修正以新决策 + supersedes 表达。</p></div>
    <div class="card"><h3>五条不变量（违例即协议错误）</h3><div id="invariants"></div>
      <h3>批次三态</h3><p class="kv" id="batch-verdict"></p></div>
  </div>
  <div class="card"><h3>示例裁决（演示数据，非真实批次记录）</h3><pre id="demo-decision"></pre></div>
</section>

<section id="t2">
  <h2>V1-FROZEN 规则注册表 · <span id="rule-count"></span> 条（HardGate <span id="hg-count"></span> 条）</h2>
  <div class="card"><h3>维度 × 严重级 分布（点击单元格过滤下方清单）</h3>
    <table class="vmatrix" id="vmatrix"></table><div id="vm-note" class="muted" style="margin-top:6px"></div></div>
  <div class="card"><table id="rules-table"></table></div>
</section>

<section id="t3">
  <h2>受控词表与四仓对齐</h2>
  <div class="card"><h3>AdmissionAction（准入 4 态）</h3><div id="enum-admission"></div>
    <h3>GovernanceDisposition（处置 5 态）</h3><div id="enum-disposition"></div>
    <h3>Severity（分级）</h3><div id="enum-severity"></div></div>
  <div class="card"><h3>词汇对照（<span id="vocab-desc"></span>）</h3>
    <table id="vocab-table"></table></div>
</section>

<section id="t4">
  <h2>规则正反例（31 组行对，来自 rule_samples_v1.jsonl）</h2>
  <div class="card">
    <input type="search" id="sample-search" placeholder="搜索规则号 / 字段 / 文本…">
    <select id="sample-select" size="14" style="margin-top:10px;height:auto"></select>
    <div id="sample-detail"></div>
  </div>
</section>

</main>
<footer id="foot"></footer>
<script>
const D = __DATA__;
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const SEVC={'C0':'bC0','C1':'bC1','C2':'bC2','C3':'bC3'};

// nav
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('nav button').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('main section').forEach(x=>x.classList.remove('show'));
  b.classList.add('active');$('#'+b.dataset.t).classList.add('show');});

// header
$('#hdr-meta').textContent=`协议 ${D.protocol_version} · 规则 ${D.rules.length} 条冻结 (${esc(D.frozen_at||'')}) · 依据 ${esc(D.basis||'')}`;
$('#pv').textContent=D.protocol_version;
$('#foot').textContent=`GeoGov · 数据源: protocol/dq_verdict_protocol_v1.json + rules/dq_rules_v1_frozen.json + rules/rule_samples_v1.jsonl · 构建: scripts/build_dashboard.py`;

// ---- panel 1: gate fields + invariants
$('#gate-fields').innerHTML='<tr><th>字段</th><th>类型/取值</th></tr>'+Object.entries(D.gate_props).map(([k,v])=>{
  const req=D.gate_required.includes(k)?'<span class="req">*</span> ':'';
  let t=v.type||'';if(v.const)t='const '+v.const;else if(v.enum)t=v.enum.join(' | ');
  if(t==='array'&&v.items){const it=v.items;if(it.$ref){const n=it.$ref.split('/').pop();t='RuleEvaluation[]';}else t=(it.type||'object')+'[]';}
  if(v.format)t+=` (${v.format})`;
  return `<tr><td>${req}${esc(k)}</td><td class="kv">${esc(t)}</td></tr>`;}).join('');
$('#invariants').innerHTML=D.invariants.map(x=>`<div class="inv">${esc(x)}</div>`).join('');
$('#batch-verdict').textContent=D.batch_verdict;

// demo decision (clearly synthetic)
const demo={protocol_version:D.protocol_version,action:'REVIEW',disposition:'QUARANTINE',scope:'batch://demo-2026-10-13',
 hard_gates_all_pass:false,rationale:'R004 主键唯一性失败 (C1 HardGate)；缺失必评证据 R022 → fail-closed',
 decided_by:'dq-officer@example',decided_at:'2026-10-13T09:00:00+08:00',immutable:true,supersedes:null,
 evaluations:[{rule_id:'DQ-R004@dq-rules-v1',verdict:'FAIL',severity:'C1',evidence_id:'ev-0001'},
              {rule_id:'DQ-R001@dq-rules-v1',verdict:'PASS',severity:'C1',evidence_id:'ev-0002'},
              {rule_id:'DQ-R022@dq-rules-v1',verdict:'NOT_APPLICABLE',severity:'C2',note:'证据缺失记 N/A，不猜测'}]};
$('#demo-decision').textContent=JSON.stringify(demo,null,1);

// ---- panel 2: matrix + rules
let filter=null;
const dims=[...new Set(D.rules.map(r=>r.dim))];
const sevs=['C0','C1','C2','C3'];
function renderMatrix(){
  let h='<tr><th></th>'+sevs.map(s=>`<th>${s}</th>`).join('')+'<th>合计</th></tr>';
  for(const d of dims){
    h+=`<tr><th>${esc(d)}</th>`;let tot=0;
    for(const s of sevs){const n=D.rules.filter(r=>r.dim===d&&r.sev===s).length;tot+=n;
      const on=filter&&filter.d===d&&filter.s===s;
      h+=`<td class="cell" data-d="${esc(d)}" data-s="${s}" style="${n?'':'opacity:.25'}${on?';outline:2px solid var(--accent)':''}">${n||'·'}</td>`;}
    h+=`<td class="muted">${tot}</td></tr>`;}
  h+='<tr><th>合计</th>'+sevs.map(s=>`<td><b>${D.rules.filter(r=>r.sev===s).length}</b></td>`).join('')+`<td><b>${D.rules.length}</b></td></tr>`;
  $('#vmatrix').innerHTML=h;
  $('#vmatrix').querySelectorAll('td.cell').forEach(td=>td.onclick=()=>{
    const f={d:td.dataset.d,s:td.dataset.s};
    filter=(filter&&filter.d===f.d&&filter.s===f.s)?null:f;renderMatrix();renderRules();});
}
function renderRules(){
  let rs=D.rules;
  if(filter){rs=rs.filter(r=>(!filter.d||r.dim===filter.d)&&(!filter.s||r.sev===filter.s));}
  $('#vm-note').textContent=filter?`过滤: ${filter.d||'全维度'} × ${filter.s||'全级别'} → ${rs.length} 条（再点同格清除）`:'点击矩阵单元格可过滤';
  $('#rules-table').innerHTML='<tr><th>ID</th><th>维度</th><th>子项</th><th>字段</th><th>规则</th><th>口径 A/B</th><th>阈值</th><th>级</th><th>HG</th></tr>'+
   rs.map(r=>`<tr><td><b>${esc(r.id)}</b></td><td>${esc(r.dim)}</td><td class="kv">${esc(r.sub)}</td><td>${esc(r.field)}</td><td>${esc(r.rule)}</td><td class="kv">${esc(r.A)} / ${esc(r.B)}</td><td>${r.threshold}</td><td><span class="badge ${SEVC[r.sev]}">${r.sev}</span></td><td>${r.hard_gate?'<span class="hg">●</span>':''}</td></tr>`).join('');
}
$('#rule-count').textContent=D.rules.length;$('#hg-count').textContent=D.hard_gates.length;
renderMatrix();renderRules();

// ---- panel 3: vocab
const chipify=(arr,fn)=>arr.map(x=>`<span class="chip">${fn?fn(x):esc(x)}</span>`).join('');
$('#enum-admission').innerHTML=chipify(D.enums.admission);
$('#enum-disposition').innerHTML=chipify(D.enums.disposition);
$('#enum-severity').innerHTML=Object.entries(D.severity_levels).map(([k,v])=>`<span class="chip"><span class="badge ${SEVC[k]}">${k}</span> ${esc(v)}</span>`).join('');
$('#vocab-desc').textContent=D.vocab.description||'';
const repos=Object.keys(D.vocab).filter(k=>!['description'].includes(k));
$('#vocab-table').innerHTML='<tr><th>仓</th><th>词汇映射</th></tr>'+repos.map(rp=>{
  const v=D.vocab[rp];const body=typeof v==='object'?Object.entries(v).map(([a,b])=>`<b>${esc(a)}</b> → ${esc(Array.isArray(b)?b.join(', '):b)}`).join('<br>'):esc(v);
  return `<tr><td style="white-space:nowrap">${esc(rp)}</td><td class="kv">${body}</td></tr>`;}).join('');

// ---- panel 4: samples
const sel=$('#sample-select');
const ruleList=()=>{const q=$('#sample-search').value.trim().toLowerCase();
  return D.rules.filter(r=>{const s=D.samples['DQ-'+r.id+'@dq-rules-v1'];
    return !q||((r.id+r.field+r.rule+(s?s.rule_text:'')).toLowerCase().includes(q));});};
function fillSelect(){const rs=ruleList();
  sel.innerHTML=rs.map(r=>{const hg=r.hard_gate?' ●':'';return `<option value="${r.id}">${r.id} [${r.sev}${hg}] ${r.dim} · ${r.field} — ${r.rule}</option>`;}).join('');
  if(rs.length)show(rs[0].id);}
function show(id){const r=D.rules.find(x=>x.id===id);if(!r)return;
  const s=D.samples['DQ-'+r.id+'@dq-rules-v1'];
  if(!s){$('#sample-detail').innerHTML='<p class="muted">该规则无样例登记。</p>';return;}
  const p=s.samples.positive_trigger,n=s.samples.negative_pass;
  const keys=[...new Set([...Object.keys(p||{}),...Object.keys(n||{})])];
  const diffKeys=keys.filter(k=>JSON.stringify(p?.[k])!==JSON.stringify(n?.[k]));
  const row=(obj,cls)=>`<div class="rowcard ${cls}"><div class="hd">${cls==='bad'?'positive_trigger（触发违例）':'negative_pass（合格对照）'}</div><table>`+
    keys.map(k=>{const v=obj?.[k];const isd=diffKeys.includes(k);
      return `<tr><td class="k">${esc(k)}</td><td class="${isd?'diff':''}">${v===undefined?'<span class="muted">—</span>':esc(JSON.stringify(v))}</td></tr>`;}).join('')+'</table></div>';
  $('#sample-detail').innerHTML=`<h3 style="margin-top:14px">${esc(r.id)} · ${esc(r.rule)} <span class="badge ${SEVC[r.sev]}">${r.sev}</span>${r.hard_gate?' <span class="hg">● HardGate</span>':''}</h3>
    <p class="kv">口径: ${esc(r.A)} / ${esc(r.B)} ≥ ${r.threshold} ｜ expected: ${esc(JSON.stringify(s.expected))}</p>
    ${s.note?`<p class="muted">注: ${esc(s.note)}</p>`:''}
    <div class="rowpair">${row(p,'bad')}${row(n,'good')}</div>
    <p class="muted" style="margin-top:6px">高亮 = 两行取值不同的触发字段（共 ${diffKeys.length} 处）。</p>`;}
sel.onchange=()=>show(sel.value);
$('#sample-search').oninput=fillSelect;
fillSelect();
</script>
</body>
</html>
"""


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "reports" / "geogov_dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = build()
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
