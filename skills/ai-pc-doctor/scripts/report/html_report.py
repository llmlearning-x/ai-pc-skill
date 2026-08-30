"""交互式 HTML Dashboard（V0.3 像素科技风）：单文件、自包含、无 CDN/外链依赖。

- 像素/复古终端风：深色底 + 霓虹强调色 + CSS 像素描边与切角，无外部字体。
- 模式主题色（V0.3）：quick=琥珀 / standard=青 / full=紫，注入 --accent 变量
  驱动标题/边框/表头/条形图等界面主题元素；语义色（PASS/FAIL/WARN）不变。
- 动效（纯 CSS keyframes + 少量 vanilla JS，全部离线可用）：
  背景网格/扫描线、标题打字机、数字 count-up、卡片 hover 发光、
  条形图生长动画、状态点呼吸闪烁；prefers-reduced-motion 下全部关闭。
- 九节结构（全中文）：设备概览 / 就绪度评分 / OpenVINO 状态 / 设备兼容性 /
  性能基准 / 生成式 AI 性能 / 模型容量评估 / 部署建议 / 问题与修复。
"""

import html
from pathlib import Path

# 霓虹配色
C_GREEN = "#39ff14"   # PASS / EXCELLENT
C_CYAN = "#00e5ff"    # RECOMMENDED / 主强调
C_MAGENTA = "#ff2e88"  # FAIL / NOT_RECOMMENDED
C_AMBER = "#ffb000"   # WARN / LIMITED / UNSUPPORTED
C_GREY = "#6b7280"    # SKIPPED / UNKNOWN

# 模式主题色：--accent 按模式注入，用于界面主题元素（标题/边框/表头/条形图等），
# 语义色（PASS 绿 / FAIL 品红 / WARN 琥珀 / RECOMMENDED 青）不受影响。
# quick=琥珀（轻量快速） standard=青（默认） full=紫（深度体检）
MODE_THEMES = {
    "quick": {"accent": "#ffb000", "rgb": "255,176,0",
              "label": "QUICK · 快速检查"},
    "standard": {"accent": "#00e5ff", "rgb": "0,229,255",
                 "label": "STANDARD · 标准体检"},
    "full": {"accent": "#b26bff", "rgb": "178,107,255",
             "label": "FULL · 完整体检"},
}
_DEFAULT_THEME = MODE_THEMES["standard"]

