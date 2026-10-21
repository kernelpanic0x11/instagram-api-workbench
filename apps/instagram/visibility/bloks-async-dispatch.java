    public static final C0Ajj A03(C01qh c01qh, C02sD c02sD, String str, Map map) {
        String str2;
        C05s2.A0V(c01qh, 0);
        C05s2.A0V(str, 1);
        C015E c015e = A04;
        Map mapA00 = (((MobileConfigUnsafeContext) C01ox.A00()).BZS(C02ft.A06, 18321080649282308L) || !(c01qh instanceof C02pa) || map == null || (str2 = (String) map.get("params")) == null || !C05t8.A19(str2, "maa_request_headers", false)) ? C02bn.A00 : C0Hek.A00(C0Hek.A01(str2));
        if (!c015e.A0A(c01qh, str)) {
            return str.startsWith("com.bloks.www") ? new C0bjC(c015e.A06(c01qh, c02sD, str, null, "bloks/async_action/", map, mapA00, 0, 0L, false)) : new C0Sv3(c015e.A06(c01qh, c02sD, str, null, "bloks/apps/", map, mapA00, 0, 0L, false));
        }
        C05VC c05vcA00 = c015e.A00(str, map, mapA00);
        C0oft c0oft = (C0oft) C03fn.A03(c01qh, 131433);
        C02O0 c02o0 = new C02O0(C00L3.A01);
        C012I c012iA00 = C00J8.A00(C034g.A00(c01qh));
        C05s2.A0C(c012iA00);
        return new C034J(c0oft, c05vcA00, c02o0, c012iA00);
    }