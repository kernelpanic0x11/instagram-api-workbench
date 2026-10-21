    @Override // X.C0oiC
    public final /* bridge */ /* synthetic */ C0NZz GaG(C04s3 c04s3) throws IOException {
        int i = this.$t;
        if (i != 0 && i == 1) {
            C05s2.A0R(c04s3);
            C05BK c05bk = (C05BK) C0ZMX.A00.parseFromJsonParser(c04s3);
            if (c05bk != null) {
                return c05bk;
            }
            throw AnonymousClass0123.A0a("configure_to_clips returned an unparseable response");
        }
        return C0C3B.A0V(c04s3);
    }