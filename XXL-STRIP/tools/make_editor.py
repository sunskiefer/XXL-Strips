#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Writes the XXL Pro Panel Editor page from the built skin (run ./build.sh first).

    python3 tools/make_editor.py [out.html]

The page is the ALPHA Panel Editor (tools/editor_base.html: its look, tools and layout-file format) fed with XXL Pro's
pages: every knob, name, value, switch, button, tile, readout and drawn text is its own piece to move, resize, retext.
"Export layout" gives the layout file; saved as layout.json next to build.sh, the next build puts every piece there.
"""
import json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
base = open(os.path.join(ROOT, "tools", "editor_base.html")).read().split("\n")
data = json.load(open(os.path.join(ROOT, "build", "editor_data.json")))
lay = os.path.join(ROOT, "layout.json")
data["saved"] = json.load(open(lay)).get("parts", []) if os.path.isfile(lay) else []
NAME = json.load(open(os.path.join(ROOT, "vst.json")))["name"]
SLUG = re.sub(r"[^A-Za-z0-9]", "", NAME)
i_data = next(i for i, l in enumerate(base) if l.startswith("const D="))
head = "\n".join(base[:i_data])
head = head[head.index("<title>"):]
script = "\n".join(base[i_data + 1:])
script = script[:script.rindex("</script>") + len("</script>")]


def sub(text, a, b, count=1):
    assert text.count(a) == count, (a, text.count(a))
    return text.replace(a, b)


head = sub(head, "<title>ALPHA Panel Editor</title>", "<title>%s Panel Editor</title>" % NAME)
head = sub(head, "<h1>ALPHA Panel Editor</h1>", "<h1>%s Panel Editor</h1>" % NAME)
head = re.sub(r"<p>Every part is its own piece:.*?</p>", "<p>Every part is its own piece: each knob, its name and its value, each switch, button, tile, readout and text. "
              "Pick a page, click a piece to select it, drag it, drag the corner to resize it, or type exact numbers. Then press Export layout and send me the layout "
              "(or save it as layout.json next to build.sh). Select a knob and press a KNOB picture to swap its style and colour." + (" Patch bay sockets and cables are fixed for now." if NAME == "XXL Pro" else "") + "</p>", head, flags=re.S)
head = sub(head, "--accent:#d12a8c", "--accent:#d99a1c")
head = sub(head, "rgba(209,42,140,.15)", "rgba(217,154,28,.15)")
head = sub(head, "ALPHA magenta accent", "XXL amber accent")
for b in ('<button data-r="tick">Ticks</button>', '<button data-r="shadow">Shadows</button>'):
    head = sub(head, b, b.replace("<button ", "<button hidden "))
head = sub(head, '<button id="bSw" ', '<button hidden id="bSw" ')
head = sub(head, '<button id="bApply" ', '<button hidden id="bApply" ')
head = sub(head, '<label style="display:flex;gap:8px;align-items:center;font-size:13px;color:var(--dim)">Turn knobs', '<label hidden>Turn knobs')
head = sub(head, '<div class="panel" id="shp">', '<div class="panel" id="shp" hidden>')
head = sub(head, "the magenta corner", "the amber corner") if "the magenta corner" in head else head

# the loader: every part of every control is one piece (no ALPHA knob art)
a, b = script.index("D.views.forEach((v,p)=>v.forEach(c=>{"), script.index("try{")
script = script[:a] + """D.views.forEach((v,p)=>v.forEach(c=>{
 const pg=pageList[p];
 c.parts.forEach(q=>{const key=c.id+':'+q.id,base={ctl:c.id,cname:c.name,kind:c.kind};
  if(q.k==='img')add(key,{...base,role:q.role,x:c.x+q.x,y:c.y+q.y,w:q.w,h:q.h,parts:[{...q,x:0,y:0}],ow:q.w,oh:q.h},pg);
  else add(key,{...base,role:q.role,x:c.x+q.x,y:c.y+q.y,w:q.w,h:q.h,part:q},pg)});
}));
(D.saved||[]).forEach(o=>{const l=L[o.id];if(!l)return;if(o.knob)l.col=o.knob;l.x=o.x;l.y=o.y;l.w=o.w;l.h=o.h;if(o.text!==undefined){l.t=o.text;l.size=o.size*0.75;l.wt=o.weight;l.c=o.colour}});
""" + script[b:]
script = sub(script, "alphaLayoutV5", SLUG + "LayoutV1", 2)
a, b = script.index("  if(it.role==='tick')"), script.index("  else if(TXT.includes(it.role)){const q=it.part;const f=el(")
script = script[:a] + "  if(false){}\n" + script[b:]
script = sub(script, "plugin:'ALPHA'", "plugin:'%s'" % NAME)
script = sub(script, "const TXT=['name','value','text'];", "const TXT=['name','value','text'];const ART={};")
# ---- XXL additions to the base editor: swap a knob's colour, add a text, insert a picture, delete what was added
head = sub(head, '<div id="wrap">', """<div class="bar"><strong style="font-size:13px;color:var(--dim)">KNOB</strong><span class="styles" id="kcol"></span>
 <span class="sp"></span><button id="bAddText">+ Add text</button><button id="bAddImg">+ Insert image</button><button id="bDel">Delete added</button>
 <input id="fImg" type="file" accept="image/*" hidden></div>
