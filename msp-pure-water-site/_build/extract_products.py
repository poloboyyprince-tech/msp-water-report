import re,json,codecs,glob,os

def payload(f):
    s=open(f,encoding='utf-8').read()
    parts=re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)</script>',s,re.S)
    o=[]
    for p in parts:
        try:o.append(json.loads('"'+p+'"'))
        except Exception:o.append(codecs.decode(p,'unicode_escape'))
    return "".join(o)

def objs_at(d, key):
    """yield JSON objects that follow  "<key>":{  via brace matching"""
    for m in re.finditer(r'"%s":\{' % re.escape(key), d):
        st=m.end()-1; depth=0; instr=False; esc=False
        for i in range(st,len(d)):
            c=d[i]
            if esc: esc=False; continue
            if c=='\\': esc=True; continue
            if c=='"': instr=not instr; continue
            if instr: continue
            if c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0:
                    try: yield json.loads(d[st:i+1])
                    except Exception: pass
                    break

def money(v):
    if v is None: return None
    return f"${v/100:,.0f}" if float(v).is_integer() and v%100==0 else f"${v/100:,.2f}"

cat={}
for f in glob.glob('pages/products_*.html'):
    d=payload(f)
    for p in objs_at(d,'product'):
        if not p.get('handle') or 'variants' not in p: continue
        vs=[]
        for v in p.get('variants') or []:
            cp=(v.get('calculated_price') or {})
            vs.append({'title':v.get('title'),'amount':cp.get('calculated_amount'),
                       'price':money(cp.get('calculated_amount'))})
        opts=[{'title':o.get('title'),
               'values':[x.get('value') for x in (o.get('values') or [])]}
              for o in (p.get('options') or [])]
        cat[p['handle']]={'title':p.get('title'),'subtitle':p.get('subtitle'),
                          'description':p.get('description') or '',
                          'variants':vs,'options':opts,
                          'price':vs[0]['price'] if vs else None}
json.dump(cat,open('catalog.json','w'),indent=1)
print(f"{len(cat)} products extracted\n")
for h,p in cat.items():
    print(f"  {h}")
    print(f"     title  : {p['title']}")
    print(f"     price  : {p['price']}")
    print(f"     options: {p['options']}")
    print(f"     variants: {[(v['title'],v['price']) for v in p['variants']]}")
    print(f"     desc   : {len(p['description'])} chars html\n")
