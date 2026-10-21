/* JADX INFO: loaded from: classes9.dex */
public final class AccountStatusUrlHandlerActivity extends UserSessionUrlHandlerActivity implements C0Eto {
    @Override // com.instagram.urlhandler.UserSessionUrlHandlerActivity
    public final void A2V(Bundle bundle, Bundle bundle2, UserSession userSession) {
        String strA0m = AnonymousClass0225.A0m(bundle2, userSession);
        if (strA0m == null) {
            finish();
            return;
        }
        String queryParameter = C021X.A05(strA0m).getQueryParameter("location");
        C01lf.A01(131674);
        C0dIe c0dIe = (C0dIe) C021X.A0e(queryParameter, C0dIe.A8D);
        C05s2.A0K(c0dIe);
        AnonymousClass0227.A1P(AnonymousClass0220.A0H(null, C0L1j.A00(this, c0dIe, this, userSession, null, null).A03(), this, userSession));
    }