_CSS = """
:root{--bg:#0a0e1a;--panel:#101627;--line:#1e2a44;--txt:#c9d6e8;
--green:#39ff14;--cyan:#00e5ff;--magenta:#ff2e88;--amber:#ffb000;
--accent:#00e5ff;--accent-rgb:0,229,255;
--mono:'SF Mono','Cascadia Mono',Menlo,'PingFang SC','Microsoft YaHei',monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:var(--mono);
font-size:14px;letter-spacing:.3px}
/* 背景细网格 + 扫描线 */
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
background:repeating-linear-gradient(0deg,transparent 0 31px,rgba(var(--accent-rgb),.05) 31px 32px),
repeating-linear-gradient(90deg,transparent 0 31px,rgba(var(--accent-rgb),.05) 31px 32px)}
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:1;
background:repeating-linear-gradient(0deg,rgba(0,0,0,.14) 0 2px,transparent 2px 4px);
animation:scan 8s linear infinite}
@keyframes scan{from{transform:translateY(-4px)}to{transform:translateY(4px)}}
header{position:relative;z-index:2;padding:36px 40px;border-bottom:2px solid var(--accent);
background:linear-gradient(180deg,rgba(var(--accent-rgb),.08),transparent)}
header h1{margin:0;font-size:28px;color:var(--accent);
text-shadow:0 0 12px rgba(var(--accent-rgb),.6);
letter-spacing:3px;min-height:34px}
header h1 .cursor{display:inline-block;width:.6em;background:var(--accent);
animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
header p{margin:8px 0 0;color:#7c8db0;font-size:12px}
main{position:relative;z-index:2;max-width:960px;margin:24px auto;padding:0 16px}
/* 像素切角面板 */
section{background:var(--panel);margin-bottom:18px;position:relative;
clip-path:polygon(0 10px,10px 10px,10px 0,calc(100% - 10px) 0,calc(100% - 10px) 10px,
100% 10px,100% calc(100% - 10px),calc(100% - 10px) calc(100% - 10px),
calc(100% - 10px) 100%,10px 100%,10px calc(100% - 10px),0 calc(100% - 10px));
box-shadow:0 0 0 2px var(--line),0 0 18px rgba(var(--accent-rgb),.06)}
section:hover{box-shadow:0 0 0 2px var(--accent),0 0 22px rgba(var(--accent-rgb),.18)}
h2{font-size:15px;margin:0;padding:16px 24px;cursor:pointer;user-select:none;
color:var(--accent);display:flex;justify-content:space-between;letter-spacing:2px}
h2::before{content:'▸ ';color:var(--magenta)}
h2 .arrow{color:#5a6b8f;font-size:12px;transition:transform .2s}
section.collapsed h2 .arrow{transform:rotate(-90deg)}
section.collapsed .body{display:none}
.body{padding:2px 24px 22px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left}
th{background:#0d1322;color:var(--accent);letter-spacing:1px}
tr:hover td{background:rgba(var(--accent-rgb),.04)}
.muted{color:#7c8db0;font-size:12px}
ul{padding-left:20px;margin:8px 0}
li{margin:5px 0}
code{background:#0d1322;border:1px solid var(--line);padding:1px 6px;
font-size:12px;color:var(--amber)}
/* 像素徽章 / 标签 */
.badge{display:inline-block;padding:2px 10px;font-size:11px;font-weight:700;
letter-spacing:1px;border:2px solid currentColor;background:rgba(0,0,0,.35)}
.b-green{color:var(--green);box-shadow:0 0 8px rgba(57,255,20,.35)}
.b-cyan{color:var(--cyan);box-shadow:0 0 8px rgba(0,229,255,.35)}
.b-magenta{color:var(--magenta);box-shadow:0 0 8px rgba(255,46,136,.35)}
.b-amber{color:var(--amber);box-shadow:0 0 8px rgba(255,176,0,.35)}
.b-grey{color:var(--grey)}
/* 状态像素块（呼吸） */
.px{display:inline-block;width:12px;height:12px;margin-right:6px;
vertical-align:-1px;animation:breath 2s ease-in-out infinite}
@keyframes breath{0%,100%{opacity:1}50%{opacity:.35}}
.px-green{background:var(--green);box-shadow:0 0 8px var(--green)}
.px-magenta{background:var(--magenta);box-shadow:0 0 8px var(--magenta)}
.px-amber{background:var(--amber);box-shadow:0 0 8px var(--amber)}
.px-grey{background:var(--grey)}
/* 就绪度环形仪表 */
.gauge{width:190px;height:190px;border-radius:50%;display:grid;place-items:center;
margin:14px 0;background:conic-gradient(var(--cyan) 0%,#16203a 0)}
.gauge-inner{width:140px;height:140px;border-radius:50%;background:var(--bg);
display:grid;place-items:center;box-shadow:inset 0 0 20px rgba(0,0,0,.7)}
.gauge-num{font-size:40px;font-weight:700;color:var(--cyan);
text-shadow:0 0 14px currentColor}
.gauge-max{font-size:13px;color:#7c8db0}
/* 像素条形图（生长动画） */
.bar-row{display:flex;align-items:center;margin:8px 0;font-size:12px}
.bar-row .name{width:64px;color:var(--accent);font-weight:700}
.bar-track{flex:1;background:#0d1322;border:1px solid var(--line);height:20px}
.bar-fill{height:100%;width:0;animation:grow 1s ease-out forwards;
background-image:repeating-linear-gradient(90deg,rgba(0,0,0,.25) 0 4px,transparent 4px 8px)}
@keyframes grow{to{width:var(--w)}}
.bar-cpu{background-color:var(--accent);box-shadow:0 0 10px rgba(var(--accent-rgb),.5)}
.bar-gpu{background-color:var(--green);box-shadow:0 0 10px rgba(57,255,20,.5)}
.bar-npu{background-color:var(--amber);box-shadow:0 0 10px rgba(255,176,0,.5)}
.bar-val{width:150px;text-align:right;color:#9fb2d0}
/* GenAI 大数字卡片 */
.cards{display:flex;flex-wrap:wrap;gap:12px;margin:12px 0}
.card{flex:1 1 150px;background:#0d1322;border:2px solid var(--line);padding:14px;
text-align:center;transition:box-shadow .2s,border-color .2s;
clip-path:polygon(0 8px,8px 8px,8px 0,calc(100% - 8px) 0,calc(100% - 8px) 8px,
100% 8px,100% 100%,0 100%)}
.card:hover{border-color:var(--green);box-shadow:0 0 16px rgba(57,255,20,.3)}
.card .v{font-size:26px;font-weight:700;color:var(--green);
text-shadow:0 0 12px rgba(57,255,20,.5)}
.card .u{font-size:12px;color:#7c8db0}
.card .k{font-size:12px;color:#8fa3c8;margin-top:6px}
/* 推荐模型卡片 */
.rec-card{background:#0d1322;border:2px solid var(--line);padding:14px 16px;
margin:10px 0;transition:box-shadow .2s;
clip-path:polygon(0 8px,8px 8px,8px 0,calc(100% - 8px) 0,calc(100% - 8px) 8px,
100% 8px,100% 100%,0 100%)}
.rec-card:hover{border-color:var(--accent);box-shadow:0 0 16px rgba(var(--accent-rgb),.25)}
.rec-head{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.rec-name{font-weight:700;color:#e6eefc}
.stars{color:var(--amber);letter-spacing:2px;text-shadow:0 0 8px rgba(255,176,0,.5)}
.rec-meta{margin-top:8px;font-size:12px;color:#9fb2d0}
h4{color:var(--accent);letter-spacing:1px;margin:16px 0 8px}
/* 本地体验 Demo 卡片 */
.demo-box{display:flex;align-items:center;gap:18px;background:#0d1322;border:2px solid var(--accent);
padding:18px 22px;margin:12px 0;box-shadow:0 0 20px rgba(var(--accent-rgb),.15);
clip-path:polygon(0 8px,8px 8px,8px 0,calc(100% - 8px) 0,calc(100% - 8px) 8px,
100% 8px,100% 100%,0 100%)}
.demo-icon{font-size:36px;line-height:1}
.demo-info{flex:1}
.demo-info h4{margin:0 0 6px;color:var(--accent);letter-spacing:1px}
.demo-url{font-size:15px;margin:8px 0}
.demo-url a{color:var(--cyan);text-decoration:none;font-weight:700;
box-shadow:0 0 10px rgba(0,229,255,.3)}
.demo-url a:hover{text-decoration:underline}
"""

