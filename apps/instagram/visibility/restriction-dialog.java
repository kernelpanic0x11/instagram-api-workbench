    /* JADX WARN: Code duplicated, block: B:10:0x0051  */
    /* JADX WARN: Code duplicated, block: B:43:0x00e6  */
    /* JADX WARN: Code duplicated, block: B:45:0x00ea  */
    /* JADX WARN: Code duplicated, block: B:47:0x00f9  */
    /* JADX WARN: Code duplicated, block: B:51:0x010b A[Catch: all -> 0x0136, TRY_LEAVE, TryCatch #1 {, blocks: (B:49:0x0107, B:51:0x010b), top: B:65:0x0107 }] */
    /* JADX WARN: Code duplicated, block: B:57:0x0139  */
    /* JADX WARN: Code duplicated, block: B:65:0x0107 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:8:0x004b  */
    public static void A0L(Object obj, Object obj2) {
        C0Awm c0Awm;
        C01qh c01qh;
        C00ez c00ezA1Y;
        C0MMB c0mmbA01;
        int iA03 = C05VE.A03(1553352155);
        C02nW c02nW = (C02nW) obj2;
        int iA04 = C05VE.A03(-1532351331);
        C05s2.A0V(c02nW, 0);
        FragmentActivity fragmentActivity = (FragmentActivity) ((C08uB) obj).A00;
        AtomicBoolean atomicBoolean = C02nJ.A00;
        C05Mf c05MfA01 = C05Ni.A01("last_user_restriction_sentry_block_event");
        if (c05MfA01.contains("last_user_restriction_sentry_block_event")) {
            try {
                Object objA07 = new Gson().A07(c05MfA01.getString("last_user_restriction_sentry_block_event", ""), C0Awm.class);
                if (objA07 != null) {
                    c0Awm = c02nW.A01;
                    if (!c0Awm.equals(objA07)) {
                        c0Awm = c02nW.A01;
                        if (!c0Awm.A0C && c0Awm.A0B) {
                            String str = c02nW.A04;
                            if (str == null) {
                                str = "";
                            }
                            C05nX c05nXA0Z = C000H.A0Z("restriction_detail_use_case", str);
                            String str2 = c02nW.A06;
                            if (str2 == null) {
                                str2 = "";
                            }
                            C05nX c05nXA0Z2 = C000H.A0Z("restriction_type", str2);
                            String str3 = c0Awm.A02;
                            if (str3 == null) {
                                str3 = "";
                            }
                            C05nX c05nXA0Z3 = C000H.A0Z("enrollment_time", str3);
                            String str4 = c0Awm.A04;
                            if (str4 == null) {
                                str4 = "";
                            }
                            C05nX c05nXA0Z4 = C000H.A0Z("expiration_time", str4);
                            String str5 = c0Awm.A01;
                            if (str5 == null) {
                                str5 = "";
                            }
                            C05nX c05nXA0Z5 = C000H.A0Z("dialogue_type", str5);
                            String str6 = c02nW.A03;
                            if (str6 == null) {
                                str6 = "";
                            }
                            C05nX c05nXA0Z6 = C000H.A0Z("responsible_policy", str6);
                            String str7 = c02nW.A02;
                            if (str7 == null) {
                                str7 = "";
                            }
                            C05nX c05nXA0Z7 = C000H.A0Z("category", str7);
                            String str8 = c0Awm.A03;
                            if (str8 == null) {
                                str8 = "";
                            }
                            C05nX c05nXA0Z8 = C000H.A0Z("error_code", str8);
                            String str9 = c02nW.A05;
                            if (str9 == null) {
                                str9 = "";
                            }
                            C05nX c05nXA0Z9 = C000H.A0Z("restriction_extra_data", str9);
                            String str10 = c0Awm.A09;
                            C0Ajj c0AjjA04 = C015E.A04(c02nW.A00, "com.bloks.www.instagram.igwb.exp.enforcement.dialog", C01qc.A01(c05nXA0Z, c05nXA0Z2, c05nXA0Z3, c05nXA0Z4, c05nXA0Z5, c05nXA0Z6, c05nXA0Z7, c05nXA0Z8, c05nXA0Z9, C000H.A0Z("reasons_thrown", str10 != null ? str10 : "")));
                            c0AjjA04.A00(new C0EIi(c02nW, fragmentActivity, 1));
                            C02uh.A03(c0AjjA04);
                        } else if (c02nW.A07) {
                            c01qh = c02nW.A00;
                            c00ezA1Y = fragmentActivity.A1Y();
                            C05s2.A0C(c00ezA1Y);
                            if (!c00ezA1Y.A14()) {
                                c0mmbA01 = ((C0KWr) C01lf.A01(147591)).A01(c01qh);
                                synchronized (c0mmbA01) {
                                    if (!c0mmbA01.A04) {
                                        c0mmbA01.A04 = true;
                                        HashMap map = new HashMap();
                                        map.put(C020R.A00(1021), "true");
                                        C0EIi c0EIi = new C0EIi(fragmentActivity, c0mmbA01, 0);
                                        C01qh c01qh2 = c0mmbA01.A02;
                                        C05s2.A0V(c01qh2, 0);
                                        C0Ajj c0AjjA05 = C015E.A04(c01qh2, "com.instagram.challenge.navigation.take_challenge", map);
                                        c0AjjA05.A00(c0EIi);
                                        C02uh.A03(c0AjjA05);
                                    }
                                }
                            }
                        } else {
                            C00ez c00ezA1Y2 = fragmentActivity.A1Y();
                            C05s2.A0C(c00ezA1Y2);
                            C02nJ.A01(C02nJ.A00(c02nW), c00ezA1Y2);
                        }
                    }
                } else {
                    c0Awm = c02nW.A01;
                    if (!c0Awm.A0C) {
                        if (c02nW.A07) {
                            c01qh = c02nW.A00;
                            c00ezA1Y = fragmentActivity.A1Y();
                            C05s2.A0C(c00ezA1Y);
                            if (!c00ezA1Y.A14()) {
                                c0mmbA01 = ((C0KWr) C01lf.A01(147591)).A01(c01qh);
                                synchronized (c0mmbA01) {
                                    if (!c0mmbA01.A04) {
                                        c0mmbA01.A04 = true;
                                        HashMap map2 = new HashMap();
                                        map2.put(C020R.A00(1021), "true");
                                        C0EIi c0EIi2 = new C0EIi(fragmentActivity, c0mmbA01, 0);
                                        C01qh c01qh3 = c0mmbA01.A02;
                                        C05s2.A0V(c01qh3, 0);
                                        C0Ajj c0AjjA06 = C015E.A04(c01qh3, "com.instagram.challenge.navigation.take_challenge", map2);
                                        c0AjjA06.A00(c0EIi2);
                                        C02uh.A03(c0AjjA06);
                                    }
                                }
                            }
                        } else {
                            C00ez c00ezA1Y3 = fragmentActivity.A1Y();
                            C05s2.A0C(c00ezA1Y3);
                            C02nJ.A01(C02nJ.A00(c02nW), c00ezA1Y3);
                        }
                    } else if (c02nW.A07) {
                        c01qh = c02nW.A00;
                        c00ezA1Y = fragmentActivity.A1Y();
                        C05s2.A0C(c00ezA1Y);
                        if (!c00ezA1Y.A14()) {
                            c0mmbA01 = ((C0KWr) C01lf.A01(147591)).A01(c01qh);
                            synchronized (c0mmbA01) {
                                if (!c0mmbA01.A04) {
                                    c0mmbA01.A04 = true;
                                    HashMap map3 = new HashMap();
                                    map3.put(C020R.A00(1021), "true");
                                    C0EIi c0EIi3 = new C0EIi(fragmentActivity, c0mmbA01, 0);
                                    C01qh c01qh4 = c0mmbA01.A02;
                                    C05s2.A0V(c01qh4, 0);
                                    C0Ajj c0AjjA07 = C015E.A04(c01qh4, "com.instagram.challenge.navigation.take_challenge", map3);
                                    c0AjjA07.A00(c0EIi3);
                                    C02uh.A03(c0AjjA07);
                                }
                            }
                        }
                    } else {
                        C00ez c00ezA1Y4 = fragmentActivity.A1Y();
                        C05s2.A0C(c00ezA1Y4);
                        C02nJ.A01(C02nJ.A00(c02nW), c00ezA1Y4);
                    }
                }
            } catch (C05Gs unused) {
            }
        } else {
            c0Awm = c02nW.A01;
            if (!c0Awm.A0C) {
                if (c02nW.A07) {
                    c01qh = c02nW.A00;
                    c00ezA1Y = fragmentActivity.A1Y();
                    C05s2.A0C(c00ezA1Y);
                    if (!c00ezA1Y.A14()) {
                        c0mmbA01 = ((C0KWr) C01lf.A01(147591)).A01(c01qh);
                        synchronized (c0mmbA01) {
                            if (!c0mmbA01.A04) {
                                c0mmbA01.A04 = true;
                                HashMap map4 = new HashMap();
                                map4.put(C020R.A00(1021), "true");
                                C0EIi c0EIi4 = new C0EIi(fragmentActivity, c0mmbA01, 0);
                                C01qh c01qh5 = c0mmbA01.A02;
                                C05s2.A0V(c01qh5, 0);
                                C0Ajj c0AjjA08 = C015E.A04(c01qh5, "com.instagram.challenge.navigation.take_challenge", map4);
                                c0AjjA08.A00(c0EIi4);
                                C02uh.A03(c0AjjA08);
                            }
                        }
                    }
                } else {
                    C00ez c00ezA1Y5 = fragmentActivity.A1Y();
                    C05s2.A0C(c00ezA1Y5);
                    C02nJ.A01(C02nJ.A00(c02nW), c00ezA1Y5);
                }
            } else if (c02nW.A07) {
                c01qh = c02nW.A00;
                c00ezA1Y = fragmentActivity.A1Y();
                C05s2.A0C(c00ezA1Y);
                if (!c00ezA1Y.A14()) {
                    c0mmbA01 = ((C0KWr) C01lf.A01(147591)).A01(c01qh);
                    synchronized (c0mmbA01) {
                        if (!c0mmbA01.A04) {
                            c0mmbA01.A04 = true;
                            HashMap map5 = new HashMap();
                            map5.put(C020R.A00(1021), "true");
                            C0EIi c0EIi5 = new C0EIi(fragmentActivity, c0mmbA01, 0);
                            C01qh c01qh6 = c0mmbA01.A02;
                            C05s2.A0V(c01qh6, 0);
                            C0Ajj c0AjjA09 = C015E.A04(c01qh6, "com.instagram.challenge.navigation.take_challenge", map5);
                            c0AjjA09.A00(c0EIi5);
                            C02uh.A03(c0AjjA09);
                        }
                    }
                }
            } else {
                C00ez c00ezA1Y6 = fragmentActivity.A1Y();
                C05s2.A0C(c00ezA1Y6);
                C02nJ.A01(C02nJ.A00(c02nW), c00ezA1Y6);
            }
        }
        try {
            C039Q c039qBBK = c05MfA01.BBK();
            c039qBBK.Gfq("last_user_restriction_sentry_block_event", new Gson().A0A(c0Awm));
            c039qBBK.apply();
        } catch (C0nlV unused2) {
        }
        C05VE.A0A(1485436555, iA04);
        C05VE.A0A(-1412256747, iA03);
    }