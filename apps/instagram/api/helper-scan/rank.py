import json,collections,pathlib,gzip
P=pathlib.Path(__file__).resolve().parent
raw=P/'route-method-calls.json';compressed=raw.with_suffix('.json.gz')
if not raw.exists() and not compressed.exists():raise SystemExit('Run scan.py with your APK first; neither raw nor compressed helper evidence is available.')
x=json.loads(raw.read_text() if raw.exists() else gzip.open(compressed,'rt').read());routeby=collections.defaultdict(list);calls=collections.defaultdict(list)
for h in x['hits']:routeby[(h['dex'],h['method'])].append(h)
for c in x['calls']:
 if any(t in c['callee'] for t in ['LX/04x5;','LX/04x6;','LX/02sB;','LX/02sG;','LX/02sF;']):calls[c['callee']].append(c)
ranked=[]
for sig,cc in calls.items():
 methods={(c['dex'],c['caller']) for c in cc};routes={h['value'] for key in methods for h in routeby[key]}
 ranked.append({'callee':sig,'distinct_route_bearing_methods':len(methods),'distinct_cooccurring_routes':len(routes),'call_count':len(cc),'example_calls':[dict(c,cooccurring_routes=routeby[(c['dex'],c['caller'])]) for c in cc[:5]]})
ranked.sort(key=lambda r:-r['distinct_route_bearing_methods'])
chosen=['LX/0225;->A0L(','LX/021X;->A0T(','LX/021R;->A0T(','LX/0221;->A0I(','LX/020p;->A0K(','LX/0221;->A0V(','LX/020p;->A1U(','LX/0064;->A0Q(','LX/0465;->A1O(','LX/0465;->A0N(']
top=[r for prefix in chosen for r in ranked if r['callee'].startswith(prefix)]
(P/'ranked-helpers.json').write_text(json.dumps({'scope':'Static direct route-string and invoke co-occurrence within whole methods, not control/dataflow association. All instruction boundaries decoded.','stats':x['stats'],'priority_for_verification':top,'all_builder_signature_candidates':ranked,'limitations':['A helper may occur in a different branch than a route string, particularly synthetic listeners.','Routes loaded through obfuscated string lookup helpers or assembled dynamically are excluded.','No HTTP verb assigned from helper name/signature/co-occurrence alone.','Priority list omits already known helpers 0221.A0J, 0221.A0K, 0224.A0P and generic low-level parameter methods.']},indent=2)+'\n')
lines=['Ten candidate helper methods for independent REA verification','', 'Numbers count distinct methods containing a route candidate literal and invoking this helper. This is co-occurrence, not proof of route/verb association.','']
for r in top:lines.append(str(r['distinct_route_bearing_methods'])+' '+r['callee'])
lines+=['','Raw decoded callsites: route-method-calls.json. Ranked callsites with route provenance: ranked-helpers.json.','Scan coverage: 23 DEX files, 807462 decoded methods, zero instruction errors, 2039 direct const-string route references. Only existing lexical route catalog candidates are considered.','No HTTP methods inferred; parent must verify helper implementations before use.']
(P/'NOTES.txt').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