_JS = """
var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* 标题打字机 */
(function(){
  var el = document.getElementById('title');
  if (!el) return;
  var text = el.getAttribute('data-text') || '';
  if (reduced) { el.textContent = text; return; }
  var i = 0;
  (function tick(){
    if (i <= text.length) {
      el.innerHTML = text.slice(0, i) + '<span class="cursor">&nbsp;</span>';
      i++; setTimeout(tick, 55);
    }
  })();
})();

/* 数字 count-up（data-count / data-decimals） */
function countUp(el){
  var target = parseFloat(el.getAttribute('data-count'));
  var dec = parseInt(el.getAttribute('data-decimals') || '0', 10);
  if (isNaN(target)) return;
  if (reduced) { el.textContent = target.toFixed(dec); return; }
  var t0 = null, dur = 900;
  function step(ts){
    if (!t0) t0 = ts;
    var p = Math.min((ts - t0) / dur, 1);
    el.textContent = (target * p).toFixed(dec);
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
document.querySelectorAll('[data-count]').forEach(countUp);

/* 就绪度环形仪表扫动 */
(function(){
  var g = document.querySelector('.gauge[data-gauge]');
  if (!g) return;
  var score = parseFloat(g.getAttribute('data-gauge'));
  var color = g.getAttribute('data-color') || '#00e5ff';
  function setP(p){
    g.style.background = 'conic-gradient(' + color + ' ' + (p * 3.6) + 'deg, #16203a 0deg)';
  }
  if (reduced) { setP(score); return; }
  var t0 = null, dur = 1000;
  function step(ts){
    if (!t0) t0 = ts;
    var k = Math.min((ts - t0) / dur, 1);
    setP(score * k);
    if (k < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
})();

/* 节折叠 */
document.querySelectorAll('section > h2').forEach(function(h){
  h.addEventListener('click', function(){
    h.parentElement.classList.toggle('collapsed');
  });
});
"""

