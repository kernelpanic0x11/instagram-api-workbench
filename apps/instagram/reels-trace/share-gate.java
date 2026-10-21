    public static final void A0S(C0RCJ c0rcj, String str) {
        String str2;
        MVLinkInfo mVLinkInfo = A05(c0rcj).A08.A09().A0I;
        if (mVLinkInfo != null && (str2 = mVLinkInfo.A02) != null && !C05t8.A10(str2)) {
            C08xi c08xiA03 = C08xf.A03(C020p.A0Q(c0rcj.A0U));
            UserSession userSessionA0Q = C020p.A0Q(c0rcj.A0U);
            C06um c06um = ((C05Fb) c08xiA03).A05;
            C0LBt.A02(userSessionA0Q, new C0CiB(c06um.A09.toString(), "publish_sheet", "publish_media", c06um.A0R), null, "publish_media", "reel", "share", str2, mVLinkInfo.A01, mVLinkInfo.A03, null);
        }
        C0aGN c0aGN = (C0aGN) C01lf.A01(213042);
        UserSession userSessionA0Q2 = C020p.A0Q(c0rcj.A0U);
        C0P35 c0p35 = new C0P35(c0rcj, 10);
        C03oB c03oBA00 = C0FY8.A00(c0rcj);
        Integer numValueOf = c03oBA00 != null ? Integer.valueOf(C0aWQ.A00(C020p.A0Q(c0rcj.A0U), c03oBA00)) : null;
        List list = A00(c0rcj).A14().A1b;
        ArrayList arrayListA0T = C000H.A0T(list);
        Iterator it = list.iterator();
        while (it.hasNext()) {
            arrayListA0T.add(Float.valueOf(C0BQC.A1D(it).A01()));
        }
        Integer numA02 = c0aGN.A02(userSessionA0Q2, numValueOf, arrayListA0T, c0p35);
        if (numA02 == null || C000H.A0s(c0rcj.A0R)) {
            A0Q(c0rcj, str);
            return;
        }
        C0aGN c0aGN2 = (C0aGN) C01lf.A01(213042);
        UserSession userSessionA0Q3 = C020p.A0Q(c0rcj.A0U);
        Context contextRequireContext = c0rcj.requireContext();
        FragmentActivity fragmentActivityRequireActivity = c0rcj.requireActivity();
        View view = c0rcj.mView;
        ViewGroup viewGroup = view instanceof ViewGroup ? (ViewGroup) view : null;
        C0iaQ c0iaQ = new C0iaQ(str, c0rcj, 26);
        C0C6U c0c6u = new C0C6U(c0rcj, 27);
        C0C6U c0c6u2 = new C0C6U(c0rcj, 28);
        C05s2.A0V(userSessionA0Q3, 0);
        int iIntValue = numA02.intValue();
        if (iIntValue == 0) {
            C03dR.A00().markerStart(17635931);
            C0dbo c0dbo = new C0dbo(userSessionA0Q3, c0iaQ, 52);
            C0Dgd c0Dgd = new C0Dgd();
            c0Dgd.A00 = c0dbo;
            C04L6 c04l6A0T = C020p.A0T(userSessionA0Q3);
            c04l6A0T.A0U = c0Dgd;
            C020p.A1X(c04l6A0T, false);
            c04l6A0T.A0V = new C0pcy(3);
            c04l6A0T.A01().A05(contextRequireContext, c0Dgd);
            C0IFz.A00(C0DDx.A1L, C0IFy.VIEW, C0DDy.A0D, null, userSessionA0Q3);
            return;
        }
        if (iIntValue == 1) {
            C03dR.A00().markerStart(17635931);
            C0DMU c0dmu = new C0DMU();
            c0dmu.A00 = new C0JUx(userSessionA0Q3, c0iaQ);
            C04L6 c04l6A0V = AnonymousClass0225.A0V(userSessionA0Q3, false);
            c04l6A0V.A0V = new C0NYv(userSessionA0Q3, 15);
            c04l6A0V.A01().A05(contextRequireContext, c0dmu);
            return;
        }
        if (iIntValue != 2) {
            if (iIntValue != 3) {
                throw AnonymousClass0025.A0L();
            }
            if (fragmentActivityRequireActivity.isFinishing() || fragmentActivityRequireActivity.isDestroyed()) {
                return;
            }
            c0aGN2.A03(contextRequireContext, viewGroup, userSessionA0Q3, "share_button", new C0jfN(userSessionA0Q3, c0c6u2, 29), C0BRF.A0C(c0iaQ, 1250));
            C02gr c02grA0e = C021R.A0e(userSessionA0Q3, 0);
            C0ZgW.A00(c02grA0e, C01F4.A0B(c02grA0e, C0ZgW.A00, C0ZgW.A01, 0) + 1);
            return;
        }
        if (fragmentActivityRequireActivity.isFinishing() || fragmentActivityRequireActivity.isDestroyed()) {
            return;
        }
        C0IIp c0IIpA0U = C020p.A0U(fragmentActivityRequireActivity);
        c0IIpA0U.A0A(2131971896);
        c0IIpA0U.A09(2131971895);
        c0IIpA0U.A0P(new C0afj(c0iaQ, 27), AnonymousClass0009.A0C, 2131982375);
        c0IIpA0U.A0N(new C0afj(c0c6u, 28), AnonymousClass0009.A00, 2131971894);
        AnonymousClass0252.A1O(c0IIpA0U, true);
        C01F4.A1C(C021R.A0e(userSessionA0Q3, 0), C0XnY.A00, C0XnY.A01, 0, true);
    }