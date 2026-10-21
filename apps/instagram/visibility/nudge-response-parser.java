    @Override // X.C05Bj
    public final /* bridge */ /* synthetic */ Object unsafeParseFromJson(C04s3 c04s3) {
        Boolean boolA0c = null;
        if (C05Bj.A3r(c04s3) != C01yl.A0D) {
            c04s3.A1f();
            return null;
        }
        C01y9 c01y9A0M = C0C56.A0M();
        while (c04s3.A1N() != C01yl.A09) {
            boolA0c = C0C9W.A0c(c04s3, c01y9A0M, boolA0c, "show_recommendation_status_nudge");
            c04s3.A1f();
        }
        if (boolA0c == null) {
            C01yt.A0H("show_recommendation_status_nudge", "RecommendationStatusNudgeResponseImpl");
            throw AnonymousClass0002.createAndThrow();
        }
        boolean zBooleanValue = boolA0c.booleanValue();
        C0asV c0asV = new C0asV("XDTRecommendationStatusNudgeResponse");
        c0asV.A00 = zBooleanValue;
        C0C9W.A1R(c01y9A0M, c0asV);
        C05Bj.A3v(c0asV, c01y9A0M, c01y9A0M.A09);
        C05Bj.A3t(c01y9A0M, c0asV);
        return c0asV;
    }