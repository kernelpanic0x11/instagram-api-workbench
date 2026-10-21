    private final C02sG A06(C01qh c01qh, C02sD c02sD, String str, String str2, String str3, Map map, Map map2, int i, long j, boolean z) {
        String string;
        boolean z2 = i == 3;
        String strA0a = AnonymousClass0003.A0a(str3, str, "/");
        C06q3 c06q3A07 = C02rm.A01.A07(z ? C0cbg.A00 : C0SuU.A00, null, c01qh, -2);
        c06q3A07.AQE("bloks_versioning_id", "8f0f09df419d7d5826957c3f070997a65b6e8d025c84d1e91931768e8b59625e");
        ArrayList arrayListA01 = C014Z.A01(new C0DRa(17));
        try {
            StringWriter stringWriter = new StringWriter();
            C04s2 c04s2A01 = C01xe.A00.A01(stringWriter);
            C05J6.A00(c04s2A01, arrayListA01);
            c04s2A01.close();
            string = stringWriter.toString();
            C05s2.A0C(string);
        } catch (IOException unused) {
            string = "";
        }
        c06q3A07.AQE("bk_client_context", string);
        c06q3A07.A06 = z2 ? C03ar.OffScreen : C03ar.OnScreen;
        c06q3A07.A07 = C02mu.API;
        if (z2) {
            c06q3A07.A04();
        }
        c06q3A07.A07(AnonymousClass0009.A01);
        c06q3A07.A0A(strA0a);
        if (c02sD != null) {
            ((C04x5) c06q3A07).A00 = c02sD;
        }
        boolean z3 = j >= TimeUnit.DAYS.toMillis(1L);
        if ((c01qh instanceof UserSession) && str2 != null && z3) {
            c06q3A07.A0C = str2;
            c06q3A07.A09 = AnonymousClass0009.A0N;
            ((C04x6) c06q3A07).A01 = j;
        }
        if (map != null) {
            for (Map.Entry entry : map.entrySet()) {
                c06q3A07.AQE((String) entry.getKey(), (String) entry.getValue());
            }
        }
        C015E c015e = A04;
        if (c015e.A0B(str)) {
            ((C04x6) c06q3A07).A03 = null;
            c06q3A07.A0O = true;
        }
        if (c015e.A0C(str)) {
            ((C04x6) c06q3A07).A04 = null;
            c06q3A07.A0P = true;
        }
        c06q3A07.AOz("X-IG-BLOKS-SERIALIZE-PAYLOAD", "true");
        for (Map.Entry entry2 : map2.entrySet()) {
            c06q3A07.AOz((String) entry2.getKey(), (String) entry2.getValue());
        }
        return c06q3A07.A0K();
    }