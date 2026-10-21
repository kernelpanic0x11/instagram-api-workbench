    public static final void A01(C04s3 c04s3, C01y9 c01y9, String str) {
        String strA07;
        String strA08;
        String strA09;
        C06KI c06ki;
        String strA010;
        String strA011;
        String strA012;
        String strA013;
        String strA014;
        String strA015;
        Object fromJsonParser;
        String strA016;
        String strA017;
        String strA018;
        String strA019;
        String strA020;
        String strA021;
        String strA022;
        String strA023;
        String strA024;
        String strA025;
        String strA026;
        C06KH c06kh;
        String strA027;
        String strA028;
        String strA029;
        String strA030;
        String strA031;
        String strA032;
        String strA033;
        switch (str.hashCode()) {
            case -1894952180:
                if (str.equals(AnonymousClass0021.A00(164)) && (strA07 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0K = strA07;
                    break;
                }
                break;
            case -1879119064:
                if (str.equals("enrollment_time") && (strA08 = C01yt.A07(c04s3)) != null) {
                    c01y9.A06 = strA08;
                    break;
                }
                break;
            case -1725459019:
                if (str.equals("feedback_url") && (strA09 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0J = strA09;
                    break;
                }
                break;
            case -1656166225:
                if (str.equals("consent_data") && c04s3.A1d() != C01yl.A0G && (c06ki = (C06KI) C0Kbt.A00.parseFromJsonParser(c04s3)) != null) {
                    c01y9.A01 = c06ki;
                    break;
                }
                break;
            case -1567129552:
                if (str.equals("feedback_action") && (strA010 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0E = strA010;
                    break;
                }
                break;
            case -1509910759:
                if (str.equals("feedback_required")) {
                    c01y9.A0Y = c04s3.A12();
                }
                break;
            case -1057499839:
                if (str.equals("dialogue_type") && (strA011 = C01yt.A07(c04s3)) != null) {
                    c01y9.A05 = strA011;
                    break;
                }
                break;
            case -892481550:
                if (str.equals(IgReactPurchaseExperienceBridgeModule.RN_SHOP_PAY_STATUS) && (strA012 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0N = strA012;
                    break;
                }
                break;
            case -817778335:
                if (str.equals(AnonymousClass0021.A00(29)) && (strA013 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0B = strA013;
                    break;
                }
                break;
            case -587869921:
                if (str.equals("client_facing_error_message") && (strA014 = C01yt.A07(c04s3)) != null) {
                    c01y9.A02(strA014);
                    break;
                }
                break;
            case -483544115:
                if (str.equals("restriction_type") && (strA015 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0S = strA015;
                    break;
                }
                break;
            case -431384026:
                if (str.equals("can_see_notes")) {
                    c01y9.A05(c04s3.A12());
                }
                break;
            case -371576149:
                if (str.equals("_messages") && c04s3.A1d() == C01yl.A0C) {
                    ArrayList arrayList = new ArrayList();
                    while (c04s3.A1N() != C01yl.A08) {
                        if (c04s3.A1d() != C01yl.A0G && (fromJsonParser = C0Kbr.A00.parseFromJsonParser(c04s3)) != null) {
                            arrayList.add(fromJsonParser);
                        }
                    }
                    c01y9.A0V = arrayList;
                    break;
                }
                break;
            case -341385150:
                if (str.equals("can_see_broadcast_chats")) {
                    c01y9.A04(c04s3.A12());
                }
                break;
            case -309921506:
                if (str.equals("feedback_title") && (strA016 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0I = strA016;
                    break;
                }
                break;
            case -181542259:
                if (str.equals("is_epd_error")) {
                    c01y9.A06(c04s3.A12());
                }
                break;
            case 3327275:
                if (str.equals("lock")) {
                    c01y9.A0a = c04s3.A12();
                }
                break;
            case 50511102:
                if (str.equals("category") && (strA017 = C01yt.A07(c04s3)) != null) {
                    c01y9.A02 = strA017;
                    break;
                }
                break;
            case 137235097:
                if (str.equals("logout_reason") && (strA018 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0L = strA018;
                    break;
                }
                break;
            case 357164123:
                if (str.equals("error_reason") && (strA019 = C01yt.A07(c04s3)) != null) {
                    c01y9.A09 = strA019;
                    break;
                }
                break;
            case 395622962:
                if (str.equals("error_source") && (strA020 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0A = strA020;
                    break;
                }
                break;
            case 463939262:
                if (str.equals("feedback_appeal_label") && (strA021 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0F = strA021;
                    break;
                }
                break;
            case 471335075:
                if (str.equals("restriction_detail_use_case") && (strA022 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0Q = strA022;
                    break;
                }
                break;
            case 767170141:
                if (str.equals("expiration_time") && (strA023 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0D = strA023;
                    break;
                }
                break;
            case 780352845:
                if (str.equals("feedback_message") && (strA024 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0H = strA024;
                    break;
                }
                break;
            case 876177880:
                if (str.equals("reasons_thrown") && (strA025 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0O = strA025;
                    break;
                }
                break;
            case 954925063:
                if (str.equals(DialogModule.KEY_MESSAGE)) {
                    c01y9.A01(c04s3);
                }
                break;
            case 1077401445:
                if (str.equals("sentry_block_restriction_dialogue_unification_enabled")) {
                    c01y9.A0c = c04s3.A12();
                }
                break;
            case 1400849976:
                if (str.equals("checkpoint_url") && (strA026 = C01yt.A07(c04s3)) != null) {
                    c01y9.A03 = strA026;
                    break;
                }
                break;
            case 1402633315:
                if (str.equals("challenge") && c04s3.A1d() != C01yl.A0G && (c06kh = (C06KH) C0Kbs.A00.parseFromJsonParser(c04s3)) != null) {
                    c01y9.A00 = c06kh;
                    break;
                }
                break;
            case 1434157220:
                if (str.equals("news_url_is_regulated")) {
                    c01y9.A0b = c04s3.A12();
                }
                break;
            case 1635657081:
                if (str.equals("error_body") && (strA027 = C01yt.A07(c04s3)) != null) {
                    c01y9.A07 = strA027;
                    break;
                }
                break;
            case 1635686852:
                if (str.equals("error_code") && (strA028 = C01yt.A07(c04s3)) != null) {
                    c01y9.A03(strA028);
                    break;
                }
                break;
            case 1636203281:
                if (str.equals("error_type") && (strA029 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0C = strA029;
                    break;
                }
                break;
            case 1715649179:
                if (str.equals("responsible_policy") && (strA030 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0P = strA030;
                    break;
                }
                break;
            case 1928059073:
                if (str.equals("feedback_ignore_label") && (strA031 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0G = strA031;
                    break;
                }
                break;
            case 1990891213:
                if (str.equals(AnonymousClass0000.A00(1690)) && (strA032 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0T = strA032;
                    break;
                }
                break;
            case 2060208332:
                if (str.equals("restriction_extra_data") && (strA033 = C01yt.A07(c04s3)) != null) {
                    c01y9.A0R = strA033;
                    break;
                }
                break;
            case 2082229566:
                if (str.equals("is_spam")) {
                    c01y9.A0d = c04s3.A12();
                }
                break;
        }
    }