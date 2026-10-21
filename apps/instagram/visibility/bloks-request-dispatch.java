    public static final C0Ajj A02(C015E c015e, C01qh c01qh, String str, String str2, Map map, int i, long j, boolean z) {
        if (!c015e.A0A(c01qh, str)) {
            return new C0Sv3(c015e.A06(c01qh, null, str, str2, "bloks/apps/", map, C02bn.A00, i, j, z));
        }
        C00Nq c00NqA02 = GraphQlCallInput.A02.A02();
        C00Nq.A00(c00NqA02, str, "app_id");
        C00Nq.A00(c00NqA02, "8f0f09df419d7d5826957c3f070997a65b6e8d025c84d1e91931768e8b59625e", "bloks_versioning_id");
        C06ls c06ls = new C06ls();
        c06ls.A0F(AnonymousClass0367.A02(0, 9, 104), C05Ee.A02.A03(C05Bb.A00()));
        c00NqA02.A0F(c06ls.A03(), "infra_params");
        if (map != null) {
            C07py c07py = C07px.A03;
            C07qc c07qc = c07py.A02;
            C06tV c06tVA02 = C06tT.A02(String.class);
            Integer num = AnonymousClass0009.A00;
            C00Nq.A00(c00NqA02, c07py.A02(map, C06tX.A03(C06tT.A04(new C06tW(num, c06tVA02), new C06tW(num, C06tT.A01(String.class))), c07qc)), "params");
        }
        C06lq c06lq = new C06lq();
        C06lq c06lq2 = new C06lq();
        C06ls c06ls2 = c06lq.A00;
        c06ls2.A03().A0F(c00NqA02, "params");
        c06lq.A00(C015F.A00(), "bk_context");
        return new C06O8((C0oft) C03fn.A03(c01qh, 131433), C06nw.A00(C04oc.A00("itas-android"), null, "IGBloksAppRootQuery", null, "bloks_app", new ArrayList(), c06ls2.A04(), c06lq2.A00.A04(), C06O0.A00, 0, false).setMaxToleratedCacheAgeMs(j).setRequestPurpose(i == 3 ? 1 : 2).setFriendlyName(AnonymousClass0003.A0P("IGBloksAppRootQuery-", str)), new C02O0(C00L3.A01));
    }