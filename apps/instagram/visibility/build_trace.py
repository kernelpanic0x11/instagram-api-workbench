import json,pathlib
p=pathlib.Path(__file__).resolve().parent
records={}
for f in p.glob('*.json'):
 try:r=(lambda value:value.get('structuredContent',value))(json.loads(f.read_text()))
 except (ValueError,AttributeError):continue
 if not r or 'evidence_id' not in r:continue
 assert r['subject']['digest']['sha256']=='4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b'
 records[f.stem]=r;n=r['normalized_result']
 if 'source' in n:f.with_suffix('.java').write_text(n['source']['text'])
index={k:{'evidence_id':r['evidence_id'],'operation':r.get('operation'),'metadata_omitted':[key for key in ('operation','parameters') if key not in r],'parameters':r.get('parameters',{}),'source_status':r['normalized_result'].get('source',{}).get('status'),'markers':r['normalized_result'].get('markers',[])} for k,r in records.items()}
(p/'evidence-index.json').write_text(json.dumps(index,indent=2))
def ev(*names):return '\n'.join('  '+name+'.json: '+records[name]['evidence_id'] for name in names)
text='''INSTAGRAM RECOMMENDATION-RESTRICTION DISPLAY TRACE

Target: com.instagram.android 451.0.0.53.80; base APK SHA-256
4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b
Method: static DEX cross-references and REA/JADX method decompilation.
No Instagram API requests or phone interactions were performed for this trace.

FINDING
The client contains a concrete recommendation-status notification path. It asks
for a required boolean deciding whether to show a nudge, then obtains a Bloks
payload and hands the result to the Bloks action/UI machinery. This is a
notification/display mechanism, not a recovered ranking or suppression algorithm.

1. RECOMMENDATION-STATUS REQUEST — ANSWERED AT CLIENT-CODE LEVEL
X.C0L1j.A02 builds a request using the relative path:
  users/get_recommendation_status_nudge/
It binds response parser C0dmv and callback C0EoX with discriminator 2, then
schedules the request. Its instrumentation labels the module app_start. Caller
frequency, HTTP verb, complete base URL and actual on-device execution were not
established; app_start instrumentation alone does not prove every launch calls it.

'''+ev('recommendation-nudge-request')+'''

2. RECEIVED FIELD AND DISPLAY GATE — ANSWERED AT CLIENT-CODE LEVEL
C0dmv.unsafeParseFromJson requires show_recommendation_status_nudge. Missing that
field takes a parse-error path. A present value is stored in the generated
XDTRecommendationStatusNudgeResponse model.
C0EoX.A0k branch 2 reads a boolean using numeric key -2053018862. That
number exactly matches Java String.hashCode for show_recommendation_status_nudge,
corroborating the parser-to-callback mapping; the generic accessor internals were
not traced. A positive response takes
the nudge path; the false branch can also take it through a local preference
lookup. That preference's semantic name has not been resolved. An opaque host guard (C01oK.A01)
must pass before scheduling display. The callback records
network_request_success and nudge_will_show, or ends its marker without a nudge.
Decompiled callback has code-duplication and type-inference warnings: this is
static reconstructed control flow, not a runtime observation.

'''+ev('nudge-response-parser','nudge-callback')+'''

3. FETCH AND HANDLE THE NUDGE — ANSWERED TO BLOKS EXECUTION BOUNDARY
The selected app identifier is:
  com.bloks.www.ig.account_status.nudge.async
The call carries location, analytics_module=app_start, and a generated
correlation/session value under an obfuscated key helper. C05uB prevents a second
request on the same instance while its boolean guard is set, attaches C0EJA and
schedules the Bloks request. This does not establish a global once-only policy.
C015E.A03 chooses its transport conditionally. In the legacy endpoint branch,
com.bloks.www names use bloks/async_action/<app-id>/; an alternate configured
branch is also present. The endpoint request builder adds bloks_versioning_id,
bk_client_context, parameters and X-IG-BLOKS-SERIALIZE-PAYLOAD: true.
C0EJA.A06 handles the returned payload, constructs the session/UI context,
checks fragment-manager conditions, and passes the payload to C0KYw.A01.
The returned Bloks payload and exact displayed text were not captured. A true
nudge flag is not itself proof of a restriction: it controls a prompt and can
also be overridden by a local preference.

'''+ev('nudge-bloks-request','bloks-async-dispatch','bloks-http-request','nudge-render-callback')+'''

4. ACCOUNT STATUS SCREEN — PARTIALLY ANSWERED
AccountStatusUrlHandlerActivity.A2V reads the location query parameter and calls
C0L1j.A00. This launcher creates the Bloks screen identifier:
  com.bloks.www.ig.ixt.triggers.screen.ig_account_status
Its map includes location, viewer_id, and an optional enforcement_id supplied by
the caller. The URL activity passes null for enforcement_id in the inspected
path, so not every entry is enforcement-specific. It also logs trigger_session_id
from the shared parameter map. The screen is configured through C0RY3.A03,
IgBloksScreenConfig and C0LFI, then C0LEI creates a C0StF fragment with those
arguments and the session binding. The launcher supplies network success/failure
callbacks and a request_error UI path.
A generic Bloks app loader supports bloks/apps/<app-id>/ or
IGBloksAppRootQuery depending on configuration. The final rendered layout,
restriction-detail navigation and appeal behavior are not recoverable from these
selected methods without the corresponding payload or further renderer tracing.

'''+ev('accountstatus-entry','accountstatus-launch','bloks-fragment-build','accountstatus-screen-arguments','bloks-render-fragment','bloks-request-dispatch')+'''

5. GENERAL RESTRICTION/ERROR DISPLAY — SEPARATE, PARTIALLY ANSWERED
C01pP.A01 parses restriction_type, restriction_detail_use_case,
responsible_policy, enrollment_time, expiration_time, restriction_extra_data,
reasons_thrown, feedback_title, feedback_message, feedback_appeal_label,
feedback_url and other error/challenge fields.
C08uB.A0L passes similarly named values to:
  com.bloks.www.instagram.igwb.exp.enforcement.dialog
It compares a stored last_user_restriction_sentry_block_event, has conditional
challenge/fallback branches, and persists the event. The reconstructed source has
multiple duplicated-block warnings; exact suppression and deduplication semantics
need raw-instruction or runtime corroboration. This shared path is broader than
recommendation eligibility; do not equate every restriction with a shadow ban.

'''+ev('restriction-parser','restriction-dialog')+'''

CORRECTION TO EARLIER STRING-ONLY FINDINGS
is_recommendable is used by the GroupMetadata serializer, specifically the
GroupMetadataImpl.A0O boolean. Neighboring fields include chat_thread_id, group_pk
and is_viewer_admin. It is not evidence of an account-wide recommendation flag.
See group-recommendable-field.json and dex-string-references.json.

WHAT REMAINS UNKNOWN
- Whether this account currently has any recommendation restriction.
- Why a backend decides to show the nudge; a UI boolean is not a penalty score.
- Whether every recommendation restriction generates a visible notification.
- Exact server-supplied wording, affected content, expiry and appeal eligibility.
- Which conditional transport and UI branches execute on this device.
- Any effect on ranking, distribution magnitude or recovery time.

NEXT EVIDENCE NEEDED
An actual Account Status screen/payload would establish account-specific display
and wording. A controlled runtime observation could validate which requests and
branches execute. No restriction-triggering actions, account changes or API
replays were needed for this static trace.

REPRODUCTION
rea-session.mjs runs the existing pinned REA launcher over local MCP stdio.
Individual tool results retain complete structured Evidence, parameters, digest,
limitations and engine metadata. evidence-index.json indexes those records;
.java files are convenience excerpts, not original source or buildable code.
dex_refs.py separately supplies exact DEX const-string instruction references.
'''
(p/'TRACE.txt').write_text(text)
print('Validated',len(records),'REA records; wrote TRACE.txt and evidence-index.json')
