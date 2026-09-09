import re,json
s=open('js/_0nqzy4_._.js',encoding='utf-8',errors='ignore').read()
slugs=['complete-home-softener-filtration-system','dual-tank-system-for-well-water','reverse-osmosis-system']
def block(slug):
    m=re.search(r"'"+re.escape(slug)+r"':\s*\{",s)
    if not m: return None
    st=m.end()-1; depth=0
    for i in range(st,len(s)):
        if s[i]=='{':depth+=1
        elif s[i]=='}':
            depth-=1
            if depth==0: return s[st:i+1]
    return None
def unq(x):
    x=x.strip()
    if x[:1] in "'\"`" : x=x[1:-1]
    return x.replace("\\'","'").replace('\\"','"').replace("\\n"," ").strip()
out={}
for sl in slugs:
    b=block(sl)
    if not b: print("MISS",sl); continue
    img=re.search(r'image:\s*`\$\{IMG\}([^`]+)`',b)
    alt=re.search(r"alt:\s*'((?:[^'\\]|\\.)*)'",b)
    aspects=[]
    for am in re.finditer(r"kicker:\s*'((?:[^'\\]|\\.)*)'\s*,\s*crossed:\s*'((?:[^'\\]|\\.)*)'\s*,\s*headline:\s*'((?:[^'\\]|\\.)*)'\s*,\s*body:\s*'((?:[^'\\]|\\.)*)'\s*,\s*stats:\s*\[(.*?)\]\s*\}",b,re.S):
        stats=[(unq(a),unq(v)) for a,v in re.findall(r"\[\s*('(?:[^'\\]|\\.)*')\s*,\s*('(?:[^'\\]|\\.)*')\s*\]",am.group(5))]
        aspects.append({'kicker':unq("'"+am.group(1)+"'"),'crossed':unq("'"+am.group(2)+"'"),
                        'headline':unq("'"+am.group(3)+"'"),'body':unq("'"+am.group(4)+"'"),'stats':stats})
    out[sl]={'image':img.group(1) if img else None,'alt':unq("'"+alt.group(1)+"'") if alt else '','aspects':aspects}
json.dump(out,open('aspects.json','w'),indent=1)
for k,v in out.items():
    print(f"\n{k}\n  image: {v['image']}\n  aspects: {len(v['aspects'])}")
    for a in v['aspects']:
        print(f"    · {a['kicker']:18} | {a['headline'][:42]:44} stats={len(a['stats'])}")
