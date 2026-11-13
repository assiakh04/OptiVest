"""Identité visuelle : marine profond · turquoise · orange. Palette catégorielle et CSS."""

INK = '#0A2540'        # marine profond (sidebar, titres)
INK_SOFT = '#12385F'
TEAL = '#0A8F8B'       # primaire
TEAL_BRIGHT = '#2FD3C9'
ORANGE = '#FF7A3D'     # accent
AMBER = '#FFB703'
BLUE = '#2F6BFF'
RED = '#E5484D'
GREEN = '#2DBE6C'
SKY = '#38BDF8'
SLATE = '#64748B'
BG = '#F3F6FA'
CARD = '#FFFFFF'
LINE = '#D9E2EC'
MUTED = '#5B6F86'
TEXT = '#0E2238'

# catégorielle : l'ordre alterne chaud / froid pour que deux séries voisines restent distinctes
CAT = [TEAL, ORANGE, BLUE, AMBER, RED, GREEN, SKY, SLATE]
SEQ = [[0, '#EAF7F6'], [.5, '#5FC9C3'], [1, '#0A6F6C']]
DIV = [[0, '#E5484D'], [.5, '#FFFFFF'], [1, '#0A8F8B']]

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important; color: {INK}; letter-spacing: -.01em; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1280px; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* ---------- hero ---------- */
.hero {{ position: relative; overflow: hidden; border-radius: 20px; padding: 28px 34px 26px;
  background: linear-gradient(120deg, {INK} 0%, #0E3A5E 55%, #0B6E71 100%); color: #fff; margin-bottom: 22px;
  box-shadow: 0 14px 34px -18px rgba(10,37,64,.55); }}
.hero::after {{ content: ''; position: absolute; right: -60px; top: -70px; width: 250px; height: 250px; border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, {ORANGE} 0%, rgba(255,122,61,0) 68%); opacity: .55; }}
.hero::before {{ content: ''; position: absolute; right: 120px; bottom: -90px; width: 220px; height: 220px; border-radius: 50%;
  background: radial-gradient(circle, {TEAL_BRIGHT} 0%, rgba(47,211,201,0) 70%); opacity: .35; }}
