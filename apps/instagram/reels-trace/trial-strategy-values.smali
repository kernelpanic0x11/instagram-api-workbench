.method public static constructor <clinit>()V
    .registers 7

    const-string v1, "UNSET_OR_UNRECOGNIZED_ENUM_VALUE"

    const/4 v0, 0x0

    new-instance v6, LX/0TMY;

    invoke-direct {v6, v1, v0, v1}, LX/0TMY;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v6, LX/0TMY;->A05:LX/0TMY;

    const/4 v2, 0x1

    const-string v1, "manual"

    const-string v0, "MANUAL"

    new-instance v5, LX/0TMY;

    invoke-direct {v5, v0, v2, v1}, LX/0TMY;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v5, LX/0TMY;->A03:LX/0TMY;

    const/4 v2, 0x2

    const-string v1, "ss_performance"

    const-string v0, "SS_PERFORMANCE"

    new-instance v4, LX/0TMY;

    invoke-direct {v4, v0, v2, v1}, LX/0TMY;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    sput-object v4, LX/0TMY;->A04:LX/0TMY;

    const/4 v3, 0x3

    const-string v2, "time_limit"

    const-string v1, "TIME_LIMIT"

    new-instance v0, LX/0TMY;

    invoke-direct {v0, v1, v3, v2}, LX/0TMY;-><init>(Ljava/lang/String;ILjava/lang/String;)V

    filled-new-array {v6, v5, v4, v0}, [LX/0TMY;

    move-result-object v0

    sput-object v0, LX/0TMY;->A02:[LX/0TMY;

    invoke-static {v0}, LX/05r3;->A00([Ljava/lang/Enum;)LX/05r4;

    move-result-object v0

    sput-object v0, LX/0TMY;->A01:Lkotlin/enums/EnumEntries;

    return-void
.end method