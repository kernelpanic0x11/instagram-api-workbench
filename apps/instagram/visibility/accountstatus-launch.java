/* JADX INFO: renamed from: X.0L1j, reason: invalid class name */
/* JADX INFO: loaded from: classes9.dex */
public final class C0L1j {
    public static final C0RY3 A00(final FragmentActivity fragmentActivity, C0dIe c0dIe, C0Eto c0Eto, final UserSession userSession, String str, String str2) {
        String str3 = userSession.userId;
        String moduleName = c0Eto.getModuleName();
        C05s2.A0R(str3);
        C05s2.A0S(moduleName);
        LinkedHashMap linkedHashMapA00 = C0L5A.A00(C0Guy.A0p, moduleName, str);
        linkedHashMapA00.put("location", AnonymousClass0221.A0r(c0dIe.toString()));
        linkedHashMapA00.put("viewer_id", str3);
        if (str2 != null) {
            linkedHashMapA00.put("enforcement_id", str2);
        }
        Map mapA0A = C01qc.A0A(linkedHashMapA00);
        A01(userSession.userId, C021R.A0x("location", mapA0A), C021R.A0x("trigger_session_id", mapA0A));
        return new C0RY3(fragmentActivity, C0EHY.A00, c0Eto, userSession, null, new C0hkW() { // from class: X.0GhD
            @Override // X.C0hkW
            public final void A01() {
                C03dR.A00().markerPoint(387849633, "network_request_failed");
                FragmentActivity fragmentActivity2 = fragmentActivity;
                if (!fragmentActivity2.isFinishing()) {
                    C0Ir7.A0B(fragmentActivity2, "request_error");
                }
            }

            @Override // X.C0hkW
            public final void A02() {
                C03dR.A00().markerPoint(387849633, AnonymousClass0005.A00(15));
            }

            @Override // X.C0hkW
            public final void A03(Integer num) {
                C03dR.A00().markerPoint(387849633, "network_request_success");
            }
        }, null, AnonymousClass0009.A01, "com.bloks.www.ig.ixt.triggers.screen.ig_account_status", null, mapA0A);
    }