.hero .kicker {{ font: 700 11.5px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; letter-spacing: .16em; text-transform: uppercase; color: {TEAL_BRIGHT}; margin-bottom: 8px; position: relative; z-index: 1; }}
.hero h1 {{ color: #fff !important; font-size: 30px; line-height: 1.15; margin: 0 0 8px; font-weight: 800; position: relative; z-index: 1; }}
.hero p {{ color: #C6D6E8; font-size: 15px; margin: 0; max-width: 760px; position: relative; z-index: 1; }}
.hero .chips {{ margin-top: 15px; display: flex; flex-wrap: wrap; gap: 8px; position: relative; z-index: 1; }}
.chip {{ display: inline-block; font: 600 11.5px 'Inter', system-ui, sans-serif; padding: 5px 11px; border-radius: 999px;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22); color: #fff; }}
.chip.dark {{ background: {INK}0D; border-color: {LINE}; color: {INK}; }}
.chip.teal {{ background: #DDF5F3; border-color: #B7E9E5; color: #07625F; }}
.chip.orange {{ background: #FFE9DE; border-color: #FFD0B8; color: #B4430F; }}

/* ---------- cartes & KPI ---------- */
.kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin: 4px 0 20px; }}
.kpi {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 16px; padding: 15px 18px 14px; position: relative; overflow: hidden; }}
.kpi::before {{ content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--acc, {TEAL}); }}
.kpi .lab {{ font: 600 11px 'Inter', system-ui, sans-serif; letter-spacing: .08em; text-transform: uppercase; color: {MUTED}; }}
.kpi .val {{ font: 800 26px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; color: {INK}; margin-top: 4px; line-height: 1.15; word-break: break-word; }}
.kpi .sub {{ font: 500 12px 'Inter', system-ui, sans-serif; color: {MUTED}; margin-top: 3px; }}
.card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 16px; padding: 18px 20px; margin-bottom: 14px; }}
.card h4 {{ margin: 0 0 6px; font-size: 15.5px; }}
.card p {{ margin: 0; color: {MUTED}; font-size: 13.5px; line-height: 1.55; }}
.card .tag {{ font: 700 10.5px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; letter-spacing: .12em; text-transform: uppercase; color: {TEAL}; margin-bottom: 6px; }}
.card.accent {{ border-top: 4px solid {ORANGE}; }}
.card.teal {{ border-top: 4px solid {TEAL}; }}
.card.blue {{ border-top: 4px solid {BLUE}; }}
.card.amber {{ border-top: 4px solid {AMBER}; }}

.callout {{ border-radius: 12px; padding: 12px 16px; font-size: 13.8px; line-height: 1.55; margin: 8px 0 14px; border: 1px solid; }}
.callout b {{ font-weight: 700; }}
.callout.info {{ background: #E9F1FF; border-color: #C8DAFF; color: #12336B; }}
.callout.tip {{ background: #E3F7F5; border-color: #B7E9E5; color: #07514F; }}
.callout.warn {{ background: #FFF3DA; border-color: #FFE0A3; color: #7A4B00; }}
.callout.ok {{ background: #E2F7EA; border-color: #B8EBCB; color: #0F5B2D; }}
.callout.bad {{ background: #FDE8E9; border-color: #F8C5C8; color: #8A1F24; }}

.sec {{ display: flex; align-items: center; gap: 10px; margin: 26px 0 8px; }}
.sec .bar {{ width: 5px; height: 22px; border-radius: 3px; background: linear-gradient({TEAL}, {ORANGE}); }}
.sec h3 {{ margin: 0; font-size: 18px; }}
.sec-sub {{ color: {MUTED}; font-size: 13.5px; margin: -2px 0 12px 15px; }}

.formula-box {{ background: #F7FAFD; border: 1px dashed #B9C9DB; border-radius: 12px; padding: 4px 12px; margin: 6px 0 12px; }}
.rankpill {{ display: inline-block; min-width: 26px; text-align: center; font: 800 12px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; border-radius: 8px; padding: 3px 8px; color: #fff; background: {SLATE}; }}
.rankpill.r1 {{ background: {ORANGE}; }} .rankpill.r2 {{ background: {TEAL}; }} .rankpill.r3 {{ background: {BLUE}; }}

.stepper {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin: 6px 0 18px; }}
.stepper .s {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 14px; padding: 12px 12px 12px; position: relative; }}
.stepper .s .n {{ font: 800 18px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; color: {ORANGE}; }}
.stepper .s .t {{ font: 700 12.5px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; color: {INK}; margin-top: 2px; }}
.stepper .s .d {{ font: 400 11.5px 'Inter', system-ui, sans-serif; color: {MUTED}; margin-top: 3px; line-height: 1.4; }}
@media (max-width: 900px) {{ .stepper {{ grid-template-columns: repeat(2, 1fr); }} }}

/* ---------- widgets Streamlit ---------- */
div[data-testid="stTabs"] [role="tablist"] {{ gap: 4px; border-bottom: 2px solid {LINE}; }}
div[data-testid="stTabs"] button[role="tab"] {{ font: 600 13.5px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; padding: 9px 18px; border-radius: 10px 10px 0 0; color: {MUTED}; }}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{ color: {TEAL}; }}
div[data-testid="stMetric"] {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 14px; padding: 12px 16px; }}
div[data-testid="stMetricValue"] {{ font-family: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; font-weight: 800; color: {INK}; }}
div[data-testid="stExpander"] {{ border: 1px solid {LINE}; border-radius: 14px; background: {CARD}; }}
div[data-testid="stExpander"] summary {{ font-weight: 600; }}
.stButton > button, .stDownloadButton > button {{ border-radius: 11px; font-weight: 600; border: 1px solid {LINE}; transition: all .15s ease; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: {TEAL}; color: {TEAL}; transform: translateY(-1px); }}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{ background: linear-gradient(135deg, {TEAL}, #0B6E71); border: 0; color: #fff; box-shadow: 0 8px 18px -10px {TEAL}; }}
.stButton > button[kind="primary"]:hover {{ color: #fff; filter: brightness(1.08); }}
div[data-testid="stDataFrame"] {{ border: 1px solid {LINE}; border-radius: 12px; overflow: hidden; }}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] > div {{ background: linear-gradient(180deg, {INK} 0%, #0B2E50 100%); }}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {{ border-radius: 10px; margin: 1px 6px; font-weight: 500; }}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: linear-gradient(90deg, rgba(47,211,201,.22), rgba(47,211,201,.05)); box-shadow: inset 3px 0 0 {TEAL_BRIGHT}; font-weight: 700; color: #fff; }}
.side-card {{ background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.12); border-radius: 14px; padding: 12px 14px; margin: 6px 4px 10px; color: #E8F0FA; }}
.side-card .t {{ font: 700 10.5px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; letter-spacing: .14em; color: {TEAL_BRIGHT}; text-transform: uppercase; }}
.side-card .v {{ font: 700 14px 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif; margin: 3px 0 2px; color: #fff; }}
.side-card .s {{ font-size: 12px; color: #A9BDD3; }}
.footer {{ margin-top: 40px; padding-top: 14px; border-top: 1px solid {LINE}; color: {MUTED}; font-size: 12px; text-align: center; }}
"""

# OptiVest visual layer: accessible animated hero, pastel finance UI, retained plot components.
TEAL='#2DACA6'
TEAL_BRIGHT='#8EE1CF'
ORANGE='#F6A285'
AMBER='#E6BD66'
BLUE='#8D9DED'
GREEN='#57BDA0'
BG='#F8F9FD'
CAT=['#2DACA6','#8C94E4','#F1AA8C','#E9C46C','#9AC5EC','#A7B79C','#DDA7C5','#AEC8D8']
CSS += r'''
/* OptiVest: refined spacing, pastel cards and ambient motion */
html,body,[class*="css"] {font-family: 'Inter', system-ui, sans-serif !important;}
.stApp {background:radial-gradient(ellipse at 94% 1%, rgba(229,231,253,.8),transparent 28%),radial-gradient(ellipse at 8% 12%,rgba(255,234,224,.55),transparent 28%),#F9FAFC;}
.block-container{max-width:1420px;padding-top:1.35rem;padding-bottom:3rem}
.hero{padding:40px 46px;border-radius:27px;background:linear-gradient(125deg,#132F50 1%,#1A5169 64%,#2C8785 100%);min-height:190px}
.hero h1{font-size:clamp(28px,3vw,43px)}
.hero p{max-width:850px}
.hero::before{animation:ovBreathe 9s ease-in-out infinite alternate}
.hero::after{animation:ovDrift 13s ease-in-out infinite alternate}
@keyframes ovBreathe{from{transform:scale(.88) translateY(3px)}to{transform:scale(1.2) translateY(-18px)}}
@keyframes ovDrift{from{transform:translate(0,0) rotate(0deg)}to{transform:translate(-35px,12px) rotate(35deg)}}
.ov-hero{overflow:hidden;isolation:isolate;position:relative;min-height:335px;padding:52px 5.5%;border-radius:29px;margin:3px 0 25px;
 background:linear-gradient(120deg,#122D4B 0%,#164763 54%,#2D8D88 100%);box-shadow:0 19px 50px -29px rgba(27,64,83,.6);color:white;display:flex;align-items:center;}
.ov-hero-copy{position:relative;z-index:2;max-width:65%;}
.ov-kicker{display:flex;align-items:center;gap:9px;letter-spacing:.16em;color:#99E5D6;font-size:11px;font-weight:800;margin-bottom:17px;}
.ov-live{width:8px;height:8px;border-radius:50%;background:#9CEBD6;box-shadow:0 0 0 0 rgba(156,235,214,.45);animation:ovPulse 2.4s ease-out infinite}
@keyframes ovPulse{0%{box-shadow:0 0 0 0 rgba(156,235,214,.6)}65%{box-shadow:0 0 0 11px rgba(156,235,214,0)}100%{box-shadow:0 0 0 0 rgba(156,235,214,0)}}
.ov-hero h1{font-size:clamp(34px,4vw,53px);letter-spacing:-.055em;line-height:1.12;margin:0 0 18px;font-weight:800;color:#fff !important;max-width:720px;}
.ov-hero p{color:#CCE0E9;font-size:15px;line-height:1.75;margin:0;max-width:660px;}
.ov-pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:24px;}
.ov-pills span{border:1px solid rgba(224,255,250,.24);background:rgba(255,255,255,.11);color:#E5F7F4;border-radius:40px;padding:8px 12px;font-size:11px;font-weight:700;}
.ov-art{position:absolute;z-index:1;right:3.2%;top:8%;width:30%;height:86%;}
.ov-sphere{width:180px;height:180px;border-radius:50%;position:absolute;top:16%;right:14%;background:radial-gradient(circle at 30% 25%,#C9EFE4 0%,#88CED2 25%,#8E9CD5 61%,#2E7288 100%);box-shadow:inset -15px -24px 45px #1B49698A,0 25px 60px #08283A45;animation:ovFloat 6s ease-in-out infinite;}
.ov-orbit{position:absolute;border:1px solid rgba(214,244,246,.33);border-radius:50%;transform:rotate(-26deg);}
.ov-orbit-one{height:270px;width:270px;right:1%;top:0;animation:ovRotate 23s linear infinite;}
.ov-orbit-two{height:210px;width:325px;right:-7%;top:12%;animation:ovRotate 29s linear infinite reverse;}
.ov-particle{position:absolute;border-radius:50%;background:#FFD6B6;box-shadow:0 0 20px #FFD6B690;animation:ovFloat 5.2s ease-in-out infinite;}
.ov-p1{width:13px;height:13px;right:10%;top:16%}.ov-p2{width:8px;height:8px;right:83%;top:70%;animation-delay:-2s}.ov-p3{width:9px;height:9px;right:6%;bottom:14%;animation-delay:-3s}
.ov-float{position:absolute;padding:11px 15px;border:1px solid rgba(255,255,255,.35);border-radius:16px;background:rgba(242,255,255,.12);backdrop-filter:blur(10px);box-shadow:0 12px 35px #09243C38;animation:ovFloat 5s ease-in-out infinite;}
.ov-float small{display:block;color:#D1E9EB;margin-top:3px;font-size:10px}.ov-float strong{font-size:22px;color:#DDF9EB;font-weight:800}.ov-float-one{top:5%;left:-4%;animation-delay:-1s}.ov-float-two{bottom:4%;right:0;animation-delay:-3s}
.ov-bars{display:flex;align-items:end;gap:5px;height:42px}.ov-bars i{width:11px;border-radius:5px 5px 0 0;background:#A5DFD3;animation:ovBars 2s ease-in-out infinite alternate}.ov-bars i:nth-child(1){height:40%}.ov-bars i:nth-child(2){height:75%;animation-delay:.3s}.ov-bars i:nth-child(3){height:56%;animation-delay:.5s}.ov-bars i:nth-child(4){height:100%;animation-delay:.6s}.ov-bars i:nth-child(5){height:68%;animation-delay:.8s}
@keyframes ovBars{from{transform:scaleY(.72);transform-origin:bottom}to{transform:scaleY(1);transform-origin:bottom}}
@keyframes ovRotate{from{transform:rotate(-26deg)}to{transform:rotate(334deg)}}
@keyframes ovFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-13px)}}
.kpi-row{gap:13px;margin-bottom:22px}.kpi{border:1px solid #E7EBF4;border-radius:19px;padding:20px 21px;box-shadow:0 8px 24px rgba(40,62,87,.045);transition:transform .25s ease,box-shadow .25s ease;background:#fff;}
.kpi:hover{transform:translateY(-3px);box-shadow:0 15px 30px rgba(40,62,87,.1)}.kpi::before{border-radius:4px;top:16px;bottom:16px;width:4px}
.kpi .val{font-size:clamp(19px,1.7vw,25px);overflow-wrap:anywhere}
.card{background:white;border-color:#E7EBF3;border-radius:18px;box-shadow:0 6px 23px rgba(48,64,94,.035);transition:transform .23s ease,box-shadow .23s ease}.card:hover{transform:translateY(-3px);box-shadow:0 10px 25px rgba(48,64,94,.09)}
.sec .bar{background:linear-gradient(180deg,#48B8AA,#B4A5F5)}
section[data-testid="stSidebar"]>div{background:linear-gradient(170deg,#102C46 0%,#122F4B 68%,#1C4D60 100%)}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"]{padding-top:.1rem}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]{padding-top:8px;padding-bottom:8px;transition:background .2s ease,transform .2s ease;}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover{transform:translateX(3px);background:rgba(126,212,197,.12)}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"]{background:linear-gradient(90deg,rgba(107,215,201,.25),rgba(107,215,201,.06));box-shadow:inset 3px 0 0 #78E1CC}
.ov-brand{display:flex;align-items:center;gap:11px;color:#fff;margin:10px 2px 15px}.ov-brand-symbol{display:flex;justify-content:center;align-items:center;width:40px;height:40px;border-radius:13px;font-size:26px;color:#143F4D;background:linear-gradient(140deg,#A8E9D9,#C6C5FF);box-shadow:0 5px 21px rgba(128,220,207,.2)}.ov-brand b{display:block;font:800 23px 'Plus Jakarta Sans',system-ui}.ov-brand small{display:block;color:#A1E3D8;letter-spacing:.17em;font-size:8px;font-weight:800}
.side-card{border-color:rgba(213,245,237,.14);background:rgba(230,248,242,.065)}.side-card .t{color:#92E5D6}.side-card .v{font-size:13px}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:linear-gradient(110deg,#268F8D,#4CB5A4);border-radius:13px;box-shadow:0 10px 24px -13px #0A8F8B}.stButton>button,.stDownloadButton>button{border-radius:12px}
.stTabs [role="tab"]{font-weight:700!important}
@media(max-width:950px){.ov-art{opacity:.5;right:-8%;}.ov-hero-copy{max-width:85%}.ov-hero{padding:35px 6%;min-height:275px}}
@media(max-width:650px){.ov-art{display:none}.ov-hero-copy{max-width:100%}.ov-hero h1{font-size:32px}.ov-hero{min-height:0;padding:33px 24px}.ov-pills span{font-size:10px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
.ov-prog{height:6px;border-radius:6px;background:rgba(255,255,255,.14);overflow:hidden;margin:7px 0 3px}.ov-prog i{display:block;height:100%;border-radius:6px;background:linear-gradient(90deg,#78E1CC,#B4A5F5);transition:width .5s ease}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]{color:#E8F0FA!important;font-size:14.5px}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"]{background:linear-gradient(90deg,rgba(120,225,204,.38),rgba(120,225,204,.1));box-shadow:inset 4px 0 0 #78E1CC;font-weight:800;color:#fff!important}
section[data-testid="stSidebar"] [data-testid="stNavSectionHeader"],section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span[data-testid="stHeader"]{color:#9BE5D6!important;letter-spacing:.1em;font-weight:800}
.kpi-row .kpi{animation:ovRise .5s ease both}@keyframes ovRise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

'''
CSS += r'''
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] *{color:#DCE9F5!important;opacity:1!important}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] *{color:#fff!important;font-weight:800!important}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover *{color:#fff!important}
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] header,section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] header *{color:#8FE3D2!important;font-size:11px!important;letter-spacing:.07em!important;white-space:normal!important;opacity:1!important}
.ov-hero h1{letter-spacing:-.03em}
'''
