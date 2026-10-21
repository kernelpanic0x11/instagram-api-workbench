#!/usr/bin/env python3
"""Offline, conservative candidate catalog. No HTTP methods inferred from strings."""
import argparse, collections, gzip, hashlib, json, re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
PATH = re.compile(r'^/?[A-Za-z0-9_~.%{}:@+-]+(?:/[A-Za-z0-9_~.%{}:@+=$-]*)+(?:\?[^\s<>"\\]*)?$')
DESCRIPTOR = re.compile(r'^\[*L[^\s;]+;$')
OP = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*(?:Query|Mutation|Subscription)(?:\$[A-Za-z0-9_]+)?$')
DOCUMENT = re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)\s*[({]')
BLOKS = re.compile(r'^com\.bloks\.www\.[A-Za-z0-9_.]+$')
FILE = re.compile(r'\.(?:png|jpe?g|webp|gif|svg|xml|json|txt|bin|so|dex|apk|jar|zip|ttf|otf|mp4|webm|wav|mp3|html?|js|css|pb|db|log|csv|kt|java|cpp|h|prof|lock)(?:$|[?#])', re.I)
FILESYSTEM = re.compile(r'^(?:/(?:data|proc|sys|system|dev|mnt|storage|sdcard|vendor|apex|product|etc|cache)/|/?(?:assets?|res|lib|META-INF|cache|files|datastore|audio|fonts|drawable|raw|mipmap|values|layout)/)')
API_MARKER = re.compile(r'(?:^|/)(?:api|graphql|v[0-9]+|rupload_[a-z0-9_]+)(?:/|$)', re.I)
KNOWN_ROUTE_FAMILIES = set('accounts ads archive attestation business clips collections commerce consent creatives creators direct_v2 discover fan_club fb fbsearch feed friendships fundraiser launcher live map media mental_well_being metaverse_bridges multiple_accounts music notifications push stories text_feed third_party_sharing upcoming_events users usertags video_call address_book'.split())
ACTION = re.compile(r'(?:^|/)(?:get|set|create|delete|update|fetch|upload|configure|search|list|send|submit|remove|add|edit|enable|disable|register|unregister|report|validate|check|approve|deny|mark|mute|unmute|subscribe|unsubscribe|publish|dismiss|accept|reject|broadcast|sync|refresh|complete|cancel|reorder|save|unsave|follow|unfollow|like|unlike|archive|unarchive|block|unblock)(?:_|/|$)')

def classify(s):
    if BLOKS.fullmatch(s):
        return {'kind':'bloks_id','reason':'com.bloks.www namespace; identifier only, not HTTP route'}
    if OP.fullmatch(s):
        return {'kind':'graphql_operation','reason':'operation-like name suffix; not a verified registered operation'}
    if len(s) <= 100000 and (s.lstrip().startswith(('query ', 'mutation ', 'subscription '))):
        names=DOCUMENT.findall(s)
        if names:
            return {'kind':'graphql_document','operations':[{'operation_type':t,'name':n} for t,n in names],'reason':'embedded GraphQL document syntax'}
    if len(s)>2048 or any(c.isspace() for c in s):return None
    if s.startswith(('http://','https://')):
        try:u=urlsplit(s)
        except ValueError:return {'kind':'url_candidate','reason':'HTTP-like URL that could not be parsed'}
        if not u.netloc:return None
        api_url=bool(u.path and u.path != '/') and (bool(re.search(r'(?:^|/)(?:api|graphql)(?:/|$)',u.path)) or u.hostname in ('graph.facebook.com','graph.instagram.com','graph-video.facebook.com','i.instagram.com','b.i.instagram.com')) and not (FILE.search(u.path) or re.match(r'^/(?:legal|help|about|developer|developers|docs?|documentation)/',u.path))
        out={'kind':'absolute_api_url' if api_url else 'url_candidate','reason':'explicit API path or API host' if api_url else 'HTTP URL; API role unverified','host':u.netloc,'scheme':u.scheme}
        if u.path:out['path']=u.path
        return out
    if '://' in s:
        return {'kind':'non_http_uri','reason':'deep link, content URI or other non-HTTP scheme'}
    if DESCRIPTOR.fullmatch(s) or '(' in s or ')' in s:return None
    if '/' not in s or not PATH.fullmatch(s):return None
    if FILE.search(s) or FILESYSTEM.search(s):
        return {'kind':'asset_or_filesystem_path','reason':'file extension or asset/filesystem prefix'}
    path=s if s.startswith('/') else '/'+s
    if re.fullmatch(r'/?(?:api/)?v[0-9]+/?|/?api/?|/?rupload_[a-z0-9_]+/?',s):
        return {'kind':'path_fragment','path':path,'reason':'API or upload prefix without a resource suffix'}
    if API_MARKER.search(s):
        return {'kind':'route_candidate','path':path,'reason':'explicit API/version/upload path marker','confidence':'lexical-high'}
    route_part=s.split('?',1)[0]
    segments=[x for x in route_part.split('/') if x]
    if len(segments)>=2 and segments[0] in KNOWN_ROUTE_FAMILIES:
        return {'kind':'route_candidate','path':path,'reason':'known Instagram route-family prefix; method and actual request use unverified','confidence':'lexical-medium'}
    if route_part.endswith('/') and len(segments)>=2 and not re.search('[A-Z]',route_part):
        return {'kind':'route_candidate','path':path,'reason':'lowercase multi-segment trailing-slash route shape','confidence':'lexical-medium'}
    if ACTION.search(s) and not re.search('[A-Z]',s):
        return {'kind':'route_candidate','path':path,'reason':'multi-segment action-like route shape','confidence':'lexical-medium'}
    if s.startswith('/') or s.endswith('/') or '%' in s or '{' in s:
        return {'kind':'path_fragment','path':path,'reason':'path-like fragment; endpoint completeness and API use unverified'}
    return {'kind':'ambiguous_path','path':path,'reason':'slash-delimited string; could be API, MIME type, class name, metric or other value'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'evidence/all-dex-strings.jsonl.gz');p.add_argument('--output',type=Path,default=Path(__file__).with_name('catalog.json'));a=p.parse_args()
    grouped={};stats=collections.Counter()
    with gzip.open(a.input,'rt') as f:
        for line_number,line in enumerate(f,1):
            row=json.loads(line);stats['input_records']+=1;s=row.get('value','');c=classify(s)
            if c is None:continue
            key=(s,c['kind'])
            if key not in grouped:grouped[key]={'raw':s,**c,'evidence':[]}
            grouped[key]['evidence'].append({k:v for k,v in row.items() if k!='value'}|{'source_line':line_number})
            stats['matched_records']+=1
    entries=sorted(grouped.values(),key=lambda e:(e['kind'],e['raw']))
    counts=collections.Counter(e['kind'] for e in entries)
    out={'schema_version':1,'source':str(a.input.relative_to(ROOT)) if a.input.is_relative_to(ROOT) else str(a.input),'source_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'entries':entries,'stats':dict(stats)|{'unique_entries':len(entries),'by_kind':dict(counts)},'limitations':['Static lexical catalog of indexed DEX strings only; not all APIs used by Instagram. Native code, packed assets, generated/composed paths, server-delivered code and server-only APIs are outside this extraction.','No HTTP verb, base URL for relative routes, authentication, request schema, response schema, availability or authorization inferred.','Raw strings and all observed source records are retained. Relative path only receives a leading slash; no /api/v1 prefix is assumed. Format placeholders remain verbatim.','Route candidates require semantic verification at request-building call sites. Lexical matches can include non-API paths, MIME types, class names and telemetry strings.','GraphQL operation suffix matching is a candidate heuristic and can include helper names. Bloks IDs identify server-driven UI/action identifiers and are not separate HTTP endpoints.','Paths and operations can overlap or alias each other. Absolute URLs may refer to third-party, documentation or test infrastructure. No requests were made.']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['stats'],indent=2))
if __name__=='__main__':main()
