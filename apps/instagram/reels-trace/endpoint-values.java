.method public static constructor <clinit>()V
    .registers 46

    new-instance v23, LX/0auv;

    invoke-direct/range {v23 .. v23}, LX/0auv;-><init>()V

    sput-object v23, LX/0bm8;->A0L:LX/0bm8;

    new-instance v24, LX/0aut;

    invoke-direct/range {v24 .. v24}, LX/0aut;-><init>()V

    sput-object v24, LX/0bm8;->A08:LX/0bm8;

    const/4 v3, 0x2

    const-string v2, "media/configure_sidecar/"

    const-string v1, "SIDECAR"

    new-instance v22, LX/0bm8;

    move-object/from16 v0, v22

    invoke-direct {v0, v1, v3, v2}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v22, LX/0bm8;->A0J:LX/0bm8;

    const/4 v3, 0x3

    const-string v2, "media/configure_sidecar_children/"

    const-string v1, "SIDECAR_CHILDREN"

    new-instance v21, LX/0bm8;

    move-object/from16 v0, v21

    invoke-direct {v0, v1, v3, v2}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v21, LX/0bm8;->A0K:LX/0bm8;

    const/4 v3, 0x4

    const-string v2, "media/configure_to_nametag/"

    const-string v1, "NAMETAG"

    new-instance v20, LX/0bm8;

    move-object/from16 v0, v20

    invoke-direct {v0, v1, v3, v2}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v20, LX/0bm8;->A0D:LX/0bm8;

    const/4 v3, 0x5

    const-string v2, "media/configure/"

    const-string v1, "FEED"

    new-instance v19, LX/0bm8;

    move-object/from16 v0, v19

    invoke-direct {v0, v1, v3, v2}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v19, LX/0bm8;->A09:LX/0bm8;

    const/4 v3, 0x6

    const-string v2, "media/upload_finish/"

    const-string v1, "FINISH"

    new-instance v18, LX/0bm8;

    move-object/from16 v0, v18

    invoke-direct {v0, v1, v3, v2}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v18, LX/0bm8;->A0A:LX/0bm8;

    const/4 v3, 0x7

    const-string v2, "media/update_media_with_pdq_hash_info/"

    const-string v1, "PDQ_HASH_REPORT"

    new-instance v17, LX/0bm8;

    move-object/from16 v0, v17

    invoke-direct {v0, v1, v3, v2}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v17, LX/0bm8;->A0G:LX/0bm8;

    const/16 v3, 0x8

    const-string v2, "media/configure_to_clips/"

    const-string v1, "CLIPS"

    new-instance v16, LX/0bm8;

    move-object/from16 v0, v16

    invoke-direct {v0, v1, v3, v2}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v16, LX/0bm8;->A04:LX/0bm8;

    new-instance v32, LX/0auu;

    invoke-direct/range {v32 .. v32}, LX/0auu;-><init>()V

    sput-object v32, LX/0bm8;->A0B:LX/0bm8;

    const/16 v2, 0xa

    const-string v1, "media/configure_to_comment/"

    const-string v0, "COMMENT_MEDIA"

    new-instance v15, LX/0bm8;

    invoke-direct {v15, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v15, LX/0bm8;->A06:LX/0bm8;

    const/16 v2, 0xb

    const-string v1, "media/configure_to_media_kit_cover/"

    const-string v0, "MEDIA_KIT"

    new-instance v14, LX/0bm8;

    invoke-direct {v14, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v14, LX/0bm8;->A0C:LX/0bm8;

    const/16 v2, 0xc

    const-string v1, "media/configure_text_only_post/"

    const-string v0, "TEXT_ONLY"

    new-instance v13, LX/0bm8;

    invoke-direct {v13, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v13, LX/0bm8;->A0P:LX/0bm8;

    const/16 v2, 0xd

    const-string v1, "media/configure_text_post_app_feed/"

    const-string v0, "TEXT_APP_FEED"

    new-instance v12, LX/0bm8;

    invoke-direct {v12, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v12, LX/0bm8;->A0N:LX/0bm8;

    const/16 v2, 0xe

    const-string v1, "media/configure_text_post_app_sidecar/"

    const-string v0, "TEXT_APP_SIDECAR"

    new-instance v11, LX/0bm8;

    invoke-direct {v11, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v11, LX/0bm8;->A0O:LX/0bm8;

    const/16 v2, 0xf

    const-string v1, "direct_v2/threads/broadcast/raven_attachment/"

    const-string v0, "RAVEN"

    new-instance v10, LX/0bm8;

    invoke-direct {v10, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v10, LX/0bm8;->A0I:LX/0bm8;

    const/16 v2, 0x10

    const-string v1, "media/configure_to_open_carousel/"

    const-string v0, "OPEN_CAROUSEL_SUBMISSION"

    new-instance v9, LX/0bm8;

    invoke-direct {v9, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v9, LX/0bm8;->A0F:LX/0bm8;

    const/16 v2, 0x11

    const-string v1, "media/configure_to_cutout_sticker/"

    const-string v0, "CUTOUT_STICKER"

    new-instance v8, LX/0bm8;

    invoke-direct {v8, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v8, LX/0bm8;->A07:LX/0bm8;

    const/16 v2, 0x12

    const-string v1, "media/configure_to_story_template_asset/"

    const-string v0, "STORY_TEMPLATE_ASSET"

    new-instance v7, LX/0bm8;

    invoke-direct {v7, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v7, LX/0bm8;->A0M:LX/0bm8;

    const/16 v2, 0x13

    const-string v1, "media/configure_to_reusable_template_assets/"

    const-string v0, "CLIPS_TEMPLATE_REUSABLE_ASSETS"

    new-instance v6, LX/0bm8;

    invoke-direct {v6, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v6, LX/0bm8;->A05:LX/0bm8;

    const/16 v2, 0x14

    const-string v1, "media/manage_submitted_sub_post/"

    const-string v0, "OPEN_CAROUSEL_ACCEPTANCE"

    new-instance v5, LX/0bm8;

    invoke-direct {v5, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v5, LX/0bm8;->A0E:LX/0bm8;

    const/16 v2, 0x15

    const-string v1, "media/configure_to_quick_snap/"

    const-string v0, "QUICKSNAP"

    new-instance v4, LX/0bm8;

    invoke-direct {v4, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v4, LX/0bm8;->A0H:LX/0bm8;

    const/16 v2, 0x16

    const-string v1, "media/configure_to_basel_elements/"

    const-string v0, "BASEL_TEMPLATE"

    new-instance v3, LX/0bm8;

    invoke-direct {v3, v0, v2, v1}, LX/0bm8;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v3, LX/0bm8;->A03:LX/0bm8;

    move-object/from16 v36, v12

    move-object/from16 v37, v11

    move-object/from16 v38, v10

    move-object/from16 v39, v9

    move-object/from16 v40, v8

    move-object/from16 v41, v7

    move-object/from16 v42, v6

    move-object/from16 v43, v5

    move-object/from16 v44, v4

    move-object/from16 v45, v3

    move-object/from16 v26, v21

    move-object/from16 v27, v20

    move-object/from16 v28, v19

    move-object/from16 v29, v18

    move-object/from16 v30, v17

    move-object/from16 v31, v16

    move-object/from16 v33, v15

    move-object/from16 v34, v14

    move-object/from16 v35, v13

    move-object/from16 v25, v22

    filled-new-array/range {v23 .. v45}, [LX/0bm8;

    move-result-object v0

    sput-object v0, LX/0bm8;->A02:[LX/0bm8;

    invoke-static {v0}, LX/05r3;->A00([Ljava/lang/Enum;)LX/05r4;

    move-result-object v0

    sput-object v0, LX/0bm8;->A01:Lkotlin/enums/EnumEntries;

    return-void
.end method