# reduced-motion：关掉全部动画
_CSS_REDUCED = """
@media (prefers-reduced-motion: reduce){
*,*::before,*::after{animation:none!important;transition:none!important}
.bar-fill{width:var(--w)!important}
}
"""

_SECTIONS = [
    ("01", "设备概览"), ("02", "就绪度评分"), ("03", "OpenVINO 状态"),
    ("04", "设备兼容性"), ("05", "性能基准"), ("06", "生成式 AI 性能"),
    ("06a", "本地体验"), ("07", "模型容量评估"), ("08", "部署建议"), ("09", "问题与修复"),
]

# 等级 → 霓虹色 class
_GRADE_CLASS = {"EXCELLENT": "b-green", "RECOMMENDED": "b-cyan",
                "LIMITED": "b-amber", "NOT_RECOMMENDED": "b-magenta",
                "UNKNOWN": "b-grey"}
_STARS = {"EXCELLENT": "★★★★★", "RECOMMENDED": "★★★★",
          "LIMITED": "★★★", "NOT_RECOMMENDED": "✖", "UNKNOWN": "?"}
_STATUS_CLASS = {"PASS": "green", "FAIL": "magenta", "UNSUPPORTED": "amber",
                 "SKIPPED": "grey", "runtime_detected": "green",
                 "runtime_not_detected": "grey", "detected": "green",
                 "not_detected": "grey", "unknown": "amber"}


def _e(value) -> str:
    return html.escape("unknown" if value is None else str(value))


def _status_px(status) -> str:
    """状态像素块（呼吸闪烁）。"""
    cls = _STATUS_CLASS.get(str(status), "grey")
    return f"<span class='px px-{cls}'></span>{_e(status)}"


def _kv_table(rows: list) -> str:
    body = "".join(f"<tr><th>{_e(k)}</th><td>{v}</td></tr>" for k, v in rows)
    return f"<table>{body}</table>"


