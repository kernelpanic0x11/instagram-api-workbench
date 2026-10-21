/* JADX INFO: renamed from: X.0LEI, reason: invalid class name */
/* JADX INFO: loaded from: classes9.dex */
public abstract class C0LEI {
    public static final Bundle A00(IgBloksScreenConfig igBloksScreenConfig, C0LFI c0lfi) {
        C01qh c01qh = igBloksScreenConfig.A0B;
        C05s2.A0T(c01qh);
        boolean zA0o = C000H.A0o(C01ox.A02(c01qh, false), 36314189005917703L);
        Bundle bundleA04 = C020p.A04();
        Map map = c0lfi.A07;
        Map map2 = c0lfi.A0B;
        int i = c0lfi.A00;
        List list = c0lfi.A09;
        String str = c0lfi.A05;
        String str2 = c0lfi.A06;
        C0Amq c0Amq = c0lfi.A03;
        C0TOw.A02(bundleA04, new C0TOw(c0lfi.A02, null, null, c0Amq, null, c0lfi.A08, str, str2, (HashMap) map, list, c0lfi.A0A, map2, map2, -1, i, -1L, -1L, false, false), zA0o);
        IgBloksScreenConfig.A03(bundleA04, igBloksScreenConfig);
        C01qh c01qh2 = igBloksScreenConfig.A0B;
        C05s2.A0T(c01qh2);
        C020p.A1B(bundleA04, c01qh2.getToken());
        return bundleA04;
    }