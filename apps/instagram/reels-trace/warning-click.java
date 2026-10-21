    @Override // android.content.DialogInterface.OnClickListener
    public final void onClick(DialogInterface dialogInterface, int i) {
        C08xz c08xzA0W;
        C0H0c c0H0c;
        String str;
        C08xv c08xv;
        Integer num;
        String str2;
        String strA11;
        C01wg c01wg;
        String str3;
        Object obj;
        BrandedContentTag brandedContentTag;
        switch (this.$t) {
            case 0:
                C0RKH c0rkh = (C0RKH) this.A01;
                UserSession userSessionA08 = c0rkh.A08();
                User user = (User) this.A00;
                C0aLt.A04(c0rkh.getBaseAnalyticsModule(), userSessionA08, user.A7D());
                c0rkh.A04.add(user);
                C0aLt.A01(c0rkh.getBaseAnalyticsModule(), c0rkh.A08(), user.A7D());
                AnonymousClass0226.A1M(c0rkh);
                C0LEK.A04(c0rkh.getBaseAnalyticsModule(), c0rkh.A08(), AnonymousClass0009.A0Z, c0rkh.A08().userId, AnonymousClass0127.A0p("action_type", "continue"));
                if (c0rkh.A0B) {
                    C0RKH.A02(c0rkh);
                    return;
                }
                return;
            case 1:
                C0RKH c0rkh2 = (C0RKH) this.A01;
                C0aLt.A03(c0rkh2.getBaseAnalyticsModule(), c0rkh2.A08(), C021R.A0v(this.A00));
                C0LEK.A04(c0rkh2.getBaseAnalyticsModule(), c0rkh2.A08(), AnonymousClass0009.A0Z, c0rkh2.A08().userId, AnonymousClass0127.A0p("action_type", SelfieResultLogger.OUTCOME_CANCEL));
                return;
            case 2:
                BrandedContentDisclosureBaseViewModel brandedContentDisclosureBaseViewModel = (BrandedContentDisclosureBaseViewModel) this.A01;
                C0Eto baseAnalyticsModule = ((C05B6) this.A00).getBaseAnalyticsModule();
                C05s2.A0V(baseAnalyticsModule, 0);
                if (!brandedContentDisclosureBaseViewModel.A0F) {
                    brandedContentDisclosureBaseViewModel.A0B = false;
                    brandedContentDisclosureBaseViewModel.A14();
                    C04aF c04aFA00 = C04aF.A00(brandedContentDisclosureBaseViewModel.A12());
                    C0bvp c0bvp = new C0bvp();
                    c0bvp.A00 = false;
                    C$StoreFenceHelper.DUMMY_VOLATILE = 0;
                    c04aFA00.GcE(c0bvp);
                    return;
                }
                C0ndi c0ndi = brandedContentDisclosureBaseViewModel.A00;
                if (c0ndi != null) {
                    String str4 = null;
                    String strDH2 = AnonymousClass0465.A0A(c0ndi, "itas-android", -281179466, 0).DH2(-1938933922);
                    if (strDH2 != null) {
                        brandedContentDisclosureBaseViewModel.A0B = false;
                        brandedContentDisclosureBaseViewModel.A03 = "ad_toggle";
                        C0haQ.A01(brandedContentDisclosureBaseViewModel, strDH2, C00mb.A00(brandedContentDisclosureBaseViewModel), 1);
                        if (!brandedContentDisclosureBaseViewModel.A06.isEmpty() && (brandedContentTag = (BrandedContentTag) C0BXD.A1Q(brandedContentDisclosureBaseViewModel.A06, 0)) != null) {
                            str4 = brandedContentTag.A01;
                        }
                        UserSession userSessionA12 = brandedContentDisclosureBaseViewModel.A12();
                        String str5 = brandedContentDisclosureBaseViewModel.A04;
                        C05s2.A0V(userSessionA12, 0);
                        C00ws c00wsAMz = C02di.A01(baseAnalyticsModule, userSessionA12).AMz("instagram_bc_boost_code_access_token_disable");
                        c00wsAMz.AQu(C020R.A00(876), "ad_toggle");
                        c00wsAMz.AQu("media_id", str5);
                        c00wsAMz.AQu("sponsor_igid", str4);
                        c00wsAMz.Ei8();
                        return;
                    }
                    return;
                }
                return;
            case 3:
                C0SDw c0SDw = (C0SDw) this.A01;
                C00dQ.A0R((View) this.A00, -2052168796);
                C0Y5A c0y5aA00 = C0Y5A.A00(C020p.A0Q(c0SDw.A0W));
                Context contextRequireContext = c0SDw.requireContext();
                C00py c00pyA00 = LoaderManager.A00(c0SDw);
                Media media = c0SDw.A0B;
                if (media == null) {
                    C05s2.A0a("editMedia");
                    throw AnonymousClass0002.createAndThrow();
                }
                C0SFE c0sfe = new C0SFE(c0SDw);
                UserSession userSession = c0y5aA00.A00;
                C0D9e c0D9eAU4 = media.AU4("itas-android", 772595033);
                C05s2.A0V(c0D9eAU4, 0);
                C05s2.A0V(userSession, 0);
                C0D9e c0D9eCux = AnonymousClass0061.A08(c0D9eAU4, -712068656, 0).Cux(552573414);
                if (c0D9eCux == null || (strA11 = AnonymousClass0799.A11(c0D9eCux)) == null) {
                    strA11 = "";
                }
                C02sB c02sBA0J = AnonymousClass0221.A0J(C02rm.A01, C0MY4.A00, userSession);
                C0BUH.A1D(c02sBA0J, C000H.A0L(c0D9eAU4));
                c02sBA0J.AQE(DialogModule.KEY_TITLE, AnonymousClass0222.A0q(c0D9eAU4));
                c02sBA0J.AQE(IGQSSharingModule.MESSENGER_MEDIA_CAPTION_KEY, strA11);
                c02sBA0J.A0G("igtv_ads_toggled_on", false);
                C02sG c02sGA0V = AnonymousClass0221.A0V(c02sBA0J, AnonymousClass0000.A00(139), ConstantsKt.CAMERA_ID_FRONT, true);
                C0R0f c0R0f = new C0R0f(userSession);
                c0R0f.A00 = c0sfe;
                C$StoreFenceHelper.DUMMY_VOLATILE = 0;
                c02sGA0V.A09(c0R0f);
                C02uh.A00(contextRequireContext, c00pyA00, c02sGA0V);
                return;
            case 4:
                C0G5w c0G5w = (C0G5w) ((C0RGw) this.A01).A02.getValue();
                String str6 = ((String[]) this.A00)[i];
                C05s2.A09(str6);
                C0UEF c0uef = c0G5w.A00;
                C0D4X c0d4x = new C0D4X(str6, 34);
                C0ynL c0ynL = c0uef.A01;
                c0ynL.HUn(c0d4x.invoke(c0ynL.getValue()));
                while (!C0QI0.A01(c0uef, c0G5w.A01)) {
                }
                dialogInterface.dismiss();
                return;
            case 5:
                dialogInterface.dismiss();
                C0IFz.A00((C0DDx) this.A00, C0IFy.DECLINE, C0DDy.A1d, C0ArG.A11(), (UserSession) this.A01);
                return;
            case 6:
                C0YHi.A00(C0IFy.ACCEPT, (C0YHi) this.A01, null);
                C0YIm c0YIm = (C0YIm) this.A00;
                c0YIm.A03.A07(c0YIm.A00, c0YIm.A01, c0YIm.A02, false);
                return;
            case 7:
                C0ZiY.A00(C0IFy.OTHER, (C0ZiY) this.A01, null);
                C0YIx c0YIx = (C0YIx) this.A00;
                C02MW c02mw = C02MW.A01;
                UserSession userSession2 = c0YIx.A02;
                C06ls c06lsA0m = C0BRD.A0m();
                C0BSI.A1S(C0DDy.A1S, c06lsA0m);
                C0UIN c0uin = c0YIx.A01;
                C0BSI.A1R(c0uin.A00, c06lsA0m);
                c02mw.A0I(c06lsA0m, userSession2, "UPSELL");
                c0YIx.A03.A07(c0YIx.A00.requireContext(), c0uin, userSession2, true);
                return;
            case 8:
                C0ZiY.A00(C0IFy.ACCEPT, (C0ZiY) this.A01, null);
                C0YIx c0YIx2 = (C0YIx) this.A00;
                c0YIx2.A03.A07(c0YIx2.A00.requireContext(), c0YIx2.A01, c0YIx2.A02, false);
                return;
            case 9:
                C0BMO c0bmo = ((C0I4G) this.A01).A1G;
                c0bmo.A00 = (Medium) this.A00;
                c0bmo.A03.A0A(new C0Ale(C0THx.CLIPS));
                return;
            case 10:
                ((C0Bj8) this.A01).A05(((C0Snr) ((C0Tl6) this.A00)).A04, "ig_replace_captions", true);
                return;
            case 11:
                c08xv = (C08xv) this.A01;
                num = (Integer) this.A00;
                str2 = "Cancel";
                c08xv.A0P(num, str2);
                return;
            case 12:
                c08xv = (C08xv) this.A01;
                num = (Integer) this.A00;
                str2 = "OK";
                c08xv.A0P(num, str2);
                return;
            case 13:
                ((C08xv) this.A00).A0O(C0bhR.A0C, C0TQn.TAP, C0Dxj.A0e, "Save draft");
                obj = this.A01;
                AnonymousClass0064.A1E(obj);
                return;
            case 14:
                C0G7w c0G7w = (C0G7w) this.A01;
                UserSession userSessionA00 = C0G7w.A00(c0G7w);
                C06up c06up = c0G7w.A0A;
                C05s2.A0R(userSessionA00);
                C05s2.A0S(c06up);
                AnonymousClass0123.A0X(userSessionA00).A0n(c06up, C0Dxj.A6d, "CANCEL");
                obj = this.A00;
                AnonymousClass0064.A1E(obj);
                return;
            case 15:
            case 17:
                c01wg = (C01wg) this.A01;
                str3 = "continue";
                c01wg.A00 = str3;
                obj = this.A00;
                AnonymousClass0064.A1E(obj);
                return;
            case 16:
            case 18:
            default:
                c01wg = (C01wg) this.A01;
                str3 = "dismiss";
                c01wg.A00 = str3;
                obj = this.A00;
                AnonymousClass0064.A1E(obj);
                return;
            case 19:
                AnonymousClass0123.A0W(((C0ULN) this.A01).A00).A1D((C043C) this.A00, "LINKED_MEDIA_UNLINK_DIALOG_CANCEL");
                return;
            case 20:
                C05s2.A0R(dialogInterface);
                C0BQa.A1R(null, AnonymousClass0123.A0W((UserSession) this.A01), "RESUME_DRAFT_EXIT_DIALOG_DISCARD_EDITS");
                ((DialogInterface.OnClickListener) this.A00).onClick(dialogInterface, i);
                return;
            case 21:
                AnonymousClass0064.A1E(this.A00);
                c08xzA0W = AnonymousClass0123.A0W((UserSession) this.A01);
                c0H0c = null;
                str = "MAX_UPLOAD_LIMIT_EXCEEDED_DRAFT_TAPPED";
                C0BQa.A1R(c0H0c, c08xzA0W, str);
                return;
            case 22:
                AnonymousClass0064.A1E(this.A00);
                c08xzA0W = AnonymousClass0123.A0W((UserSession) this.A01);
                c0H0c = null;
                str = "DISTRIBUTION_LIMIT_WARNING_SHARE_TAPPED";
                C0BQa.A1R(c0H0c, c08xzA0W, str);
                return;
            case 23:
                C0BQa.A1R(null, AnonymousClass0123.A0W((UserSession) this.A01), "DISTRIBUTION_LIMIT_WARNING_EDIT_DRAFT_TAPPED");
                obj = this.A00;
                AnonymousClass0064.A1E(obj);
                return;
            case 24:
                DirectPrivateStoryRecipientController directPrivateStoryRecipientController = (DirectPrivateStoryRecipientController) this.A01;
                DirectPrivateStoryRecipientController.A0A((DirectShareTarget) this.A00, directPrivateStoryRecipientController);
                directPrivateStoryRecipientController.A1D = true;
                DirectPrivateStoryRecipientController.A0E(directPrivateStoryRecipientController);
                return;
            case 25:
                ((C01wg) this.A00).A00 = "dismiss";
                final C0SDM c0sdm = (C0SDM) this.A01;
                c0sdm.A0D.A00(C0TRm.MUTE_AUDIO_DISCARD);
                C02bo.A01(new Runnable() { // from class: X.0fvN
                    @Override // java.lang.Runnable
                    public final void run() {
                        C0Ki9.A01(c0sdm.A03);
                    }
                });
                return;
        }
    }