def _grid_table(headers: list, rows: list) -> str:
    head = "".join(f"<th>{_e(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def _section(num: str, title: str, content: str) -> str:
    return (f"<section><h2>{num} {title}"
            f"<span class='arrow'>&#9660;</span></h2>"
            f"<div class='body'>{content}</div></section>")


def _device_overview(r: dict) -> str:
    s, cpu, gpu, npu, mem = (r.get("system", {}), r.get("cpu", {}),
                             r.get("gpu", {}), r.get("npu", {}),
                             r.get("memory", {}))
    return _kv_table([
        ("操作系统", _e(f"{s.get('os', 'unknown')} {s.get('release', '')} "
                        f"({s.get('architecture', 'unknown')})")),
        ("CPU", _e(f"{cpu.get('model', 'unknown')} "
                   f"（物理 {cpu.get('physical_cores', '?')} 核 / "
                   f"逻辑 {cpu.get('logical_cores', '?')} 核）")),
        ("GPU", _e(gpu.get("gpu", "unknown"))),
        ("NPU", _status_px(npu.get("status", "unknown"))),
        ("内存", _e(f"{mem.get('total_gb', '?')} GB"
                    f"（可用 {mem.get('available_gb', '?')} GB）")),
    ])


def _score_color(score: int) -> str:
    if score >= 90:
        return C_GREEN
    if score >= 75:
        return C_CYAN
    if score >= 60:
        return C_AMBER
    return C_MAGENTA


def _readiness(r: dict) -> str:
    rs = r.get("readiness_score") or {}
    if rs.get("score") is not None:
        score = rs["score"]
        color = _score_color(score)
        out = (f"<div class='gauge' data-gauge='{score}' data-color='{color}'>"
               f"<div class='gauge-inner'><div>"
               f"<span class='gauge-num' style='color:{color}' "
               f"data-count='{score}'>0</span>"
               f"<span class='gauge-max'> / 100</span>"
               f"</div></div></div>")
        out += (f"<p><span class='badge b-cyan'>{_e(rs.get('level'))}</span></p>")
        comp = rs.get("components") or {}
        if comp:
            names = {"cpu": "CPU AI 能力", "gpu": "GPU 能力", "npu": "NPU 能力",
                     "memory": "内存", "openvino": "OpenVINO 环境",
                     "benchmark": "实测 Benchmark"}
            out += _grid_table(["评分项", "得分"],
                               [[_e(names.get(k, k)), _e(v)]
                                for k, v in comp.items()])
        out += f"<p class='muted'>{_e(rs.get('disclaimer'))}</p>"
        return out
    # 未评分（降级平台或 quick 模式）：徽章 + 说明，不显示分数
    return (f"<p><span class='px px-amber'></span>"
            f"<span class='badge b-amber'>未评分 NOT SCORED</span></p>"
            f"<p>{_e(rs.get('note', ''))}</p>")


def _openvino(r: dict) -> str:
    ov = r.get("openvino", {})
    if not ov.get("installed"):
        guide = "".join(f"<li><code>{_e(s)}</code></li>"
                        for s in ov.get("install_guide", []))
        return ("<p>状态：<span class='badge b-magenta'>未安装</span></p>"
                f"<p>引导步骤：</p><ul>{guide}</ul>")
    devices = ov.get("devices") or {}
    rows = [[_e(name), _status_px(d.get("status"))] for name, d in devices.items()]
    return (f"<p>版本：{_e(ov.get('version'))} "
            f"<span class='badge b-green'>BENCHMARKED 环境实测</span></p>"
            + _grid_table(["设备", "Runtime 状态"], rows))


def _device_compat(r: dict) -> str:
    tests = r.get("device_tests") or []
    if not tests:
        return "<p class='muted'>未执行（quick 模式不运行冒烟测试）。</p>"
    rows = [[_e(t.get("device")), _status_px(t.get("compile")),
             _status_px(t.get("inference")),
             _e(t.get("error") or t.get("hint") or t.get("note") or "")]
            for t in tests]
    return _grid_table(["设备", "编译", "推理", "说明"], rows)


def _bars(benches: list, key: str, unit: str) -> str:
    """像素风条形图：按数值占比，加载时生长动画。"""
    values = [b.get(key) for b in benches
              if isinstance(b.get(key), (int, float))]
    if not values:
        return ""
    vmax = max(values) or 1
    rows = []
    for b in benches:
        v = b.get(key)
        if not isinstance(v, (int, float)):
            continue
        pct = max(int(v / vmax * 100), 3)
        cls = f"bar-{b['device'].lower()}"
        rows.append(
            f"<div class='bar-row'><span class='name'>{_e(b['device'])}</span>"
            f"<span class='bar-track'><span class='bar-fill {cls}' "
            f"style='--w:{pct}%'></span></span>"
            f"<span class='bar-val'>{_e(v)} {_e(unit)}</span></div>")
    return "".join(rows)


def _benchmark(r: dict) -> str:
    benches = [b for b in (r.get("benchmarks") or []) if b.get("status") == "PASS"]
    if not benches:
        return "<p class='muted'>未执行或无实测数据。</p>"
    runs = benches[0].get("timed_runs", "-")
    warm = benches[0].get("warmup_runs", "-")
    out = ("<p><span class='badge b-green'>BENCHMARKED</span> "
           f"<span class='muted'>模型 mnist-8 · warmup {warm} 次 + "
           f"计时 {runs} 次</span></p>")
    note = benches[0].get("measurement_note")
    if note:
        out += f"<p class='muted'>{_e(note)}</p>"
    out += "<h4>平均延迟对比（越低越好）</h4>" + _bars(benches, "avg_latency_ms", "ms")
    out += "<h4>吞吐对比（越高越好）</h4>" + _bars(benches, "throughput_infer_per_s",
                                                  "infer/s")
    rows = [[_e(b["device"]), _e(b["compile_time_ms"]),
             _e(b.get("median_latency_ms", "-")), _e(b["avg_latency_ms"]),
             _e(f"{b['min_latency_ms']} / {b['max_latency_ms']}"),
             _e(b.get("stddev_ms", "-")),
             _e(b["throughput_infer_per_s"]), _e(b.get("peak_rss_delta_mb", "-")),
             _e(b.get("avg_cpu_percent", "-"))] for b in benches]
    out += _grid_table(["设备", "编译 ms", "中位延迟 ms", "平均延迟 ms",
                        "最小/最大 ms", "标准差 ms",
                        "吞吐 infer/s", "峰值内存增量 MB", "平均 CPU%"], rows)
    return out


def _card(name: str, value, unit: str, decimals: int = 1) -> str:
    if isinstance(value, (int, float)):
        v = (f"<span data-count='{value}' "
             f"data-decimals='{decimals}'>0</span>")
    else:
        v = _e(value)
    return (f"<div class='card'><div class='v'>{v}"
            f"<span class='u'> {_e(unit)}</span></div>"
            f"<div class='k'>{_e(name)}</div></div>")


def _genai(r: dict) -> str:
    g = r.get("genai")
    if not isinstance(g, dict):
        return ("<p class='muted'>未执行（生成式 AI 基准测试仅在 full 模式运行）。"
                "</p>")
    results = g.get("results") or []
    if not results:
        err = (g.get("error") or {}).get("message", "")
        if g.get("status") == "SKIPPED":
            return f"<p class='muted'>未执行（SKIPPED）。{_e(err)}</p>"
        return f"<p class='muted'>未执行或失败。{_e(err)}</p>"
    badge = ("b-green" if g.get("label") == "BENCHMARKED" else "b-grey")
    label = g.get("label") or "NOT_RUN"
    out = (f"<p>模型：{_e(g.get('model'))}（{_e(g.get('model_size_mb'))} MB · "
           f"来源 {_e(g.get('model_source'))}） "
           f"<span class='badge {badge}'>{_e(label)}</span></p>")
    for res in results:
        if res.get("status") != "PASS":
            continue
        out += f"<h4>{_e(res.get('device'))}</h4><div class='cards'>"
        out += _card("模型加载", res.get("model_load_time_s"), "s", 2)
        out += _card("TTFT 首 Token 延迟", res.get("ttft_ms"), "ms")
        out += _card("TPOT 每 Token 耗时", res.get("tpot_ms"), "ms")
        out += _card("生成吞吐", res.get("throughput_tokens_per_s"), "tokens/s")
        out += _card("输入 Tokens", res.get("input_tokens"), "", 0)
        out += _card("输出 Tokens", res.get("output_tokens"), "", 0)
        out += _card("峰值内存增量", res.get("peak_rss_delta_mb"), "MB")
        out += "</div>"
    failed = [x for x in results if x.get("status") != "PASS"]
    if failed:
        rows = [[_e(x.get("device")), _status_px(x.get("status")),
                 _e((x.get("error") or {}).get("message", ""))] for x in failed]
        out += _grid_table(["设备", "状态", "说明"], rows)
    return out


def _demo_chat(r: dict) -> str:
    d = r.get("demo_chat")
    if not d:
        return ("<p class='muted'>本地体验服务仅在 full 模式且 GenAI benchmark 通过时可用。</p>")
    if not d.get("running"):
        reason = d.get("reason", "未知原因")
        return f"<p class='muted'>本地体验未启动：{_e(reason)}</p>"
    return (f"<div class='demo-box'>"
            f"<div class='demo-icon'>🤖</div>"
            f"<div class='demo-info'>"
            f"<h4>本地 AI 对话体验已就绪</h4>"
            f"<p>模型：<b>{_e(d.get('model'))}</b>　·　设备：<b>{_e(d.get('device'))}</b></p>"
            f"<p class='demo-url'><a href='{_e(d.get('url'))}' target='_blank'>"
            f"{_e(d.get('url'))}</a></p>"
            f"<p class='muted'>{_e(d.get('note', ''))}</p>"
            f"</div></div>")


def _capacity(r: dict) -> str:
    cap = r.get("capacity", {})
    models = cap.get("models") or []
    if not models:
        return f"<p class='muted'>{_e(cap.get('note', '未执行。'))}</p>"
    rows = []
    for m in models:
        grade = m["recommendation"]
        cls = _GRADE_CLASS.get(grade, "b-grey")
        rows.append([_e(m["model_size"]), _e(m["quantization"]),
                     _e(m["weights_gb_estimated"]),
                     _e(m["required_ram_gb_estimated"]),
                     f"<span class='badge {cls}'>{_e(grade)}</span>"])
    return ("<p><span class='badge b-amber'>ESTIMATED</span> "
            f"<span class='muted'>{_e(cap.get('note', ''))}</span></p>"
            + _grid_table(["模型规模", "量化", "权重估算 GB",
                           "需求内存估算 GB", "推荐等级"], rows))


def _recommendation(r: dict) -> str:
    recs = r.get("recommendations") or []
    model_recs = r.get("model_recommendations") or []
    out = ""
    if model_recs:
        out += "<h4>模型推荐清单</h4>"
        for m in model_recs:
            grade = m.get("grade", "UNKNOWN")
            cls = _GRADE_CLASS.get(grade, "b-grey")
            label_cls = "b-green" if m.get("label") == "BENCHMARKED" else "b-amber"
            out += (
                f"<div class='rec-card'><div class='rec-head'>"
                f"<span class='rec-name'>{_e(m.get('name'))}</span>"
                f"<span class='stars'>{_e(_STARS.get(grade, grade))}</span>"
                f"<span class='badge {cls}'>{_e(grade)}</span>"
                f"<span class='badge {label_cls}'>{_e(m.get('label'))}</span>"
                f"</div><div class='rec-meta'>推荐设备："
                f"<b style='color:var(--accent)'>{_e(m.get('device'))}</b>"
                f"　·　{_e(m.get('reason'))}</div></div>")
    if recs:
        items = "".join(
            f"<li><b style='color:var(--accent)'>{_e(x['device'])}</b>："
            f"{_e(x['recommendation'])}</li>"
            if x.get("device") else f"<li>{_e(x['recommendation'])}</li>"
            for x in recs)
        out += f"<h4>设备建议</h4><ul>{items}</ul>"
    return out or "<p class='muted'>未执行。</p>"


def _issues(r: dict) -> str:
    errors = r.get("errors") or []
    if not errors:
        return ("<p><span class='px px-green'></span>"
                "<span class='muted'>未发现问题。</span></p>")
    sev_cls = {"error": "magenta", "warning": "amber", "info": "cyan"}
    items = "".join(
        f"<li><span class='badge b-{sev_cls.get(str(e.get('severity')), 'grey')}'>"
        f"{_e(e.get('severity'))}</span> <code>{_e(e.get('code'))}</code>："
        f"{_e(e.get('message'))}</li>" for e in errors)
    return f"<ul>{items}</ul>"


_RENDERERS = [_device_overview, _readiness, _openvino, _device_compat,
              _benchmark, _genai, _demo_chat, _capacity, _recommendation, _issues]


def render(report: dict) -> str:
    meta = report.get("meta", {})
    mode = str(meta.get("mode") or "standard").lower()
    theme = MODE_THEMES.get(mode, _DEFAULT_THEME)
    # 按模式覆盖主题色（只影响界面主题元素，语义色不变）
    mode_style = (f"<style>:root{{--accent:{theme['accent']};"
                  f"--accent-rgb:{theme['rgb']}}}</style>")
    sections = "".join(
        _section(num, title, fn(report))
        for (num, title), fn in zip(_SECTIONS, _RENDERERS))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>AI PC Doctor · 体检报告</title>
<style>{_CSS}{_CSS_REDUCED}</style>
{mode_style}
</head>
<body>
<header>
<h1 id="title" data-text="AI PC DOCTOR · 体检报告"></h1>
<p><span class='badge' style='color:{theme['accent']};box-shadow:0 0 8px rgba({theme['rgb']},.35)'>{_e(theme['label'])}</span></p>
<p>模式：{_e(meta.get('mode'))} · 生成时间：{_e(meta.get('generated_at'))} · v0.3</p>
</header>
<main>{sections}</main>
<script>{_JS}</script>
</body>
</html>
"""


def write(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "AI_PC_Readiness_Report.html"
    path.write_text(render(report), encoding="utf-8")
    return path
