#!/usr/bin/env python3
"""GeoGov 芜湖数据质量检查页 v2 — 协议对齐版构建器（单文件 HTML）。

相比 v1（visit-research/experiments/wuhu_demo/build_qc_page.py, 2026-09-20）：
  1. 决策词汇对齐 dq_verdict_protocol_v1.json（v1.0.1）：Severity C0-C3、
     AdmissionAction、GateDecision 形状的单店裁决卡、fail-closed 口径说明；
  2. 纳入 V1-FROZEN 31 条规则注册表（维度/子项/口径/阈值/HardGate）；
  3. 批次证据面板：可复算子集给出实测通过率；不可复算规则显式列 N/A（不猜）；
  4. 结论按协议纪律定级：页面只产「建议裁决」，授权动作留给人（G4/Not promotion）；
  5. 离线可用：Leaflet 在线时出瓦片地图，不可用时自动降级为 canvas 散点图。

数据敏感性：门店名/地址/坐标属客户数据 —— 生成物默认写到 ~/Downloads，不进公开仓。
仓库只收本脚本。输入：
  --stores  qc_stores.json       (1070 条：code/name/address/district/sp/lat/lng/quality_state/quality_level/otm)
  --detail  wuhu_detail.json     (四层评估明细：①-⑥ + 系统结论/建议动作，按店编码)
  --rules   rules/dq_rules_v1_frozen.json
  --protocol protocol/dq_verdict_protocol_v1.json

用法: python3 scripts/build_wuhu_qc_page.py --stores ... --detail ... [--out ...]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 状态 → 规则族映射（升级新增；仅映射数据可证实的族，逐规则证据见规则注册表）
STATE_TO_RULES = {
    "结构残缺_低风险": ("R010/R014/R017", "地址结构/组分", "C2"),
    "不一致_待修": ("R018/R019/R025", "区县×坐标一致性", "C2"),
    "不一致_POI佐证填报区(核坐标)": ("R021/R031", "POI 佐证与跨源裁决", "C2"),
    "跨区钉死_铁证": ("R023", "异常坐标复用(HardGate)", "C1"),
    "边界不确定": ("R018/R031", "区界待人工判定", "C2"),
    "同点待核": ("R024", "50m 紧邻风险信号", "C3"),
    "通过": ("—", "未触发", "—"),
}


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def severity_of(level: str) -> str:
    return {"重错漏": "C1", "轻错漏": "C2", "无错漏": "—"}.get(level, "C2")


def compute_evidence(stores: list[dict], detail: dict, rules_doc: dict) -> dict:
    """可复算规则子集（只用门店字段，证据合同见 rules/dq_rules_v1_frozen.json）。"""
    n = len(stores)
    codes = [s["code"] for s in stores]

    def rate(ok: int) -> float:
        return round(ok / n, 4) if n else 0.0

    lat_ok = sum(1 for s in stores if isinstance(s.get("lat"), (int, float)) and 30.5 <= s["lat"] <= 31.8)
    lng_ok = sum(1 for s in stores if isinstance(s.get("lng"), (int, float)) and 117.5 <= s["lng"] <= 119.0)
    non_zero = sum(1 for s in stores if (s.get("lat") or 0) != 0 and (s.get("lng") or 0) != 0)
    name_ok = sum(1 for s in stores if isinstance(s.get("name"), str) and len(s["name"].strip()) >= 2)
    uniq = len(set(codes))
    # R023: 字节级同坐标 + 不同编码（跨区钉死铁证在四层明细中已判）
    coord_groups: dict[tuple, list] = {}
    for s in stores:
        coord_groups.setdefault((s.get("lat"), s.get("lng")), []).append(s["code"])
    dup_codes = {c for g in coord_groups.values() if len(g) > 1 for c in g}
    cross_district = [s for s in stores if "跨区钉死" in str(s.get("quality_state", ""))]
    hard_gate_fail = len(cross_district)

    return {
        "evaluated": [
            {"rule": "R001/R011 店编码非空唯一", "dim": "规范性/完整性", "sev": "C1",
             "value": f"{uniq}/{n}", "pass": uniq == n, "threshold": "=1.0"},
            {"rule": "R002/R012 店名非空且长度≥2", "dim": "规范性/完整性", "sev": "C2",
             "value": f"{name_ok}/{n}", "pass": name_ok == n, "threshold": "=1.0"},
            {"rule": "R008 lng ∈ [117.5,119.0]", "dim": "规范性", "sev": "C1",
             "value": f"{lng_ok}/{n}", "pass": lng_ok == n, "threshold": "=1.0"},
            {"rule": "R009 lat ∈ [30.5,31.8]", "dim": "规范性", "sev": "C1",
             "value": f"{lat_ok}/{n}", "pass": lat_ok == n, "threshold": "=1.0"},
            {"rule": "R015 经纬度非空且≠(0,0)", "dim": "完整性", "sev": "C1",
             "value": f"{non_zero}/{n}", "pass": non_zero == n, "threshold": "=1.0"},
            {"rule": "R022 店编码全表唯一", "dim": "准确性", "sev": "C1",
             "value": f"{uniq}/{n}", "pass": uniq == n, "threshold": "=1.0"},
            {"rule": "R023 跨区钉死（四层明细判定）", "dim": "准确性", "sev": "C1",
             "value": f"违规 {hard_gate_fail} 条", "pass": hard_gate_fail == 0, "threshold": "=0 条"},
            {"rule": "R018 区县×坐标一致（四层明细④）", "dim": "准确性", "sev": "C2",
             "value": f"{sum(1 for v in detail.values() if v.get('coord_match')=='与填报区一致')}/{n} 一致",
             "pass": False, "threshold": "≥0.98"},
        ],
        "unavailable": [
            "R003/R004/R005 行政区划合法性（需民政部码表比对，证据未随数据集留存）",
            "R019/R025/R026 第二源（高德）交叉验证（证据未随数据集留存）",
            "R020/R021 POI 命中率与官方 adcode（POI 快照未留存，仅存命中文案）",
            "R028 现势性（仅报告风险，协议明确不判合格）",
            "R029 文件可访问性（批次级，非门店级）",
        ],
        "same_coord_groups": sum(1 for g in coord_groups.values() if len(g) > 1),
        "dup_stores": len(dup_codes),
        "quality_levels": dict(Counter(s.get("quality_level", "") for s in stores)),
    }


def build(stores_path: Path, detail_path: Path, rules_path: Path, protocol_path: Path) -> str:
    stores = load_json(stores_path)
    detail = load_json(detail_path)
    rules_doc = load_json(rules_path)
    protocol = load_json(protocol_path)
    samples = {s["rule_id"]: s for s in load_jsonl(rules_path.parent / "rule_samples_v1.jsonl")}

    for s in stores:
        d = detail.get(s["code"], {})
        s.update({k: d.get(k, "") for k in ("addr_q", "dist_match", "tencent_dist", "coord_match", "dup", "poi", "conclusion", "action")})
        s["sev"] = severity_of(s.get("quality_level", ""))
        fam = STATE_TO_RULES.get(str(s.get("quality_state", "")).split(" | ")[0], ("—", "未映射", "—"))
        s["rules"], s["rule_family"], s["rule_sev"] = fam

    evidence = compute_evidence(stores, detail, rules_doc)
    data = {
        "protocol_version": protocol["protocol_version"],
        "batch": "芜湖全量 · 1,070 店 · 2026-09 检查（V1-FROZEN 检测器）",
        "counts": {
            "total": len(stores),
            "levels": evidence["quality_levels"],
            "hard_gate_fail": sum(1 for s in stores if "跨区钉死" in str(s.get("quality_state", ""))),
            "same_coord_groups": evidence["same_coord_groups"],
            "dup_stores": evidence["dup_stores"],
        },
        "rules": rules_doc["rules"],
        "hard_gates": rules_doc["hard_gates"],
        "severity_levels": rules_doc["severity_levels"],
        "batch_verdict_rule": rules_doc["batch_verdict"],
        "invariants": protocol["invariants"],
        "enums": {
            "admission": protocol["$defs"]["AdmissionAction"]["enum"],
            "disposition": protocol["$defs"]["GovernanceDisposition"]["enum"],
            "severity": protocol["$defs"]["Severity"]["enum"],
        },
        "evidence": evidence,
        "samples_available": sorted(samples.keys()),
        "stores": stores,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return TEMPLATE.replace("__DATA__", payload)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GeoGov · 芜湖数据质量检查（协议对齐版）</title>

<style>
:root{--ink:#1a2332;--paper:#f7f5f0;--card:#fff;--line:#d8d3c8;--accent:#0f4c81;
--c0:#b42318;--c1:#d97706;--c2:#0e7490;--c3:#6b7280;--ok:#15803d;--bad:#b42318;--warn:#b45309}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.55}
header{background:var(--ink);color:#fff;padding:20px 28px}
header h1{font-size:20px;font-weight:600}
header .sub{font-size:13px;opacity:.85;margin-top:5px}
header .badge{display:inline-block;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);border-radius:20px;padding:2px 10px;font-size:11.5px;margin-right:6px}
main{max-width:1240px;margin:0 auto;padding:20px}
h2{font-size:16px;margin:18px 0 10px;color:var(--accent)}
h3{font-size:13.5px;margin:12px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin-bottom:14px}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:14px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.kpi .v{font-size:24px;font-weight:700;line-height:1.2}
.kpi .l{font-size:12px;color:#5a6270;margin-top:2px}
.kpi.green .v{color:var(--ok)}.kpi.amber .v{color:var(--warn)}.kpi.red .v{color:var(--bad)}
.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.step{background:#fbfaf7;border:1px solid var(--line);border-radius:8px;padding:12px}
.step .n{display:inline-flex;width:22px;height:22px;border-radius:50%;background:var(--ok);color:#fff;align-items:center;justify-content:center;font-size:12px;font-weight:700;margin-bottom:6px}
.step .t{font-weight:600;font-size:13px}
.step .d{font-size:12px;color:#59606b;margin-top:3px}
.step .u{font-size:11.5px;color:#0f4c81;margin-top:5px;border-top:1px dashed var(--line);padding-top:5px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#efeadf;font-weight:600;white-space:nowrap}
.badge2{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11.5px;font-weight:600;color:#fff}
.bC0{background:var(--c0)}.bC1{background:var(--c1)}.bC2{background:var(--c2)}.bC3{background:var(--c3)}.bX{background:#8a8f98}
.pass{color:var(--ok);font-weight:700}.fail{color:var(--bad);font-weight:700}.na{color:#8a8f98}
#map{height:420px;border-radius:8px;border:1px solid var(--line);background:#eef1f4}
.layout{display:grid;grid-template-columns:1.15fr .85fr;gap:14px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.filters select,.filters input{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:#fff}
.filters input[type=search]{flex:1;min-width:200px}
#ledger{max-height:520px;overflow:auto}
#ledger tr{cursor:pointer}#ledger tr:hover{background:#f5f2ea}
.tag{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11px;font-weight:600;color:#fff}
.tG{background:var(--ok)}.tY{background:#e8710a}.tR{background:var(--bad)}
.ev{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0}
.ev div{background:#fbfaf7;border:1px solid var(--line);border-radius:6px;padding:7px 10px;font-size:12.5px}
.ev b{display:block;font-size:11px;color:#6a7280;font-weight:600}
.gd{background:#0f1720;color:#d7e3ee;border-radius:8px;padding:12px;font-size:12px;overflow:auto;line-height:1.5;white-space:pre-wrap;word-break:break-word}
.inv{border-left:4px solid var(--accent);padding:7px 11px;margin:6px 0;background:#f2f6fa;border-radius:0 6px 6px 0;font-size:12.5px}
.note{background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:10px 12px;font-size:12.5px;color:#7c2d12;margin-top:10px}
footer{text-align:center;color:#8a8f98;font-size:11.5px;padding:16px}
@media(max-width:1000px){.layout,.kpis,.steps{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>GeoGov · 芜湖全量数据质量检查 <span style="font-weight:400;opacity:.8">（协议对齐版 v2）</span></h1>
  <div class="sub" id="sub"></div>
  <div style="margin-top:8px"><span class="badge" id="pb"></span><span class="badge">V1-FROZEN 31 规则</span><span class="badge">fail-closed：缺证据不猜</span><span class="badge">仅产建议裁决，授权留人</span></div>
</header>
<main>
  <h2>从全量概览到逐店核查</h2>
  <div class="card"><div class="steps" id="steps"></div></div>

  <div class="kpis" id="kpis"></div>

  <div class="layout">
    <div>
      <div class="card" style="padding:8px"><div id="map"></div></div>
      <div class="card">
        <h3 style="margin-top:0">台账 <span class="na" id="ledger-n"></span></h3>
        <div class="filters">
          <select id="f-lv"><option value="">全部层级</option><option>无错漏</option><option>轻错漏</option><option>重错漏</option></select>
          <select id="f-rules"><option value="">全规则族</option></select>
          <input type="search" id="f-q" placeholder="店编码 / 店名 / 区县…">
        </div>
        <div id="ledger"><table id="lt"><thead><tr><th>店编码</th><th>店名</th><th>区县</th><th>层级</th><th>状态</th><th>结论</th></tr></thead><tbody id="lb"></tbody></table></div>
      </div>
    </div>
    <div>
      <div class="card" id="detail"><p class="na">点选台账或地图点位查看单店核查详情。</p></div>
    </div>
  </div>

  <h2>批次证据与建议裁决</h2>
  <div class="card">
    <h3 style="margin-top:0">可复算子集（只用本数据集字段）</h3>
    <table id="ev-table"></table>
    <h3>不可复算（证据未随数据集留存 → N/A，不猜测）</h3>
    <table id="na-table"></table>
    <div class="note" id="verdict-note"></div>
  </div>

  <h2>V1-FROZEN 规则注册表（31 条检测器）</h2>
  <div class="card">
    <div class="filters">
      <select id="r-dim"><option value="">全维度</option></select>
      <select id="r-sev"><option value="">全级别</option><option>C0</option><option>C1</option><option>C2</option><option>C3</option></select>
      <label class="na" style="font-size:12.5px;display:flex;align-items:center;gap:5px"><input type="checkbox" id="r-hg">仅 HardGate</label>
    </div>
    <table id="rules-table"></table>
  </div>

  <h2>协议不变量（本页按此裁决）</h2>
  <div class="card" id="invariants"></div>
</main>
<footer id="foot"></footer>

<script>
const D = __DATA__;
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const SEV={'—':'bX','C0':'bC0','C1':'bC1','C2':'bC2','C3':'bC3'};
const LV={'无错漏':['tG','#188038'],'轻错漏':['tY','#e8710a'],'重错漏':['tR','#d93025']};

$('#sub').textContent=`${D.batch} ｜ 协议 ${D.protocol_version} ｜ 门店 ${D.counts.total}`;
$('#pb').textContent=`协议 ${D.protocol_version}`;
$('#foot').textContent='GeoGov · 数据：芜湖全量检查（2026-09）+ V1-FROZEN 规则 + DQ 裁决协议 v1.0.1 · 构建：scripts/build_wuhu_qc_page.py';

// intro steps (rebuilt from 好来SRP升级方案 PPT slide5)
const STEPS=[
 ['全量质量概览','多少家店有问题、问题分几类','判断该优先处理哪一档'],
 ['排序识别疑点','按问题类型/严重级排序，找出该先处理的店','锁定首批处理对象'],
 ['地图·台账联动','从地图或台账选中疑点店，核对空间位置与门店身份','防止“张冠李戴”'],
 ['单店核查依据','点开核查面板：证据分层、关键点、建议动作','形成可解释的处理意见'],
 ['按建议业务确认','选定目标区县，打开问题状态、系统建议与人工确认结果','闭环：改数据 or 改清单']];
$('#steps').innerHTML=STEPS.map(([t,d,u],i)=>`<div class="step"><div class="n">${i+1}</div><div class="t">${esc(t)}</div><div class="d">${esc(d)}</div><div class="u">业务用途：${esc(u)}</div></div>`).join('');

// KPIs
const L=D.counts.levels, tot=D.counts.total;
$('#kpis').innerHTML=[
 ['',tot,'门店总数',''],['',tot,'全量检查覆盖',''],
 ['green',L['无错漏']||0,`无错漏 ${((L['无错漏']||0)/tot*100).toFixed(0)}%`,'green'],
 ['amber',L['轻错漏']||0,'轻错漏','amber'],
 ['red',L['重错漏']||0,'重错漏','red'],
 ['red',D.counts.hard_gate_fail,'HardGate 违规（跨区钉死）','red']]
 .map(([c,v,l])=>`<div class="kpi ${c}"><div class="v">${v}</div><div class="l">${esc(l)}</div></div>`).join('');

// ---- map (leaflet with canvas fallback)
const pts=D.stores.filter(s=>s.lat&&s.lng);
let map=null;
function drawCanvas(){const c=document.createElement('canvas');const el=$('#map');el.innerHTML='';
 c.width=el.clientWidth||900;c.height=420;el.appendChild(c);const x=c.getContext('2d');
 const lo=[...pts].map(p=>p.lng),la=[...pts].map(p=>p.lat);
 const x0=Math.min(...lo),x1=Math.max(...lo),y0=Math.min(...la),y1=Math.max(...la);
 const nx=v=>(v-x0)/(x1-x0)*(c.width-40)+20,ny=v=>(y1-v)/(y1-y0)*(c.height-40)+20;
 x.fillStyle='#f7f5f0';x.fillRect(0,0,c.width,c.height);
 for(const p of pts){x.fillStyle=(LV[p.quality_level]||['','#5f6368'])[1];x.beginPath();x.arc(nx(p.lng),ny(p.lat),p.quality_level==='重错漏'?4:2.5,0,7);x.fill();}
 x.fillStyle='#59606b';x.font='12px sans-serif';x.fillText('离线模式：点位散点渲染（在线时显示地图瓦片）',12,18);return c;}
// canvas-first：先出离线散点图（绝不阻塞），Leaflet 异步到达后再升级为地图
const cv=drawCanvas();
function upgradeMap(){
 if(map||!window.L) return;
 const el=$('#map'); el.innerHTML='';
 map=L.map(el,{scrollWheelZoom:true}).setView([31.15,118.35],10);
 L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap'}).addTo(map);
 pts.forEach(s=>L.circleMarker([s.lat,s.lng],{radius:s.quality_level==='重错漏'?6:4,fillColor:(LV[s.quality_level]||['','#5f6368'])[1],color:'#fff',weight:1.2,fillOpacity:.9})
  .addTo(map).bindPopup(`<b>${esc(s.name)}</b><br>${esc(s.code)} · ${esc(s.district)}<br>${esc(s.quality_state)}<br><a href="javascript:void(0)" onclick="window.__sel('${esc(s.code)}')">查看核查 →</a>`));
}
// 在线底图为可选项：点击才注入 Leaflet（避免不可达 CDN 拖住页面 load 事件）
(function mountBtn(){
 const btn=document.createElement('button');
 btn.textContent='加载在线底图（OSM）';
 btn.style.cssText='position:absolute;right:10px;top:10px;z-index:900;font:inherit;font-size:12px;padding:5px 10px;border:1px solid #d8d3c8;border-radius:6px;background:#fff;cursor:pointer';
 btn.onclick=()=>{btn.disabled=true;btn.textContent='加载中…';
  const css=document.createElement('link');css.rel='stylesheet';css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';document.head.appendChild(css);
  const js=document.createElement('script');js.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
  js.onload=()=>{upgradeMap();btn.remove();};
  js.onerror=()=>{btn.textContent='底图不可达（离线）';setTimeout(()=>btn.remove(),2500);};
  document.head.appendChild(js);};
 $('#map').style.position='relative';$('#map').appendChild(btn);
})();

// ---- ledger
let view=D.stores.slice();
const ruleOpts=[...new Set(D.stores.map(s=>s.rules))];
$('#f-rules').innerHTML+=[...new Set(ruleOpts)].map(r=>`<option>${esc(r)}</option>`).join('');
function renderLedger(){
  const lv=$('#f-lv').value,ru=$('#f-rules').value,q=$('#f-q').value.trim().toLowerCase();
  view=D.stores.filter(s=>(!lv||s.quality_level===lv)&&(!ru||s.rules===ru)&&(!q||(s.code+s.name+s.district).toLowerCase().includes(q)));
  $('#ledger-n').textContent=`（${view.length} / ${D.stores.length}）`;
  $('#lb').innerHTML=view.map(s=>{const t=LV[s.quality_level]||['',''];
   return `<tr onclick="window.__sel('${esc(s.code)}')"><td>${esc(s.code)}</td><td>${esc(s.name)}</td><td>${esc(s.district)}</td><td><span class="tag ${t[0]}">${esc(s.quality_level)}</span></td><td>${esc(s.quality_state)}</td><td class="na">${esc((s.conclusion||'').slice(0,26))}</td></tr>`}).join('');
}
['#f-lv','#f-rules','#f-q'].forEach(k=>$(k).oninput=renderLedger);
renderLedger();

// ---- detail
window.__sel=code=>{
  const s=D.stores.find(x=>x.code===code);if(!s)return;
  const gd={protocol_version:D.protocol_version,action:s.quality_level==='重错漏'?'REVIEW':s.quality_level==='轻错漏'?'ALLOW_WITH_LIMITS':'ALLOW',
   disposition:s.quality_level==='重错漏'?'REPAIR_REQUIRED':s.quality_level==='轻错漏'?'NONE':'NONE',
   scope:`store://${s.code}`,hard_gates_all_pass:!String(s.quality_state||'').includes('跨区钉死'),
   rationale:`${s.quality_state}（规则族 ${s.rules} · ${s.rule_family}）${s.conclusion?'；结论：'+s.conclusion:''}`,
   decided_by:'GeoGov 建议生成器（非授权人）',decided_at:'2026-09-17T00:00:00+08:00',immutable:true,supersedes:null};
  $('#detail').innerHTML=`<h3 style="margin-top:0">${esc(s.name)} <span class="tag ${(LV[s.quality_level]||['',''])[0]}">${esc(s.quality_level)}</span> <span class="badge2 ${SEV[s.sev]||'bX'}">${esc(s.sev)}</span></h3>
   <p class="na">${esc(s.code)} · ${esc(s.district)} · SP ${esc(s.sp)} · ${s.lat}, ${s.lng}</p>
   <p style="margin-top:6px">${esc(s.address||'')}</p>
   <div class="ev">
    <div><b>① 地址质量</b>${esc(s.addr_q||'—')}</div>
    <div><b>② 地址区 vs 填报区</b>${esc(s.dist_match||'—')}</div>
    <div><b>③ 坐标所在区（腾讯）</b>${esc(s.tencent_dist||'—')}</div>
    <div><b>④ 坐标 vs 填报区</b>${esc(s.coord_match||'—')}</div>
    <div><b>⑤ 坐标重复</b>${esc(s.dup||'—')}</div>
    <div><b>⑥ POI 匹配</b>${esc(s.poi||'—')}</div>
   </div>
   <p><b>规则族</b> ${esc(s.rules)} — ${esc(s.rule_family)}</p>
   ${s.conclusion?`<p style="margin-top:6px"><b>系统结论</b> ${esc(s.conclusion)}</p>`:''}
   ${s.action?`<div style="padding:10px;background:#e6f4ea;border-radius:8px;margin-top:8px"><div style="font-size:12px;font-weight:700;color:#188038">建议动作</div><div style="font-size:12.5px;margin-top:3px">${esc(s.action)}</div></div>`:''}
   <h3>按协议投影的裁决卡（建议，待授权人确认）</h3>
   <pre class="gd">${esc(JSON.stringify(gd,null,1))}</pre>
   <p class="na" style="margin-top:6px">fail-closed：本卡仅由已留存证据生成；未评规则不参与 action 推断。</p>`;
  if(map)map.setView([s.lat,s.lng],13);
};

// ---- evidence
$('#ev-table').innerHTML='<tr><th>规则</th><th>维度</th><th>级</th><th>实测</th><th>阈值</th><th>结论</th></tr>'+
 D.evidence.evaluated.map(e=>`<tr><td>${esc(e.rule)}</td><td>${esc(e.dim)}</td><td><span class="badge2 ${SEV[e.sev]||'bX'}">${e.sev}</span></td><td>${esc(e.value)}</td><td class="na">${esc(e.threshold)}</td><td class="${e.pass?'pass':'fail'}">${e.pass?'PASS':'FAIL'}</td></tr>`).join('');
$('#na-table').innerHTML='<tr><th>规则</th><th>状态</th></tr>'+D.evidence.unavailable.map(u=>`<tr><td>${esc(u)}</td><td class="na">N/A — 证据未留存</td></tr>`).join('');
const gFail=D.counts.hard_gate_fail, accFail=D.evidence.evaluated.filter(e=>!e.pass).length;
$('#verdict-note').innerHTML=`<b>建议裁决（需授权人确认，页面不自动晋升）：</b>${gFail?`HardGate 存在 ${gFail} 条违规（R023 跨区钉死）→ 协议口径「Hard Gate 任一 C1 失败 = BLOCK，覆盖任何 ALLOW 语义」→ <b>建议 BLOCK（整改后重评）</b>`:'HardGate 全过'}。
 另有 ${accFail} 项可复算规则未达阈值。批次三态判定式：<span class="na">${esc(D.batch_verdict_rule)}</span>。
 <br><b>诚实边界：</b>本批尚未完成逐规则 A/B 全量计数（R019/R020/R021/R025/R026 等第二源与 POI 证据未随数据集留存）——按 fail-closed 口径记 N/A，不以猜测补齐。`;

// ---- rules
$('#r-dim').innerHTML+=[...new Set(D.rules.map(r=>r.dim))].map(d=>`<option>${esc(d)}</option>`).join('');
function renderRules(){const d=$('#r-dim').value,s=$('#r-sev').value,h=$('#r-hg').checked;
 const rs=D.rules.filter(r=>(!d||r.dim===d)&&(!s||r.sev===s)&&(!h||r.hard_gate));
 $('#rules-table').innerHTML='<tr><th>ID</th><th>维度/子项</th><th>字段</th><th>规则</th><th>口径 A/B</th><th>阈值</th><th>级</th><th>HG</th></tr>'+
  rs.map(r=>`<tr><td><b>${r.id}</b></td><td>${esc(r.dim)}<br><span class="na">${esc(r.sub)}</span></td><td>${esc(r.field)}</td><td>${esc(r.rule)}</td><td class="na">${esc(r.A)} / ${esc(r.B)}</td><td>${r.threshold}</td><td><span class="badge2 ${SEV[r.sev]||'bX'}">${r.sev}</span></td><td>${r.hard_gate?'<b style="color:var(--bad)">●</b>':''}</td></tr>`).join('');}
['#r-dim','#r-sev','#r-hg'].forEach(k=>$(k).oninput=renderRules);renderRules();
$('#invariants').innerHTML=D.invariants.map(x=>`<div class="inv">${esc(x)}</div>`).join('');
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stores", required=True)
    ap.add_argument("--detail", required=True)
    ap.add_argument("--rules", default=str(ROOT / "rules" / "dq_rules_v1_frozen.json"))
    ap.add_argument("--protocol", default=str(ROOT / "protocol" / "dq_verdict_protocol_v1.json"))
    ap.add_argument("--out", default=str(Path.home() / "Downloads" / "GeoGov_芜湖数据质量检查_v2.html"))
    a = ap.parse_args()
    html = build(Path(a.stores), Path(a.detail), Path(a.rules), Path(a.protocol))
    out = Path(a.out)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())