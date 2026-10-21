import json,pathlib,xml.etree.ElementTree as ET,collections
p=pathlib.Path(__file__).resolve().parent/'evidence';r=json.load(open(p/'package-verified.json'));r=r.get('structuredContent',r);n=r['normalized_result'];v=n['manifest']['text'];(p/'AndroidManifest.xml').write_text(v)
root=ET.fromstring(v);a='{http://schemas.android.com/apk/res/android}';app=root.find('application')
comps=[]
for e in app:
 if e.tag not in ['activity','activity-alias','service','receiver','provider']:continue
 comps.append({'attributes':{k.removeprefix(a):v for k,v in e.attrib.items()},'type':e.tag,'name':e.get(a+'name'),'exported':e.get(a+'exported'),'permission':e.get(a+'permission'),'authorities':e.get(a+'authorities'),'intent_filters':[{'actions':[x.get(a+'name') for x in i.findall('action')],'categories':[x.get(a+'name') for x in i.findall('category')],'data':[{k.removeprefix(a):v for k,v in d.attrib.items()} for d in i.findall('data')]} for i in e.findall('intent-filter')]})
(p/'components.json').write_text(json.dumps(comps,indent=2));(p/'application-attributes.json').write_text(json.dumps(app.attrib,indent=2))
print('Components:',collections.Counter(x['type'] for x in comps));print('Explicit exported:',sum(x['exported']=='true' for x in comps));print('Requested permissions:',len(n['permissions']));print('Application:',app.attrib)
