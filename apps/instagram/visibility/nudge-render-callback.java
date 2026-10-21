    @Override // X.C0Aji
    public final /* bridge */ /* synthetic */ void A06(Object obj) {
        C05eU c05eUA0K;
        int i = this.$t;
        C057p c057pA0L = C020p.A0L(obj);
        if (i != 0) {
            c05eUA0K = C05eU.A04((Fragment) this.A02, (C0Eto) this.A01, ((C0HNJ) this.A03).A00);
        } else {
            if (this.A01 != null) {
                C03dR.A00().markerPoint(387850546, "bloks_request_succeeded");
            }
            UserSession userSession = ((C05uB) this.A03).A01;
            C05B6 c05b6 = (C05B6) this.A00;
            c05eUA0K = AnonymousClass0220.A0K(c05b6, userSession);
            Object obj2 = this.A02;
            if (obj2 != null) {
                c05eUA0K.A0A(R.id.open_share_sheet_handler, obj2);
            }
            C00ez c00ez = c05b6.mFragmentManager;
            if (C00fA.A00(c00ez) || !C00fA.A01(c00ez)) {
                return;
            }
        }
        C0KYw.A01(c05eUA0K, c057pA0L);
    }