    public final Integer A02(UserSession userSession, Integer num, List list, Function0 function0) {
        C0GAZ c0gaz;
        C0Jop c0Jop;
        Boolean boolCuj;
        Integer numCut;
        Integer numCut2;
        C05s2.A0V(userSession, 0);
        C04Sh c04ShA0A = C021R.A0A(userSession, C0K9D.A00);
        boolean zA0o = C000H.A0o(C01ox.A02(userSession, false), 36325828367240773L);
        C02gr c02grA00 = C02gr.A00(userSession);
        if (zA0o) {
            c0gaz = A02;
            c0Jop = A03[1];
        } else {
            c0gaz = A01;
            c0Jop = A03[0];
        }
        boolean zA0n = C000H.A0n(c0gaz.DuR(c02grA00, c0Jop));
        if (!zA0n) {
            C0D9e c0D9e = c04ShA0A.A01;
            if (AnonymousClass0061.A0P(c0D9e) == C02AA.PrivacyStatusPublic && ((numCut2 = c0D9e.Cut(1930610808)) == null || numCut2.intValue() == 0)) {
                return AnonymousClass0009.A00;
            }
        }
        if (zA0o && !zA0n) {
            C0D9e c0D9e2 = c04ShA0A.A01;
            if (AnonymousClass0061.A0P(c0D9e2) == C02AA.PrivacyStatusPublic && (numCut = c0D9e2.Cut(1930610808)) != null && numCut.intValue() > 0) {
                return AnonymousClass0009.A01;
            }
        }
        if (!AnonymousClass0127.A1Y(C021R.A0e(userSession, 0), C0XnY.A00, C0XnY.A01, 0) && C000H.A0l(c04ShA0A.A01, new C0G9g(c04ShA0A, 154), -1474908074) && num != null && num.intValue() > C0DZv.A04.A00.A01) {
            C0G7K c0g7k = C0G7K.A00;
            if (C000H.A0o(C01ox.A02(userSession, false), 36314914855653848L) && !c0g7k.A01(userSession, list)) {
                return AnonymousClass0009.A0C;
            }
        }
        if (!C000H.A0o(C01ox.A02(userSession, false), 36315718014342568L) || !C000H.A0o(C01ox.A02(userSession, false), 36315718016112052L)) {
            return null;
        }
        C01lf.A01(180225);
        C03oe.A01("android_purge_26_q2_TranslationsCreationSettingsHelper_getHasSeenVoiceTranslationsConsentNux");
        C0D9e c0D9eCux = C01F4.A0W(userSession, C0K7D.A00).Cux(-1838505370);
        if (((c0D9eCux == null || (boolCuj = c0D9eCux.Cuj(816461467)) == null) ? AnonymousClass0127.A1Y(C021R.A0e(userSession, 0), C04MF.A01, C04MF.A02, 0) : boolCuj.booleanValue()) || ((C03vO) C01lf.A01(180225)).A05(userSession) || ((C03vO) C01lf.A01(180225)).A06(userSession, AnonymousClass0009.A00) || C01F4.A0B(C021R.A0e(userSession, 0), C0ZgW.A00, C0ZgW.A01, 0) >= 3 || !C000H.A0t(function0)) {
            return null;
        }
        C02gr c02grA0e = C021R.A0e(userSession, 0);
        C0GAZ c0gaz2 = C0ZgL.A00;
        C0Jop[] c0JopArr = C0ZgL.A01;
        int iA0B = C01F4.A0B(c02grA0e, c0gaz2, c0JopArr, 0);
        C02gr c02grA01 = C02gr.A00(userSession);
        if (iA0B == 0) {
            C0ZgL.A00(c02grA01, 3);
            return AnonymousClass0009.A0N;
        }
        C05s2.A0V(c02grA01, 0);
        C0ZgL.A00(c02grA01, C01F4.A0B(c02grA01, c0gaz2, c0JopArr, 0) - 1);
        return null;
    }