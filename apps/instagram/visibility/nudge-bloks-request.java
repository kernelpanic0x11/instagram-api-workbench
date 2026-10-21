    public final void A00(C05B6 c05b6, C0MvL c0MvL, C0JQr c0JQr, String str, Map map) {
        if (this.A00) {
            return;
        }
        this.A00 = true;
        C0Ajj c0AjjA04 = C015E.A04(this.A01, str, map);
        c0AjjA04.A00(new C0EJA(0, c0MvL, c05b6, c0JQr, this));
        c05b6.schedule(c0AjjA04);
    }