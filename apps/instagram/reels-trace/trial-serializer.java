    public final String A00(C0CcK c0CcK) {
        StringWriter stringWriterA0b = AnonymousClass0123.A0b();
        C04s2 c04s2A0V = AnonymousClass0123.A0V(stringWriterA0b);
        c04s2A0V.A0m();
        c04s2A0V.A0Z(AnonymousClass0238.A01(), c0CcK.A0q);
        C01yt.A0F(c04s2A0V, "video_segments");
        Iterator it = c0CcK.A1b.iterator();
        while (it.hasNext()) {
            C06Tc.A00(c04s2A0V, C0BQC.A1D(it));
        }
        c04s2A0V.A0i();
        List list = c0CcK.A1a;
        if (list != null) {
            Iterator itA17 = AnonymousClass0123.A17(c04s2A0V, AnonymousClass0021.A00(FilterIds.PARIS), list);
            while (itA17.hasNext()) {
                C06Tc.A00(c04s2A0V, C0BQC.A1D(itA17));
            }
            c04s2A0V.A0i();
        }
        C0F3w c0F3w = c0CcK.A0V;
        C05s2.A0R(c0F3w);
        c04s2A0V.A0Z("draft_save_state", c0F3w.A00);
        c04s2A0V.A17("draft_save_metadata");
        C0ERE c0ere = c0CcK.A0U;
        C05s2.A0V(c0ere, 1);
        c04s2A0V.A0m();
        c04s2A0V.A0Y("last_save_time", c0ere.A01);
        c04s2A0V.A0Y("last_user_save_time", c0ere.A02);
        c04s2A0V.A0Y("last_precapture_save_time", c0ere.A00);
        C01yt.A0F(c04s2A0V, "draft_save_apps");
        for (C0Bl0 c0Bl0 : c0ere.A03) {
            C05s2.A0R(c0Bl0);
            c04s2A0V.A1A(c0Bl0.A00);
        }
        c04s2A0V.A0i();
        c04s2A0V.A0j();
        C07EK c07ek = c0CcK.A0b;
        C05s2.A0R(c07ek);
        c04s2A0V.A0Z("clips_creation_type", c07ek.A00);
        String str = c0CcK.A0p;
        if (str != null) {
            c04s2A0V.A0Z("caption", str);
        }
        c04s2A0V.A0a("is_share_to_feed", c0CcK.A1r);
        String str2 = c0CcK.A1C;
        if (str2 != null) {
            c04s2A0V.A0Z("pending_media_id", str2);
        }
        C03EP c03ep = c0CcK.A0G;
        if (c03ep != null) {
            c04s2A0V.A17("post_capture_edits");
            C03E9.A00(c04s2A0V, c03ep);
        }
        List list2 = c0CcK.A1P;
        if (list2 != null) {
            Iterator itA18 = AnonymousClass0123.A17(c04s2A0V, "sticker_list", list2);
            while (itA18.hasNext()) {
                C0FXP.A01(c04s2A0V, (C0Ozc) itA18.next());
            }
            c04s2A0V.A0i();
        }
        List list3 = c0CcK.A1Q;
        if (list3 != null) {
            Iterator itA19 = AnonymousClass0123.A17(c04s2A0V, "timed_adjustments", list3);
            while (itA19.hasNext()) {
                C0YNj.A00(c04s2A0V, (C0RVG) itA19.next());
            }
            c04s2A0V.A0i();
        }
        C01yt.A0F(c04s2A0V, "recent_color_list");
        Iterator it2 = c0CcK.A1O.iterator();
        while (it2.hasNext()) {
            c04s2A0V.A0q(AnonymousClass0127.A0J(it2));
        }
        c04s2A0V.A0i();
        C01yt.A0F(c04s2A0V, "unschematized_compositions");
        Iterator it3 = c0CcK.A1G.iterator();
        while (it3.hasNext()) {
            C0F5t.A00(c04s2A0V, (C037k) it3.next());
        }
        c04s2A0V.A0i();
        C037Z c037z = c0CcK.A0d;
        C05s2.A0R(c037z);
        c04s2A0V.A0X("media_type", c037z.A00);
        ShareMediaLoggingInfo shareMediaLoggingInfo = c0CcK.A0F;
        if (shareMediaLoggingInfo != null) {
            c04s2A0V.A17("logging_info");
            C0FX1.A00(c04s2A0V, shareMediaLoggingInfo);
        }
        AudioOverlayTrack audioOverlayTrack = c0CcK.A0S;
        if (audioOverlayTrack != null) {
            c04s2A0V.A17("audio_overlay_track");
            C07Eb.A01(c04s2A0V, audioOverlayTrack);
        }
        AudioOverlayTrack audioOverlayTrack2 = c0CcK.A0R;
        if (audioOverlayTrack2 != null) {
            c04s2A0V.A17("attribution_only_audio_overlay_track");
            C07Eb.A01(c04s2A0V, audioOverlayTrack2);
        }
        C0FT0 c0ft0 = c0CcK.A0I;
        if (c0ft0 != null) {
            c04s2A0V.A17("remix_model");
            C0FSP.A00(c04s2A0V, c0ft0);
        }
        String str3 = c0CcK.A1B;
        if (str3 != null) {
            c04s2A0V.A0Z(C005P.A00(83), str3);
        }
        String str4 = c0CcK.A0s;
        if (str4 != null) {
            c04s2A0V.A0Z("cover_photo_path", str4);
        }
        ClipsDraftAsset clipsDraftAsset = c0CcK.A0a;
        if (clipsDraftAsset != null) {
            c04s2A0V.A17("cover_photo_asset");
            C06Tw.A01(c04s2A0V, clipsDraftAsset);
        }
        MediaCroppingCoordinates mediaCroppingCoordinates = c0CcK.A09;
        if (mediaCroppingCoordinates != null) {
            c04s2A0V.A17("crop_coordinates");
            C07bt.A00(c04s2A0V, mediaCroppingCoordinates);
        }
        String str5 = c0CcK.A0u;
        if (str5 != null) {
            c04s2A0V.A0Z("funded_content_deal_id", str5);
        }
        List list4 = c0CcK.A1W;
        if (list4 != null) {
            Iterator itA110 = AnonymousClass0123.A17(c04s2A0V, "people_tags", list4);
            while (itA110.hasNext()) {
                C0NX9.A00(c04s2A0V, (PeopleTag) itA110.next());
            }
            c04s2A0V.A0i();
        }
        List list5 = c0CcK.A1X;
        if (list5 != null) {
            Iterator itA111 = AnonymousClass0123.A17(c04s2A0V, "product_links", list5);
            while (itA111.hasNext()) {
                C0dN0.A00(c04s2A0V, (ProductLink) itA111.next());
            }
            c04s2A0V.A0i();
        }
        C0KA7 c0ka7 = c0CcK.A0Q;
        if (c0ka7 != null) {
            c04s2A0V.A17(AnonymousClass0021.A00(268));
            C04Lf.A00(c04s2A0V, c0ka7.B0W().A00(), true);
        }
        C0ndm c0ndm = c0CcK.A06;
        if (c0ndm != null) {
            c04s2A0V.A17("comment_quiz");
            C0ROJ.A00(c04s2A0V, c0ndm.Aiq().A01());
        }
        C03hU c03hU = c0CcK.A0c;
        if (c03hU != null) {
            c04s2A0V.A0Z("audience", c03hU.A00);
        }
        LocationDict locationDict = c0CcK.A08;
        if (locationDict != null) {
            c04s2A0V.A17("location");
            C02Al.A00(c04s2A0V, locationDict);
        }
        List list6 = c0CcK.A1V;
        if (list6 != null) {
            Iterator itA112 = AnonymousClass0123.A17(c04s2A0V, "locations", list6);
            while (itA112.hasNext()) {
                C02Al.A00(c04s2A0V, (LocationDict) itA112.next());
            }
            c04s2A0V.A0i();
        }
        List list7 = c0CcK.A1K;
        if (list7 != null) {
            Iterator itA113 = AnonymousClass0123.A17(c04s2A0V, "interest_topics", list7);
            while (itA113.hasNext()) {
                AnonymousClass0127.A1A(c04s2A0V, itA113);
            }
            c04s2A0V.A0i();
        }
        String str6 = c0CcK.A0r;
        if (str6 != null) {
            c04s2A0V.A0Z("collaborator_id", str6);
        }
        List list8 = c0CcK.A1F;
        if (list8 != null) {
            Iterator itA114 = AnonymousClass0123.A17(c04s2A0V, "collaborator_ids", list8);
            while (itA114.hasNext()) {
                AnonymousClass0127.A1A(c04s2A0V, itA114);
            }
            c04s2A0V.A0i();
        }
        String str7 = c0CcK.A0t;
        if (str7 != null) {
            c04s2A0V.A0Z("entry_point", str7);
        }
        String str8 = c0CcK.A1A;
        if (str8 != null) {
            c04s2A0V.A0Z(AnonymousClass0000.A00(483), str8);
        }
        String str9 = c0CcK.A0y;
        if (str9 != null) {
            c04s2A0V.A0Z(C005P.A00(359), str9);
        }
        String str10 = c0CcK.A0x;
        if (str10 != null) {
            c04s2A0V.A0Z(C005P.A00(358), str10);
        }
        Boolean bool = c0CcK.A0i;
        if (bool != null) {
            c04s2A0V.A0a(AnonymousClass0005.A00(447), bool.booleanValue());
        }
        String str11 = c0CcK.A11;
        if (str11 != null) {
            c04s2A0V.A0Z("linked_series_id", str11);
        }
        List list9 = c0CcK.A1M;
        if (list9 != null) {
            Iterator itA115 = AnonymousClass0123.A17(c04s2A0V, C005P.A00(80), list9);
            while (itA115.hasNext()) {
                C07Eb.A01(c04s2A0V, (AudioOverlayTrack) itA115.next());
            }
            c04s2A0V.A0i();
        }
        ClipsTemplateInfoImpl clipsTemplateInfoImpl = c0CcK.A05;
        if (clipsTemplateInfoImpl != null) {
            c04s2A0V.A17("clips_template_info");
            C05DZ.A00(c04s2A0V, clipsTemplateInfoImpl);
        }
        c04s2A0V.A0a("template_disabled", c0CcK.A1v);
        List list10 = c0CcK.A1E;
        if (list10 != null) {
            Iterator itA116 = AnonymousClass0123.A17(c04s2A0V, C005P.A00(322), list10);
            while (itA116.hasNext()) {
                AnonymousClass0127.A1A(c04s2A0V, itA116);
            }
            c04s2A0V.A0i();
        }
        List list11 = c0CcK.A1R;
        if (list11 != null) {
            Iterator itA117 = AnonymousClass0123.A17(c04s2A0V, "audio_effects", list11);
            while (itA117.hasNext()) {
                C0Yo2.A00.A02(c04s2A0V, (C0Nts) itA117.next());
            }
            c04s2A0V.A0i();
        }
        UpcomingEventImpl upcomingEventImpl = c0CcK.A0f;
        if (upcomingEventImpl != null) {
            c04s2A0V.A17("upcoming_event");
            C0deS.A00(c04s2A0V, upcomingEventImpl);
        }
        String str12 = c0CcK.A14;
        if (str12 != null) {
            c04s2A0V.A0Z("media_id", str12);
        }
        CropInfo cropInfo = c0CcK.A0E;
        if (cropInfo != null) {
            c04s2A0V.A17("video_crop_info");
            C0Fge.A00(c04s2A0V, cropInfo);
        }
        C0YKf c0YKf = c0CcK.A0H;
        if (c0YKf != null) {
            c04s2A0V.A17(C005P.A00(314));
            C0ROp.A00(c04s2A0V, c0YKf);
        }
        C0QL9 c0ql9 = c0CcK.A0B;
        if (c0ql9 != null) {
            c04s2A0V.A17(C005P.A00(323));
            C0ROu.A00(c04s2A0V, c0ql9);
        }
        C0YcZ c0YcZ = c0CcK.A0C;
        if (c0YcZ != null) {
            c04s2A0V.A17("facebook_cross_posting_model");
            c04s2A0V.A0m();
            c04s2A0V.A0a("enabled", c0YcZ.A05);
            c04s2A0V.A0a("is_account_linked", c0YcZ.A06);
            String str13 = c0YcZ.A01;
            if (str13 != null) {
                c04s2A0V.A0Z("account_id", str13);
            }
            String str14 = c0YcZ.A03;
            if (str14 != null) {
                c04s2A0V.A0Z("posting_type", str14);
            }
            String str15 = c0YcZ.A02;
            if (str15 != null) {
                c04s2A0V.A0Z("page_name", str15);
            }
            c04s2A0V.A0a("reels_share_to_facebook", c0YcZ.A08);
            String str16 = c0YcZ.A04;
            if (str16 != null) {
                c04s2A0V.A0Z("reels_destination_id", str16);
            }
            C06St c06St = c0YcZ.A00;
            if (c06St != null) {
                c04s2A0V.A0Z("reels_cross_app_share_type", c06St.A00);
            }
            c04s2A0V.A0a("reels_cross_app_share_fb_validation_check_bypass", c0YcZ.A07);
            c04s2A0V.A0j();
        }
        List list12 = c0CcK.A1Z;
        if (list12 != null) {
            Iterator itA118 = AnonymousClass0123.A17(c04s2A0V, "target_profiles", list12);
            while (itA118.hasNext()) {
                C06h5.A00(c04s2A0V, (PendingRecipient) itA118.next());
            }
            c04s2A0V.A0i();
        }
        c04s2A0V.A0a("is_draft_for_posted_clip", c0CcK.A1l);
        c04s2A0V.A0a("is_vcr_sticker_added", c0CcK.A1s);
        String str17 = c0CcK.A10;
        if (str17 != null) {
            c04s2A0V.A0Z(C005P.A00(75), str17);
        }
        String str18 = c0CcK.A0z;
        if (str18 != null) {
            c04s2A0V.A0Z("highlight_media_id", str18);
        }
        ExistingStandaloneFundraiserForFeedModel existingStandaloneFundraiserForFeedModel = c0CcK.A0g;
        if (existingStandaloneFundraiserForFeedModel != null) {
            c04s2A0V.A17(C005P.A00(344));
            C0ROo.A00(c04s2A0V, existingStandaloneFundraiserForFeedModel);
        }
        String str19 = c0CcK.A0v;
        if (str19 != null) {
            c04s2A0V.A0Z("fundraiser_user_id", str19);
        }
        NewFundraiserInfo newFundraiserInfo = c0CcK.A0O;
        if (newFundraiserInfo != null) {
            c04s2A0V.A17(C005P.A00(409));
            C0ROr.A00(c04s2A0V, newFundraiserInfo);
        }
        c04s2A0V.A0a("is_comment_disabled", c0CcK.A1k);
        c04s2A0V.A0a("is_caption_disabled", c0CcK.A1i);
        c04s2A0V.A0a(C005P.A00(164), c0CcK.A1o);
        c04s2A0V.A0a(C005P.A00(389), c0CcK.A1q);
        c04s2A0V.A0a(AnonymousClass0021.A00(314), c0CcK.A1m);
        c04s2A0V.A0a(AnonymousClass0000.A00(277), c0CcK.A1g);
        Boolean bool2 = c0CcK.A0h;
        if (bool2 != null) {
            c04s2A0V.A0a("is_auto_resharing_to_story_override", bool2.booleanValue());
        }
        List list13 = c0CcK.A1Y;
        if (list13 != null) {
            Iterator itA119 = AnonymousClass0123.A17(c04s2A0V, AnonymousClass0021.A00(184), list13);
            while (itA119.hasNext()) {
                C06UL.A00(c04s2A0V, (StackedTimelineAction) itA119.next());
            }
            c04s2A0V.A0i();
        }
        String str20 = c0CcK.A19;
        if (str20 != null) {
            c04s2A0V.A0Z("org_cta_type", str20);
        }
        c04s2A0V.A0X("max_duration_in_ms", c0CcK.A00);
        c04s2A0V.A0Y("created_at_time", c0CcK.A01);
        c04s2A0V.A0Y("deleted_at_time", c0CcK.A02);
        c04s2A0V.A0a(AnonymousClass0005.A00(225), c0CcK.A1f);
        c04s2A0V.A0a("archive_only", c0CcK.A1c);
        c04s2A0V.A0a(AnonymousClass0005.A00(398), c0CcK.A1d);
        String str21 = c0CcK.A16;
        if (str21 != null) {
            c04s2A0V.A0Z(C005P.A00(405), str21);
        }
        String str22 = c0CcK.A17;
        if (str22 != null) {
            c04s2A0V.A0Z("meta_verified_added_link_title", str22);
        }
        c04s2A0V.A0a(C005P.A00(406), c0CcK.A1t);
        String str23 = c0CcK.A15;
        if (str23 != null) {
            c04s2A0V.A0Z(C005P.A00(3), str23);
        }
        String str24 = c0CcK.A18;
        if (str24 != null) {
            c04s2A0V.A0Z("name", str24);
        }
        List list14 = c0CcK.A1U;
        if (list14 != null) {
            Iterator itA120 = AnonymousClass0123.A17(c04s2A0V, "clips_spin_swappable_text_list", list14);
            while (itA120.hasNext()) {
                ClipsSpinSwappableTextImpl__JsonHelper.A00(c04s2A0V, (C0ENl) itA120.next());
            }
            c04s2A0V.A0i();
        }
        C0QFT c0qft = c0CcK.A0L;
        if (c0qft != null) {
            c04s2A0V.A17("bio_product");
            C0ROq.A00(c04s2A0V, c0qft);
        }
        C0AJz c0AJz = c0CcK.A0D;
        if (c0AJz != null) {
            c04s2A0V.A17(AnonymousClass0005.A00(716));
            C0AJw.A00(c04s2A0V, c0AJz);
        }
        C0P8u c0P8u = c0CcK.A0M;
        if (c0P8u != null) {
            c04s2A0V.A17(C005P.A00(48));
            C0ROZ.A00(c04s2A0V, c0P8u);
        }
        C0QwT c0QwT = c0CcK.A07;
        if (c0QwT != null) {
            c04s2A0V.A17(AnonymousClass0000.A00(248));
            ContentSchedulingMetadata__JsonHelper.A00(c04s2A0V, c0QwT);
        }
        c04s2A0V.A0a("has_comment_prompt", c0CcK.A1e);
        C0DRM c0drm = c0CcK.A0N;
        if (c0drm != null) {
            c04s2A0V.A17("linked_media");
            C0DQo.A00(c04s2A0V, c0drm);
        }
        C01Ib c01Ib = c0CcK.A0A;
        if (c01Ib != null) {
            c04s2A0V.A0Z("gen_ai_detection_method", c01Ib.toString());
        }
        c04s2A0V.A0a("is_pinned", c0CcK.A1p);
        c04s2A0V.A0a("is_closed_captions_toggle_enabled", c0CcK.A1j);
        c04s2A0V.A0a(AnonymousClass0000.A00(518), c0CcK.A1w);
        C0ZpZ c0ZpZ = c0CcK.A0P;
        if (c0ZpZ != null) {
            c04s2A0V.A17("encoding_settings");
            C0Txc.A00(c04s2A0V, c0ZpZ);
        }
        c04s2A0V.A0a("share_only_to_profile", c0CcK.A1u);
        c04s2A0V.A0a("is_internal_only", c0CcK.A1n);
        Long l = c0CcK.A0n;
        if (l != null) {
            c04s2A0V.A0Y("gen_ai_camera_tool", l.longValue());
        }
        String str25 = c0CcK.A0w;
        if (str25 != null) {
            c04s2A0V.A0Z(AnonymousClass0005.A00(FilterIds.LUT_SPARK_4), str25);
        }
        c04s2A0V.A0a("is_basel", c0CcK.A1h);
        C08un c08un = c0CcK.A0T;
        if (c08un != null) {
            c04s2A0V.A0Z("draft_origin", c08un.A00);
        }
        c04s2A0V.A0Y("last_export_time", c0CcK.A03);
        C0YxI c0YxI = c0CcK.A0J;
        if (c0YxI != null) {
            c04s2A0V.A17("text_persistence_data");
            C0dMq.A00(c04s2A0V, c0YxI);
        }
        Boolean bool3 = c0CcK.A0k;
        if (bool3 != null) {
            c04s2A0V.A0a(C005P.A00(391), bool3.booleanValue());
        }
        Boolean bool4 = c0CcK.A0j;
        if (bool4 != null) {
            c04s2A0V.A0a(C005P.A00(390), bool4.booleanValue());
        }
        C0P6t c0P6t = c0CcK.A0Y;
        if (c0P6t != null) {
            c04s2A0V.A17(C005P.A00(336));
            C0WPl.A00(c04s2A0V, c0P6t);
        }
        C0TUv c0TUv = c0CcK.A0Z;
        if (c0TUv != null) {
            c04s2A0V.A17(C005P.A00(326));
            C0bTR.A00(c04s2A0V, c0TUv);
        }
        BaselVideoCompositionModelImpl baselVideoCompositionModelImpl = c0CcK.A04;
        if (baselVideoCompositionModelImpl != null) {
            c04s2A0V.A17(AnonymousClass0000.A00(237));
            BaselVideoCompositionModelImpl__JsonHelper.A00(c04s2A0V, baselVideoCompositionModelImpl);
        }
        List list15 = c0CcK.A1T;
        if (list15 != null) {
            Iterator itA121 = AnonymousClass0123.A17(c04s2A0V, C005P.A00(310), list15);
            while (itA121.hasNext()) {
                C06qf.A00(c04s2A0V, (BaselVideoElementImpl) itA121.next());
            }
            c04s2A0V.A0i();
        }
        List list16 = c0CcK.A1S;
        if (list16 != null) {
            Iterator itA122 = AnonymousClass0123.A17(c04s2A0V, C005P.A00(309), list16);
            while (itA122.hasNext()) {
                C04Go.A00(c04s2A0V, (BaselOverlayElementImpl) itA122.next());
            }
            c04s2A0V.A0i();
        }
        String str26 = c0CcK.A0o;
        if (str26 != null) {
            c04s2A0V.A0Z("basel_kit_id", str26);
        }
        ReframeItemMetadata reframeItemMetadata = c0CcK.A0e;
        if (reframeItemMetadata != null) {
            c04s2A0V.A17(C005P.A00(86));
            C0QdQ.A00(c04s2A0V, reframeItemMetadata);
        }
        C0Q0w c0Q0w = c0CcK.A0K;
        if (c0Q0w != null) {
            c04s2A0V.A17(C005P.A00(469));
            C0RON.A00(c04s2A0V, c0Q0w);
        }
        List list17 = c0CcK.A1I;
        if (list17 != null) {
            Iterator itA123 = AnonymousClass0123.A17(c04s2A0V, "generated_captions", list17);
            while (itA123.hasNext()) {
                AnonymousClass0127.A1A(c04s2A0V, itA123);
            }
            c04s2A0V.A0i();
        }
        C0TIo c0TIo = c0CcK.A0W;
        if (c0TIo != null) {
            c04s2A0V.A0Z(C005P.A00(84), c0TIo.A00);
        }
        Integer num = c0CcK.A0l;
        if (num != null) {
            c04s2A0V.A0X("background_color", num.intValue());
        }
        Integer num2 = c0CcK.A0m;
        if (num2 != null) {
            c04s2A0V.A0X("version", num2.intValue());
        }
        String str27 = c0CcK.A1D;
        if (str27 != null) {
            c04s2A0V.A0Z("teleprompter_script", str27);
        }
        C01yt.A0F(c04s2A0V, "mutation_clock");
        for (C0ESB c0esb : c0CcK.A1N) {
            C05s2.A0S(c0esb);
            c04s2A0V.A0m();
            c04s2A0V.A0Z("actor", c0esb.A01);
            c04s2A0V.A0Y("clock", c0esb.A00);
            c04s2A0V.A0j();
        }
        c04s2A0V.A0i();
        List list18 = c0CcK.A1J;
        if (list18 != null) {
            Iterator itA124 = AnonymousClass0123.A17(c04s2A0V, "import_fallbacks", list18);
            while (itA124.hasNext()) {
                C0WPi.A00(c04s2A0V, (C0P6Z) itA124.next());
            }
            c04s2A0V.A0i();
        }
        List list19 = c0CcK.A1H;
        if (list19 != null) {
            Iterator itA125 = AnonymousClass0123.A17(c04s2A0V, "extension_drops", list19);
            while (itA125.hasNext()) {
                C0QdO.A00(c04s2A0V, (C0HQW) itA125.next());
            }
            c04s2A0V.A0i();
        }
        String str28 = c0CcK.A13;
        if (str28 != null) {
            c04s2A0V.A0Z("longform_title", str28);
        }
        String str29 = c0CcK.A12;
        if (str29 != null) {
            c04s2A0V.A0Z("longform_associated_clips", str29);
        }
        List list20 = c0CcK.A1L;
        if (list20 != null) {
            Iterator itA126 = AnonymousClass0123.A17(c04s2A0V, "longform_linked_reels", list20);
            while (itA126.hasNext()) {
                C0QF1 c0qf1 = (C0QF1) itA126.next();
                C05s2.A0V(c0qf1, 1);
                c04s2A0V.A0m();
                String str30 = c0qf1.A04;
                if (str30 != null) {
                    c04s2A0V.A0Z("media_id", str30);
                }
                C0P6n c0P6n = c0qf1.A00;
                if (c0P6n != null) {
                    c04s2A0V.A17("pending");
                    c04s2A0V.A0m();
                    c04s2A0V.A0Z("upload_id", c0P6n.A04);
                    c04s2A0V.A0Z("video_path", c0P6n.A05);
                    String str31 = c0P6n.A02;
                    if (str31 != null) {
                        c04s2A0V.A0Z("caption", str31);
                    }
                    String str32 = c0P6n.A03;
                    if (str32 != null) {
                        c04s2A0V.A0Z("cover_image_path", str32);
                    }
                    Long l2 = c0P6n.A01;
                    if (l2 != null) {
                        c04s2A0V.A0Y("cover_frame_time_ms", l2.longValue());
                    }
                    Boolean bool5 = c0P6n.A00;
                    if (bool5 != null) {
                        c04s2A0V.A0a("is_cover_from_custom_photo", bool5.booleanValue());
                    }
                    c04s2A0V.A0j();
                }
                String str33 = c0qf1.A03;
                if (str33 != null) {
                    c04s2A0V.A0Z("link_title", str33);
                }
                Long l3 = c0qf1.A02;
                if (l3 != null) {
                    c04s2A0V.A0Y("start_timestamp_ms", l3.longValue());
                }
                Long l4 = c0qf1.A01;
                if (l4 != null) {
                    c04s2A0V.A0Y("scheduled_time_ms", l4.longValue());
                }
                c04s2A0V.A0j();
            }
            c04s2A0V.A0i();
        }
        C0P4q c0P4q = c0CcK.A0X;
        if (c0P4q != null) {
            c04s2A0V.A17(C005P.A00(432));
            C0WPk.A00(c04s2A0V, c0P4q);
        }
        c04s2A0V.A0j();
        return AnonymousClass0127.A0d(c04s2A0V, stringWriterA0b);
    }