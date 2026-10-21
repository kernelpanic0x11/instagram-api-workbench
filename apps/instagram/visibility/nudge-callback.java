    /* JADX WARN: Code duplicated, block: B:36:0x0156  */
    /* JADX WARN: Code duplicated, block: B:38:0x0166  */
    /* JADX WARN: Multi-variable type inference failed */
    /* JADX WARN: Type inference failed for: r11v0, types: [X.0JQr] */
    @Override // X.C05BI
    public final /* bridge */ /* synthetic */ void A0k(Object obj) {
        int iA03;
        int i;
        C05B6 c05b6;
        String str;
        String str2;
        int i2;
        int i3 = this.$t;
        if (i3 == 0) {
            iA03 = C05VE.A03(-320948054);
            C0aui c0aui = (C0aui) obj;
            int iA02 = C000H.A02(c0aui, -223769500);
            C04Sf c04Sf = (C04Sf) c0aui.A00;
            boolean zA1Y = AnonymousClass0020.A1Y(c04Sf.innerData.DH2(1331174208).length());
            C0RIG c0rig = (C0RIG) this.A02;
            C0RIG.A02(c0rig, zA1Y ? c04Sf.innerData.DH2(1331174208) : null, this.A03, this.A04, true);
            if (zA1Y) {
                Context contextRequireContext = c0rig.requireContext();
                String strDH2 = c04Sf.innerData.DH2(-1466137445);
                String strDH3 = c04Sf.innerData.DH2(2053365130);
                C05s2.A0V(strDH2, 1);
                C05s2.A0J(strDH3);
                C0IIp c0IIpA0Y = AnonymousClass0224.A0Y(contextRequireContext, strDH3, strDH2);
                c0IIpA0Y.A0D(new DialogInterface.OnClickListener() { // from class: X.0LHG
                    @Override // android.content.DialogInterface.OnClickListener
                    public final void onClick(DialogInterface dialogInterface, int i4) {
                        dialogInterface.dismiss();
                    }
                });
                C021X.A1Q(c0IIpA0Y);
            } else {
                ((C0OtX) this.A00).GSf();
            }
            C05VE.A0A(16261721, iA02);
            i = -1146340038;
        } else if (i3 == 1) {
            iA03 = C05VE.A03(586964380);
            int iA04 = C000H.A02(obj, -1412888564);
            C05BI c05bi = (C05BI) this.A00;
            if (c05bi != null) {
                c05bi.A0k(obj);
            }
            C05VE.A0A(-2036493202, iA04);
            i = 1879241187;
        } else if (i3 != 2) {
            iA03 = C05VE.A03(847212115);
            ClipsItemDictIntf clipsItemDictIntf = (ClipsItemDictIntf) obj;
            int iA05 = C05VE.A03(-1854710774);
            C05s2.A0V(clipsItemDictIntf, 0);
            super.A0k(clipsItemDictIntf);
            Media mediaCgb = clipsItemDictIntf.Cgb();
            if (mediaCgb.A6s() != null) {
                C01jc.A0D("IGMediaActionComposerLauncher", "ig_media_action composer CTA resolved to expiring media");
                C0Ir7.A01((Context) this.A00, "meta_ai_media_action_composer_expiring", 2131972989, 0);
                i2 = -394203081;
            } else {
                String str3 = this.A03;
                if ("remix".equals(str3)) {
                    C0Bca c0Bca = (C0Bca) C01lf.A01(114719);
                    FragmentActivity fragmentActivity = (FragmentActivity) this.A00;
                    List listA10 = AnonymousClass0224.A10(fragmentActivity);
                    C05s2.A0C(listA10);
                    Fragment fragment = (Fragment) C0BXD.A1N(listA10);
                    if (fragment == null) {
                        C01jc.A0D("IGMediaActionComposerLauncher", "No fragment to host the remix options sheet; opening the remix camera directly");
                        c0Bca.A00(fragmentActivity, fragmentActivity, C06up.A4Q, ((C0KSB) this.A02).A00, null, mediaCgb);
                    } else {
                        c0Bca.A01(fragment, fragmentActivity, C06up.A4Q, C02bQ.A01("direct_thread", true, false), ((C0KSB) this.A02).A00, mediaCgb, null);
                    }
                } else if ("template".equals(str3)) {
                    C0KSB c0ksb = (C0KSB) this.A02;
                    C0D9e c0D9eAU4 = mediaCgb.AU4("itas-android", 1368656848);
                    C0Bqw c0Bqw = new C0Bqw(AnonymousClass0224.A0J(c0D9eAU4, "itas-android", 0, 1368656848), c0D9eAU4);
                    String str4 = this.A04;
                    Context context = (Context) this.A00;
                    if (C049D.A02(c0ksb.A00, ConstantsKt.CAMERA_ID_FRONT)) {
                        String str5 = (String) AnonymousClass0064.A0g(c0Bqw.A01, c0Bqw, 168);
                        if (str5 != null) {
                            str4 = str5;
                        }
                        C0KV0.A0I(context, C049D.A00(C06up.A4Q, str4), false);
                    } else {
                        C01jc.A0D("IGMediaActionComposerLauncher", "ig_media_action template CTA needs Edits installed");
                        C0Ir7.A01(context, "meta_ai_media_action_template_no_edits", 2131972989, 0);
                    }
                }
                i2 = -143172633;
            }
            C05VE.A0A(i2, iA05);
            i = 525096545;
        } else {
            iA03 = C05VE.A03(-1161786413);
            C0Flo c0Flo = (C0Flo) obj;
            int iA06 = C05VE.A03(-1814287329);
            C05s2.A0V(c0Flo, 0);
            final UserSession userSession = (UserSession) this.A00;
            C03dR.A00().markerPoint(387850546, "network_request_success");
            if (C021X.A0J(c0Flo, "ig4a-instagram-schema", 2117425378, 0).DGk(-2053018862)) {
                c05b6 = (C05B6) this.A02;
                str = this.A03;
                str2 = this.A04;
                if (C01oK.A01(c05b6)) {
                    C03dR.A00().markerPoint(387850546, "nudge_will_show");
                    new C05uB(userSession).A00(c05b6, null, new Object() { // from class: X.0JQr
                    }, "com.bloks.www.ig.account_status.nudge.async", AnonymousClass0225.A0z(AnonymousClass0234.A00(), str2, C000H.A0Z("location", str), C000H.A0Z("analytics_module", "app_start")));
                }
            } else {
                C05Nh c05NhA01 = C05Nh.A6Y.A01((Context) this.A01);
                if (AnonymousClass0127.A1Y(c05NhA01, c05NhA01.A2M, C05Nh.A6a, 175)) {
                    c05b6 = (C05B6) this.A02;
                    str = this.A03;
                    str2 = this.A04;
                    if (C01oK.A01(c05b6)) {
                        C03dR.A00().markerPoint(387850546, "nudge_will_show");
                        new C05uB(userSession).A00(c05b6, null, new Object() { // from class: X.0JQr
                        }, "com.bloks.www.ig.account_status.nudge.async", AnonymousClass0225.A0z(AnonymousClass0234.A00(), str2, C000H.A0Z("location", str), C000H.A0Z("analytics_module", "app_start")));
                    }
                } else {
                    C03dR.A00().markerEnd(387850546, (short) 2);
                }
            }
            C05VE.A0A(-1409198850, iA06);
            i = 238852141;
        }
        C05VE.A0A(i, iA03);
    }