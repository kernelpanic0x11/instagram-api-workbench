# Review of all 37 previously unverified reads

Every operation in the frozen set has a caller review and an explicit disposition. Twelve supported corrections were retested once; four succeeded. The aggregate is now **120 successful reads** and **33 tested but unverified**. These are bounded historical observations, not complete server contracts.

The executable plan is `api/remaining-read-review.json`; caller and helper proofs are in `api/bulk-trace/remaining-read-evidence.json`. Seven encoded keys have compact switch-edge proofs rather than whole string-table dumps. Swagger exposes the findings under `x-remaining-read-review`, with query parameters marked server-requiredness unknown. `api/remaining-read-audit.json` accounts for every reviewed operation.

The runner only accepts documented GET operations with reviewed fields and matching APK provenance. It skips recorded attempts, blocks known side-effect routes, stops on account-protection signals, rejects redirects, disables environment proxies and never logs in. Private identity comes from the already verified local account and is used only in memory. Request UUIDs are generated locally, following the reviewed client helper. Saved observations retain only query keys, status and allowlisted response field types; no response values or raw bodies.

Twenty-five routes were deferred: some already match their reviewed initial-page construction and have no supported correction; others need device, Facebook, merchant, fan-club, survey, world/page or other caller context. None of those values were fabricated. A Facebook ID is not interchangeable with an Instagram ID. No recovery flow, account change, message, purchase, donation, import or pagination was executed.

| Operation | This pass |
|---|---|
| `/accounts/get_controls_filtered_media/` | 200 / ok |
| `/address_book/get_ccu_setting/` | Deferred: needs-context |
| `/api/v1/text_feed/ig_bottom_sheet_info/` | 200 / ok |
| `/archive/live/live_archive_settings/` | Deferred: no-supported-correction |
| `/archive/reel/friends_with_history/` | Deferred: no-supported-correction |
| `/business/account/get_content_inspiration_medias/` | 400 / fail |
| `/business/account/get_linked_whatsapp_account_info/` | Deferred: needs-context |
| `/business/account/get_profile_media/` | 404 / non-JSON |
| `/business/branded_content/bc_pending_tag_megaphone_for_brand/` | Deferred: needs-context |
| `/business/eligibility/get_appeals_data/` | Deferred: no-supported-correction |
| `/business/eligibility/get_product_violations_render_data/` | 404 / non-JSON |
| `/commerce/community/featured_products/merchant_management/` | Deferred: needs-context |
| `/commerce/inbox/prototype/setting/` | Deferred: no-supported-correction |
| `/commerce/product_feed/metadata/` | 404 / non-JSON |
| `/commerce/product_tagging/tagging_feed/` | Deferred: needs-context |
| `/commerce/purchase_protection/` | Deferred: no-supported-correction |
| `/direct_v2/icebreakers/get_msgr_ibs/` | Deferred: no-supported-correction |
| `/direct_v2/ranked_recipients/` | 200 / ok |
| `/discover/fetch_suggestion_details/` | 200 / fail |
| `/fan_club/promotional_video/` | Deferred: needs-context |
| `/fan_club/welcome_video/` | Deferred: needs-context |
| `/fbsearch/profile_link_search/` | 400 / fail |
| `/fundraiser/story_charities_search/` | Deferred: no-supported-correction |
| `/metaverse_bridges/get_horizon_world_pages_stories/` | Deferred: needs-context |
| `/metaverse_bridges/get_horizon_world_pages/` | Deferred: needs-context |
| `/metaverse_bridges/get_meta_horizon_page_stories/` | Deferred: no-supported-correction |
| `/metaverse_bridges/get_meta_horizon_page/` | Deferred: needs-context |
| `/music/recent_searches/` | Deferred: needs-context |
| `/scores/bootstrap/users/` | 200 / ok |
| `/stories/end_of_year/get_end_of_year_info/` | Deferred: no-supported-correction |
| `/stories/hallpass/hallpass_add_people_search/` | Deferred: no-supported-correction |
| `/stories/prompt_stickers/trending_prompts/` | 404 / non-JSON |
| `/survey/get/` | Deferred: needs-context |
| `/trusted_friend/get_non_expired_requests_info/` | Deferred: security-context |
| `/users/featureduserinfo/` | 404 / non-JSON |
| `/users/get_birthday_connections_info/` | Deferred: no-supported-correction |
| `/video_call/user/` | Deferred: needs-context |

Individual deferral reasons and recovered input details are in the review JSON and Swagger. Corrected requests that still fail remain unverified; no feature entitlement, permanent retirement or exhaustive server error behavior is inferred from these responses.

```sh
python3 apps/instagram/scripts/retest-remaining-reads.py
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

Repeating the runner does not repeat recorded calls. Protection stops require investigation. Offline reproduction removes live results and regenerates the audit without runtime success claims.