<div id="wrap">""")
head = sub(head, "</style>", ".styles{display:inline-flex;gap:6px;align-items:center}.styles{flex-wrap:wrap}.styles button{padding:2px;width:52px;height:52px;display:grid;place-items:center;background:#24221e}.styles button img{width:44px;height:44px}\n</style>")
script = sub(script, "const o={id:k,control:it.cname,part:RN[it.role]||'control',x:l.x,y:l.y,w:l.w,h:l.h};",
             "const o={id:k,control:it.cname,part:RN[it.role]||'control',x:l.x,y:l.y,w:l.w,h:l.h};if(l.col)o.knob=l.col;if(it.added){o.added=it.added;o.page=D.names[it.page];if(it.added==='image')o.data=D.imgs[k]}")
script = sub(script, "j.parts.forEach(o=>{const l=L[o.id];if(l){", "j.parts.forEach(o=>{if(o.added&&!L[o.id])mkAdded(o);const l=L[o.id];if(l){if(o.knob)setCol(o.id,o.knob);")
script = sub(script, "$('snap').value='8';snap=8;\ndraw();", r"""$('snap').value='8';snap=8;
/* knob colours */
function setCol(key,col){const it=items[key];if(!it||it.role!=='body')return;const alts=it.parts[0].alts;if(alts){const c=col.replace('WHITE ','').replace('FLAT ','');if(!alts[c])return;it.parts[0].src=alts[c];L[key].col=c;return}if(it.kind!=='knob'||!D.knobs[col])return;D.imgs['knob:'+col]=D.knobs[col];it.parts[0].src='knob:'+col;L[key].col=col}
Object.keys(D.knobs).forEach(col=>{const b=document.createElement('button');b.title=col;const i=document.createElement('img');i.src=D.knobs[col];i.alt=col;b.appendChild(i);
 b.onclick=()=>{let n=0;sel.forEach(k=>{if(items[k].role==='body'){setCol(k,col);n++}});$('msg').textContent=n?n+' control'+(n>1?'s':'')+' set to '+col:'Select one or more knobs or faders first (the picture, not the name).';draw()};$('kcol').appendChild(b)});
for(const k in L)if(L[k].col)setCol(k,L[k].col);
/* added texts and pictures */
let ADDED=[];
function mkAdded(o){const pg=Math.max(0,D.names.indexOf(o.page)),base={ctl:o.id.split(':')[0],cname:'added',kind:'art',added:o.added,page:pg};
 if(o.added==='text')add(o.id,{...base,role:'text',x:o.x,y:o.y,w:o.w,h:o.h,part:{t:o.text||'TEXT',size:(o.size||30)*0.75,wt:o.weight||700,c:o.colour||'#ffffff'}},pageList[pg]);
 else{D.imgs[o.id]=o.data;add(o.id,{...base,role:'bg',x:o.x,y:o.y,w:o.w,h:o.h,parts:[{src:o.id,x:0,y:0,w:o.w,h:o.h}],ow:o.w,oh:o.h},pageList[pg])}
 ADDED.push(o.id);keepAdded()}
function keepAdded(){try{localStorage.setItem('__SLUG__AddedV1',JSON.stringify(ADDED.filter(k=>items[k]).map(k=>{const it=items[k],l=L[k],o={id:k,added:it.added,page:D.names[it.page],x:l.x,y:l.y,w:l.w,h:l.h};if(it.added==='text'){o.text=l.t;o.size=bs(k);o.weight=l.wt;o.colour=l.c}else o.data=D.imgs[k];return o})))}catch(e){}}
function newId(){let n=1;while(items['add'+n+':t']||items['add'+n+':bg'])n++;return 'add'+n}
(D.saved||[]).filter(o=>o.added).forEach(o=>{if(!items[o.id])mkAdded(o)});
try{(JSON.parse(localStorage.getItem('__SLUG__AddedV1')||'[]')).forEach(o=>{if(!items[o.id])mkAdded(o)})}catch(e){}
$('bAddText').onclick=()=>{const id=newId()+':t';mkAdded({id,added:'text',page:D.names[page],x:480,y:300,w:320,h:44,text:'TEXT',size:30,weight:700,colour:'#ffffff'});sel=new Set([id]);draw()};
$('bAddImg').onclick=()=>$('fImg').click();
$('fImg').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{const im=new Image();im.onload=()=>{const k=Math.min(1,600/im.width,400/im.height),id=newId()+':bg';
  mkAdded({id,added:'image',page:D.names[page],x:340,y:120,w:Math.round(im.width*k),h:Math.round(im.height*k),data:r.result});sel=new Set([id]);draw()};im.src=r.result};r.readAsDataURL(f);e.target.value=''};
$('bDel').onclick=()=>{let n=0;[...sel].forEach(k=>{if(items[k]&&items[k].added){pageList[items[k].page]=pageList[items[k].page].filter(x=>x!==k);delete items[k];delete L[k];delete DEF[k];sel.delete(k);n++}});$('msg').textContent=n?'Deleted '+n+' added piece'+(n>1?'s':''):'Only texts and images you added can be deleted.';keepAdded();draw()};
const _draw=draw;draw=function(){_draw();keepAdded();const f=D.faces&&D.faces[String(page)];
 if(f){stage.style.backgroundImage='url('+f+'),url('+D.bg+')';stage.style.backgroundSize='1280px '+(D.face_y[1]-D.face_y[0])+'px,100% 100%';stage.style.backgroundPosition='0 '+D.face_y[0]+'px,0 0';stage.style.backgroundRepeat='no-repeat'}
 else{stage.style.backgroundImage='url('+D.bg+')';stage.style.backgroundSize='100% 100%';stage.style.backgroundPosition='0 0'}};
draw();""")
script = sub(script, "function draw(){", "var draw=function(){")
script = script.replace("__SLUG__", SLUG)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "%s-Panel-Editor.html" % NAME.replace(" ", "-"))
open(out, "w").write(head + "\nconst D=" + json.dumps(data, separators=(",", ":")) + ";\n" + script + "\n")
print("make_editor: %s (%d KB)" % (out, os.path.getsize(out) // 1024))
