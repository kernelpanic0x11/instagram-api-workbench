    public final boolean A01(UserSession userSession, List list) {
        C05s2.A0R(userSession);
        C05s2.A0S(list);
        AnonymousClass0397 anonymousClass0397 = new AnonymousClass0397(userSession, 133);
        if (list.isEmpty()) {
            return false;
        }
        if (!(list instanceof Collection) || !list.isEmpty()) {
            Iterator it = list.iterator();
            while (it.hasNext()) {
                float fA01 = AnonymousClass0064.A01(it.next());
                if (Math.abs(fA01) > Float.MAX_VALUE || fA01 <= 1.05f) {
                    return false;
                }
            }
        }
        return C000H.A0n(anonymousClass0397.invoke());
    }