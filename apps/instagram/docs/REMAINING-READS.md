# Review of all 37 previously unverified reads

Every operation in the original frozen set of 37 has a caller review and an explicit disposition. Its first pass repaired four. The follow-up passes repaired **six of the 33 remaining unsuccessful reads**, leaving **27 unverified**. Including successful reads outside this frozen set, the aggregate is **128 observed successful operations**. These are bounded observations, not complete server contracts.

The initial plan is `api/remaining-read-review.json`; the follow-up constructions are in `api/context-read-repair-plan.json`. Caller and helper proofs are in `api/bulk-trace/remaining-read-evidence.json` (170 methods and ten decoded keys). Swagger exposes `x-remaining-read-review`, `x-context-read-repairs`, the dated observations, and public query examples from successful corrections. Private context sources remain descriptors, never literal executable examples. `api/remaining-read-audit.json` accounts for every reviewed operation and preserves the initial disposition separately from a subsequent attempted correction.

The confirmed corrections are:

- `music/recent_searches`: use the `music_first` product, a fresh UUID from the traced launcher, and empty `search_session_id`; omit `should_disable_exposures` on this branch. The earlier empty browse-session fallback failed.

- `address_book/get_ccu_setting`: use the authenticated installation UUID as `device_id` and the saved phone UUID as `phone_id`. The Android device identifier is a different value.
- `business/account/get_content_inspiration_medias`: use the client-recognized dashboard entry point `pro_dash` instead of the `unknown` fallback.
- `discover/fetch_suggestion_details`: combine the verified account's `target_id` with comma-joined real recommendation IDs and `include_social_context=1`. The earlier target-only and chain-only variants failed.
- `fan_club/promotional_video` and `fan_club/welcome_video`: use an existing selected creator's `fan_club_id` from `followed_creators_to_susbcribe_to`. The earlier own-club lookup lacked context; both selected-club reads returned 200 / ok.

The runner only accepts documented GET operations with reviewed fields and matching APK provenance. It skips recorded attempts, blocks known side-effect routes, stops on account-protection signals, rejects redirects, disables environment proxies and never logs in. Private identity comes from the already verified local account and is used only in memory. Existing SDK identifiers are read only after validating private file permissions and matching account ownership. Feature IDs come from already-successful own-user or recommendation reads and are never fabricated. Saved observations retain only query keys, status, allowlisted response types and fixed error categories/words; no response values or raw messages.

A bounded follow-up also verified the account with the APK's exact app-version, version-code and Bloks headers in an isolated connection, preserving the original workbench session. Sixteen failing routes were tried with that profile; none succeeded. A tagging search-mode variant and the alternate stories prompt surface also failed. Profile-specific variants are blocked by the normal runner unless an isolated verified profile harness selects them. Header values and results are retained in the plan and Swagger.

Eleven 404 routes still match the APK's ordinary unsigned `/api/v1/` GET construction, with no supported request-format correction found. Additional corrected reads still return 400, 404, or application failure. Others require existing Facebook authorization, merchant, pending branded-media, survey, or world/page context. The own-user response supplied no club ID, so the first club-video variants were skipped; the subsequent selected-creator variants both succeeded; an explicit interop ID was available, but its lookup still returned 404. The recovery endpoint remains excluded. No recovery flow, account change, message, purchase, donation, import, tagging workflow or pagination was executed.

| Operation | Latest reviewed result |
|---|---|
| `/accounts/get_controls_filtered_media/` | 200 / ok |
| `/address_book/get_ccu_setting/` | 200 / ok; saved installation context |
| `/api/v1/text_feed/ig_bottom_sheet_info/` | 200 / ok |
| `/archive/live/live_archive_settings/` | Deferred: no-supported-correction |
| `/archive/reel/friends_with_history/` | Deferred: no-supported-correction |
| `/business/account/get_content_inspiration_medias/` | 200 / ok; pro_dash entry point |
| `/business/account/get_linked_whatsapp_account_info/` | Deferred: needs-context |
| `/business/account/get_profile_media/` | 404 / non-JSON |
| `/business/branded_content/bc_pending_tag_megaphone_for_brand/` | Deferred: needs-context |
| `/business/eligibility/get_appeals_data/` | Deferred: no-supported-correction |
| `/business/eligibility/get_product_violations_render_data/` | 404 / non-JSON |
| `/commerce/community/featured_products/merchant_management/` | Deferred: needs-context |
| `/commerce/inbox/prototype/setting/` | Deferred: no-supported-correction |
| `/commerce/product_feed/metadata/` | 404 / non-JSON |
| `/commerce/product_tagging/tagging_feed/` | 400 / fail; complete initial client state |
| `/commerce/purchase_protection/` | Deferred: no-supported-correction |
| `/direct_v2/icebreakers/get_msgr_ibs/` | Deferred: no-supported-correction |
| `/direct_v2/ranked_recipients/` | 200 / ok |
| `/discover/fetch_suggestion_details/` | 200 / ok; target plus real suggestion chain |
| `/fan_club/promotional_video/` | 200 / ok; existing selected creator club |
| `/fan_club/welcome_video/` | 200 / ok; existing selected creator club |
| `/fbsearch/profile_link_search/` | 400 / fail |
| `/fundraiser/story_charities_search/` | Deferred: no-supported-correction |
| `/metaverse_bridges/get_horizon_world_pages_stories/` | Deferred: needs-context |
| `/metaverse_bridges/get_horizon_world_pages/` | Deferred: needs-context |
| `/metaverse_bridges/get_meta_horizon_page_stories/` | Deferred: no-supported-correction |
| `/metaverse_bridges/get_meta_horizon_page/` | Deferred: needs-context |
| `/music/recent_searches/` | 200 / ok; music_first with generated browse UUID |
| `/scores/bootstrap/users/` | 200 / ok |
| `/stories/end_of_year/get_end_of_year_info/` | Deferred: no-supported-correction |
| `/stories/hallpass/hallpass_add_people_search/` | Deferred: no-supported-correction |
| `/stories/prompt_stickers/trending_prompts/` | 404 / non-JSON |
| `/survey/get/` | Deferred: needs-context |
| `/trusted_friend/get_non_expired_requests_info/` | Deferred: security-context |
| `/users/featureduserinfo/` | 404 / non-JSON |
| `/users/get_birthday_connections_info/` | Deferred: no-supported-correction |
| `/video_call/user/` | 404 / non-JSON; explicit own interop ID |

Individual deferral reasons and recovered input details are in the review JSON and Swagger. Corrected requests that still fail remain unverified; no feature entitlement, permanent retirement or exhaustive server error behavior is inferred from these responses.

```sh
python3 apps/instagram/scripts/repair-unverified-reads.py --target saved-installation-context --target professional-dashboard-entry --target own-target-with-existing-suggestions
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

The public result file preserves the reference observations, so that command skips recorded variants. For a fresh local run, preserve that file elsewhere before starting, retaining any protection stop for investigation. The runner requires the verified local Android session and skips unavailable feature context. Offline reproduction removes live results and regenerates the audit without runtime success claims. Diagnostic-only entries in the plan classify a prior failure; they do not claim a changed request construction or a repair.
