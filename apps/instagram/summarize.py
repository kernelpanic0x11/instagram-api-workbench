import json,re,pathlib,collections,urllib.parse
p=pathlib.Path(__file__).resolve().parent/'evidence'
rows=[json.loads(x) for x in (p/'classes.jsonl').read_text().splitlines()]
areas={'Feed and caching':r'/mainfeed/|/feed/','Reels and drafts':r'/clips/|/creation/','Stories':r'/reels/|/stories/','Messaging and calls':r'/direct/|/realtimeclient/|/mqtt/|/rsys/|/msys/|/fbwebrtc/','Networking and GraphQL':r'/graphql/|/pando/|/tigon/|/proxygen/','Ads and analytics':r'/analytics/|/ads/|/xanalytics/','Session-name candidates, including login':r'/login/|/session/|/oauth/','Browser and Bloks':r'/browser/|/inappbrowser/|/bloks/','AI and wearables':r'/wearable/|/metaai/|/assistant/|/hatch/','Storage and upload':r'/pendingmedia/|/room/|/sqlite/|/upload/'}
features={k:[x for x in rows if re.search(v,x['class'],re.I)] for k,v in areas.items()}
(p/'feature-map.json').write_text(json.dumps(features,indent=2))
dump=(p/'package-dump.txt').read_text() if (p/'package-dump.txt').exists() else ''; perms=[]
# Only the primary user's runtime-permission block; do not mix other users or install-time grants.
m=re.search(r'    User 0:.*?runtime permissions:\n(.*?)(?=\n    \S|\n\S|\Z)',dump,re.S)
if m:
 for permission,grant in re.findall(r'(android\.permission\.\w+): granted=(true|false)',m[1]):perms.append({'permission':permission,'granted':grant=='true'})
if dump:(p/'primary-user-permissions.json').write_text(json.dumps(perms,indent=2))
domains=collections.defaultdict(list)
for line in (p/'url-strings.jsonl').read_text().splitlines():
 r=json.loads(line)
 for s in re.findall(r'https?://[^\s"<>]+',r['value']):
  try: host=urllib.parse.urlsplit(s).hostname
  except ValueError:continue
  if host and '.' in host and '%' not in host:domains[host].append({'apk':r['apk'],'dex':r['dex'],'offset':r['offset'],'value':r['value']})
(p/'domain-candidates.json').write_text(json.dumps(domains,indent=2))
print('Feature candidate counts:', {k:len(v) for k,v in features.items()});print('Primary user runtime permissions:',perms)
