.method public static constructor <clinit>()V
    .registers 12

    const v3, 0x7f082472

    const v1, 0x7f1336d3

    const/16 v0, 0x3a98

    new-instance v2, LX/0DZs;

    invoke-direct {v2, v0, v3, v1}, LX/0DZs;-><init>(III)V

    const-string v1, "DURATION_15_SEC_IN_MS"

    const/4 v0, 0x0

    new-instance v5, LX/0DZv;

    invoke-direct {v5, v2, v1, v0}, LX/0DZv;-><init>(LX/0DZs;Ljava/lang/String;I)V

    sput-object v5, LX/0DZv;->A03:LX/0DZv;

    const v3, 0x7f082474

    const v1, 0x7f1336d5

    const/16 v0, 0x7530

    new-instance v2, LX/0DZs;

    invoke-direct {v2, v0, v3, v1}, LX/0DZs;-><init>(III)V

    const-string v1, "DURATION_30_SEC_IN_MS"

    const/4 v0, 0x1

    new-instance v6, LX/0DZv;

    invoke-direct {v6, v2, v1, v0}, LX/0DZv;-><init>(LX/0DZs;Ljava/lang/String;I)V

    sput-object v6, LX/0DZv;->A05:LX/0DZv;

    const v3, 0x7f082476

    const v1, 0x7f1336d8

    const v0, 0xea60

    new-instance v2, LX/0DZs;

    invoke-direct {v2, v0, v3, v1}, LX/0DZs;-><init>(III)V

    const-string v1, "DURATION_60_SEC_IN_MS"

    const/4 v0, 0x2

    new-instance v7, LX/0DZv;

    invoke-direct {v7, v2, v1, v0}, LX/0DZv;-><init>(LX/0DZs;Ljava/lang/String;I)V

    sput-object v7, LX/0DZv;->A06:LX/0DZv;

    const v4, 0x7f082477

    const v3, 0x7f082477

    const v1, 0x7f1336d9

    const v0, 0x15f90

    new-instance v2, LX/0DZs;

    invoke-direct {v2, v0, v4, v1}, LX/0DZs;-><init>(III)V

    const-string v1, "DURATION_90_SEC_IN_MS"

    const/4 v0, 0x3

    new-instance v8, LX/0DZv;

    invoke-direct {v8, v2, v1, v0}, LX/0DZv;-><init>(LX/0DZs;Ljava/lang/String;I)V

    sput-object v8, LX/0DZv;->A08:LX/0DZv;

    const v4, 0x7f082475

    const v1, 0x7f1336d6

    const v0, 0x2bf20

    new-instance v2, LX/0DZs;

    invoke-direct {v2, v0, v4, v1}, LX/0DZs;-><init>(III)V

    const-string v1, "DURATION_180_SEC_IN_MS"

    const/4 v0, 0x4

    new-instance v9, LX/0DZv;

    invoke-direct {v9, v2, v1, v0}, LX/0DZv;-><init>(LX/0DZs;Ljava/lang/String;I)V

    sput-object v9, LX/0DZv;->A04:LX/0DZv;

    const v1, 0x7f1336d2

    const v0, 0xdbba0

    new-instance v2, LX/0DZs;

    invoke-direct {v2, v0, v3, v1}, LX/0DZs;-><init>(III)V

    const-string v1, "DURATION_900_SEC_IN_MS"

    const/4 v0, 0x5

    new-instance v10, LX/0DZv;

    invoke-direct {v10, v2, v1, v0}, LX/0DZv;-><init>(LX/0DZs;Ljava/lang/String;I)V

    sput-object v10, LX/0DZv;->A07:LX/0DZv;

    const v1, 0x7f1336d7

    const v0, 0x2255100

    new-instance v2, LX/0DZs;

    invoke-direct {v2, v0, v3, v1}, LX/0DZs;-><init>(III)V

    const-string v1, "UNLIMITED_DURATION"

    const/4 v0, 0x6

    new-instance v11, LX/0DZv;

    invoke-direct {v11, v2, v1, v0}, LX/0DZv;-><init>(LX/0DZs;Ljava/lang/String;I)V

    filled-new-array/range {v5 .. v11}, [LX/0DZv;

    move-result-object v0

    sput-object v0, LX/0DZv;->A02:[LX/0DZv;

    invoke-static {v0}, LX/05r3;->A00([Ljava/lang/Enum;)LX/05r4;

    move-result-object v0

    sput-object v0, LX/0DZv;->A01:Lkotlin/enums/EnumEntries;

    return-void
.end method