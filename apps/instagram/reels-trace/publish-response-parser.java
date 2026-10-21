    /* JADX WARN: Can't fix incorrect switch cases order, some code will duplicate */
    /* JADX WARN: Code duplicated, block: B:10:0x002a  */
    @Override // X.C05Bj
    public final /* bridge */ /* synthetic */ Object unsafeParseFromJson(C04s3 c04s3) {
        Media mediaA0A;
        C05ym c05ym;
        C01yv c01yv = (C01yv) c04s3;
        C05s2.A0R(c01yv);
        C0XvS c0XvS = new C0XvS();
        if (c01yv.A1d() != C01yl.A0D) {
            c01yv.A1f();
            return null;
        }
        while (c01yv.A1N() != C01yl.A09) {
            String strA08 = C01yt.A08(c01yv);
            switch (strA08.hashCode()) {
                case -1169670911:
                    if (!strA08.equals("max_cutout_sticker_limit")) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else {
                        c0XvS.A04 = AnonymousClass0025.A0H(c01yv);
                    }
                    break;
                case -1078031089:
                    if (!strA08.equals("medias")) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else if (c01yv.A1d() == C01yl.A0C) {
                        ArrayList arrayListA0S = C000H.A0S();
                        while (c01yv.A1N() != C01yl.A08) {
                            if (c01yv.A1d() != C01yl.A0G) {
                                AnonymousClass0025.A0N(c01yv, C0ZMV.A00, arrayListA0S);
                            }
                        }
                        c0XvS.A06 = arrayListA0S;
                    }
                    break;
                case -951295677:
                    if (!strA08.equals("cooldown_time_in_seconds")) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else {
                        c0XvS.A05 = AnonymousClass0025.A0H(c01yv);
                    }
                    break;
                case -315996171:
                    if (!strA08.equals("retry_entire_upload_flow")) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else {
                        c0XvS.A03 = AnonymousClass0025.A0D(c01yv);
                    }
                    break;
                case 103772132:
                    if (!strA08.equals("media")) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else if (c01yv.A1d() != C01yl.A0G && (mediaA0A = C05vk.A0A(c01yv)) != null) {
                        c0XvS.A01 = mediaA0A;
                    }
                    break;
                case 106855379:
                    if (!strA08.equals("posts")) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else if (c01yv.A1d() == C01yl.A0C) {
                        ArrayList arrayListA0S2 = C000H.A0S();
                        while (c01yv.A1N() != C01yl.A08) {
                            if (c01yv.A1d() != C01yl.A0G) {
                                AnonymousClass0025.A0N(c01yv, C0ZJE.A00, arrayListA0S2);
                            }
                        }
                        c0XvS.A07 = arrayListA0S2;
                    }
                    break;
                case 950398559:
                    if (!strA08.equals(GraphQLSubscriptionID.INAPP_NOTIFICATION_TYPE_COMMENT)) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else if (c01yv.A1d() != C01yl.A0G && (c05ym = (C05ym) C05wc.A00.parseFromJsonParser(c01yv)) != null) {
                        c0XvS.A00 = c05ym;
                    }
                    break;
                case 1244892812:
                    if (!strA08.equals(AnonymousClass0005.A00(904))) {
                        C01pP.A01(c01yv, c0XvS, strA08);
                    } else {
                        c0XvS.A02 = AnonymousClass0025.A0D(c01yv);
                    }
                    break;
                default:
                    C01pP.A01(c01yv, c0XvS, strA08);
                    break;
            }
            c01yv.A1f();
        }
        return c0XvS;
    }