// [jadx java-decompile failed → smali]
// target: X.0RCJ.A0Q
// markers: Code decompiled incorrectly, please refer to instructions dump
// (Java body was an anti-decompile stub; showing smali. Pass smali_fallback=false for the partial Java.)

.method public static final A0Q(LX/0RCJ;Ljava/lang/String;)V
    .registers 26

    move-object/from16 v4, p0

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v0

    const/4 v2, 0x0

    invoke-static {v0, v2}, LX/000H;->A0C(LX/05Dd;Z)LX/0yb5;

    move-result-object v3

    const-wide v0, 0x8110ad00055a4dL

    invoke-static {v3, v0, v1}, LX/000H;->A0o(Ljava/lang/Object;J)Z

    move-result v0

    const/4 v1, 0x1

    if-eqz v0, :cond_4f

    invoke-static {v4}, LX/0RCJ;->A05(LX/0RCJ;)LX/0SxB;

    move-result-object v0

    iget-object v0, v0, LX/0SxB;->A0T:LX/0Rwp;

    iget-object v5, v0, LX/0Rwp;->A03:LX/03oB;

    if-eqz v5, :cond_4c

    iget-object v3, v5, LX/03oB;->A4k:Ljava/lang/String;

    if-eqz v3, :cond_4c

    invoke-virtual {v3}, Ljava/lang/String;->length()I

    move-result v0

    if-eqz v0, :cond_4c

    invoke-static {v3}, LX/0127;->A1Z(Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :cond_4c

    iget-boolean v0, v5, LX/03oB;->A6a:Z

    if-eqz v0, :cond_49

    sget-object v0, LX/0009;->A01:Ljava/lang/Integer;

    :goto_39
    invoke-virtual {v0}, Ljava/lang/Number;->intValue()I

    move-result v3

    if-eq v3, v1, :cond_1f0

    if-eqz v3, :cond_4f

    const/4 v0, 0x2

    if-eq v3, v0, :cond_1f0

    invoke-static {}, LX/0025;->A0L()Lkotlin/NoWhenBranchMatchedException;

    move-result-object v0

    throw v0

    :cond_49
    sget-object v0, LX/0009;->A0C:Ljava/lang/Integer;

    goto :goto_39

    :cond_4c
    sget-object v0, LX/0009;->A00:Ljava/lang/Integer;

    goto :goto_39

    :cond_4f
    invoke-static {v4}, LX/0FY8;->A00(LX/0RCJ;)LX/03oB;

    move-result-object v2

    if-eqz v2, :cond_d9

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v0

    invoke-static {v0, v2}, LX/0aWQ;->A00(Lcom/instagram/common/session/UserSession;LX/03oB;)I

    move-result v6

    :goto_5f
    const/16 v7, 0x15

    new-instance v8, LX/0J8c;

    move-object/from16 v0, p1

    invoke-direct {v8, v4, v0, v6, v7}, LX/0J8c;-><init>(Ljava/lang/Object;Ljava/lang/String;II)V

    sget-object v9, LX/0DZs;->A03:LX/0DZu;

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v0

    invoke-virtual {v9, v0}, LX/0DZu;->A00(Lcom/instagram/common/session/UserSession;)LX/0DZs;

    move-result-object v0

    iget v0, v0, LX/0DZs;->A01:I

    invoke-static {v6, v0}, LX/0127;->A1R(II)Z

    move-result v10

    sget-object v5, LX/0G7K;->A00:LX/0G7K;

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v0

    invoke-static {v0}, LX/0G7K;->A00(Lcom/instagram/common/session/UserSession;)J

    move-result-wide v2

    long-to-int v0, v2

    mul-int/lit16 v0, v0, 0x3e8

    if-le v6, v0, :cond_d7

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v0

    invoke-static {v0}, LX/000H;->A0B(LX/05Dd;)LX/0yb5;

    move-result-object v0

    const-wide v2, 0x81099600043606L

    invoke-static {v0, v2, v3}, LX/000H;->A0o(Ljava/lang/Object;J)Z

    move-result v0

    if-eqz v0, :cond_d7

    :goto_a0
    if-nez v10, :cond_a4

    if-eqz v1, :cond_237

    :cond_a4
    invoke-virtual {v4}, LX/0RCJ;->A0a()Lcom/instagram/common/session/UserSession;

    if-nez v10, :cond_e1

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v6

    invoke-static {v4}, LX/0RCJ;->A00(LX/0RCJ;)Lcom/instagram/creation/capture/quickcapture/sundial/viewmodel/drafts/ClipsSharingDraftViewModel;

    move-result-object v0

    invoke-virtual {v0}, Lcom/instagram/creation/capture/quickcapture/sundial/viewmodel/drafts/ClipsSharingDraftViewModel;->A14()LX/0CcK;

    move-result-object v0

    iget-object v0, v0, LX/0CcK;->A1b:Ljava/util/List;

    invoke-static {v0}, LX/000H;->A0T(Ljava/lang/Iterable;)Ljava/util/ArrayList;

    move-result-object v3

    invoke-interface {v0}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object v2

    :goto_c1
    invoke-interface {v2}, Ljava/util/Iterator;->hasNext()Z

    move-result v0

    if-eqz v0, :cond_db

    invoke-static {v2}, LX/0BQC;->A1D(Ljava/util/Iterator;)LX/06Vq;

    move-result-object v0

    invoke-virtual {v0}, LX/06Vq;->A01()F

    move-result v0

    invoke-static {v0}, Ljava/lang/Float;->valueOf(F)Ljava/lang/Float;

    move-result-object v0

    invoke-virtual {v3, v0}, Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z

    goto :goto_c1

    :cond_d7
    const/4 v1, 0x0

    goto :goto_a0

    :cond_d9
    const/4 v6, 0x0

    goto :goto_5f

    :cond_db
    invoke-virtual {v5, v6, v3}, LX/0G7K;->A01(Lcom/instagram/common/session/UserSession;Ljava/util/List;)Z

    move-result v0

    if-nez v0, :cond_237

    :cond_e1
    const/16 v6, 0x17

    new-instance v5, LX/0C6U;

    invoke-direct {v5, v4, v6}, LX/0C6U;-><init>(Ljava/lang/Object;I)V

    if-eqz v10, :cond_180

    invoke-virtual {v4}, Landroidx/fragment/app/Fragment;->requireContext()Landroid/content/Context;

    move-result-object v8

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v4

    const/4 v6, 0x1

    invoke-static {v4}, LX/05s2;->A0J(Ljava/lang/Object;)V

    const v1, 0x7f136207

    invoke-virtual {v9, v4}, LX/0DZu;->A00(Lcom/instagram/common/session/UserSession;)LX/0DZs;

    move-result-object v0

    iget v0, v0, LX/0DZs;->A01:I

    const v3, 0xea60

    div-int/2addr v0, v3

    invoke-static {v8, v0, v1}, LX/0252;->A0n(Landroid/content/Context;II)Ljava/lang/String;

    move-result-object v2

    const v1, 0x7f136204

    invoke-virtual {v9, v4}, LX/0DZu;->A00(Lcom/instagram/common/session/UserSession;)LX/0DZs;

    move-result-object v0

    iget v0, v0, LX/0DZs;->A01:I

    div-int/2addr v0, v3

    invoke-static {v8, v0, v1}, LX/0252;->A0n(Landroid/content/Context;II)Ljava/lang/String;

    move-result-object v0

    invoke-static {v8}, LX/020p;->A0V(Landroid/content/Context;)LX/0IIp;

    move-result-object v3

    iput-object v2, v3, LX/0IIp;->A03:Ljava/lang/String;

    invoke-virtual {v3, v0}, LX/0IIp;->A0m(Ljava/lang/CharSequence;)V

    const v2, 0x7f136206

    new-instance v1, LX/0afq;

    invoke-direct {v1, v4, v5, v7}, LX/0afq;-><init>(Lcom/instagram/common/session/UserSession;Lkotlin/jvm/functions/Function0;I)V

    sget-object v0, LX/0009;->A0C:Ljava/lang/Integer;

    invoke-virtual {v3, v1, v0, v2}, LX/0IIp;->A0P(Landroid/content/DialogInterface$OnClickListener;Ljava/lang/Integer;I)V

    invoke-virtual {v3, v6}, LX/0IIp;->A0o(Z)V

    invoke-virtual {v3, v6}, LX/0IIp;->A0p(Z)V

    const/16 v1, 0xd

    new-instance v0, LX/0adL;

    invoke-direct {v0, v4, v1}, LX/0adL;-><init>(Ljava/lang/Object;I)V

    invoke-virtual {v3, v0}, LX/0IIp;->A0B(Landroid/content/DialogInterface$OnCancelListener;)V

    const v2, 0x7f136205

    const/16 v1, 0x1f

    new-instance v0, LX/0afj;

    invoke-direct {v0, v4, v1}, LX/0afj;-><init>(Ljava/lang/Object;I)V

    invoke-virtual {v3, v0, v2}, LX/0IIp;->A0E(Landroid/content/DialogInterface$OnClickListener;I)V

    invoke-static {v3}, LX/021X;->A1Q(LX/0IIp;)V

    invoke-static {v4}, LX/08xf;->A03(Lcom/instagram/common/session/UserSession;)LX/08xi;

    move-result-object v0

    iget-object v3, v0, LX/08xi;->A0S:LX/08zc;

    iget-object v1, v3, LX/05Fb;->A01:LX/02di;

    const-string v0, "ig_camera_share_sheet_entity_impression"

    invoke-virtual {v1, v0}, LX/02di;->AMz(Ljava/lang/String;)LX/00ws;

    move-result-object v2

    invoke-interface {v2}, LX/00ws;->isSampled()Z

    move-result v0

    if-eqz v0, :cond_236

    const/16 v1, 0x3b

    :goto_163
    const-string v0, "entity_type"

    invoke-static {v2, v0, v1}, LX/021X;->A1G(LX/00ws;Ljava/lang/String;I)V

    iget-object v0, v3, LX/05Fa;->A00:LX/0Eto;

    invoke-static {v2, v0}, LX/0562;->A1D(LX/00ws;LX/0Eto;)V

    sget-object v1, LX/043C;->A0Z:LX/043C;

    const-string v0, "surface"

    invoke-interface {v2, v1, v0}, LX/00ws;->AOZ(LX/00wp;Ljava/lang/String;)V

    iget-object v0, v3, LX/05Fb;->A05:LX/06um;

    invoke-static {v2, v0}, LX/0BTI;->A10(LX/00ws;LX/06um;)V

    invoke-static {v2}, LX/0562;->A18(LX/00ws;)V

    invoke-interface {v2}, LX/00ws;->Ei8()V

    return-void

    :cond_180
    if-eqz v1, :cond_236

    invoke-virtual {v4}, Landroidx/fragment/app/Fragment;->requireContext()Landroid/content/Context;

    move-result-object v9

    iget-object v0, v4, LX/0RCJ;->A0U:LX/0Jzl;

    invoke-static {v0}, LX/020p;->A0Q(LX/0Jzl;)Lcom/instagram/common/session/UserSession;

    move-result-object v4

    const/4 v7, 0x1

    invoke-static {v4}, LX/05s2;->A0K(Ljava/lang/Object;)V

    const v3, 0x7f136208

    invoke-static {v4}, LX/0G7K;->A00(Lcom/instagram/common/session/UserSession;)J

    move-result-wide v1

    long-to-int v0, v1

    div-int/lit8 v0, v0, 0x3c

    invoke-static {v9, v0, v3}, LX/0252;->A0n(Landroid/content/Context;II)Ljava/lang/String;

    move-result-object v1

    invoke-static {v9}, LX/020p;->A0V(Landroid/content/Context;)LX/0IIp;

    move-result-object v3

    const v0, 0x7f13620b

    invoke-virtual {v3, v0}, LX/0IIp;->A0A(I)V

    invoke-virtual {v3, v1}, LX/0IIp;->A0m(Ljava/lang/CharSequence;)V

    const v2, 0x7f13620a

    const/16 v0, 0x16

    new-instance v1, LX/0afq;

    invoke-direct {v1, v4, v8, v0}, LX/0afq;-><init>(Lcom/instagram/common/session/UserSession;Lkotlin/jvm/functions/Function0;I)V

    sget-object v0, LX/0009;->A0C:Ljava/lang/Integer;

    invoke-virtual {v3, v1, v0, v2}, LX/0IIp;->A0P(Landroid/content/DialogInterface$OnClickListener;Ljava/lang/Integer;I)V

    invoke-virtual {v3, v7}, LX/0IIp;->A0o(Z)V

    invoke-virtual {v3, v7}, LX/0IIp;->A0p(Z)V

    const/16 v1, 0xe

    new-instance v0, LX/0adL;

    invoke-direct {v0, v4, v1}, LX/0adL;-><init>(Ljava/lang/Object;I)V

    invoke-virtual {v3, v0}, LX/0IIp;->A0B(Landroid/content/DialogInterface$OnCancelListener;)V

    const v1, 0x7f136209

    new-instance v0, LX/0afq;

    invoke-direct {v0, v4, v5, v6}, LX/0afq;-><init>(Lcom/instagram/common/session/UserSession;Lkotlin/jvm/functions/Function0;I)V

    invoke-virtual {v3, v0, v1}, LX/0IIp;->A0E(Landroid/content/DialogInterface$OnClickListener;I)V

    invoke-static {v3}, LX/021X;->A1Q(LX/0IIp;)V

    invoke-static {v4}, LX/08xf;->A03(Lcom/instagram/common/session/UserSession;)LX/08xi;

    move-result-object v0

    iget-object v3, v0, LX/08xi;->A0S:LX/08zc;

    iget-object v1, v3, LX/05Fb;->A01:LX/02di;

    const-string v0, "ig_camera_share_sheet_entity_impression"

    invoke-virtual {v1, v0}, LX/02di;->AMz(Ljava/lang/String;)LX/00ws;

    move-result-object v2

    invoke-interface {v2}, LX/00ws;->isSampled()Z

    move-result v0

    if-eqz v0, :cond_236

    const/16 v1, 0x3c

    goto/16 :goto_163

    :cond_1f0
    invoke-virtual {v4}, Landroidx/fragment/app/Fragment;->requireContext()Landroid/content/Context;

    move-result-object v5

    const/4 v6, 0x0

    const v0, 0x7f13177b

    invoke-virtual {v5, v0}, Landroid/content/Context;->getString(I)Ljava/lang/String;

    move-result-object v18

    const v0, 0x7f13177a

    invoke-virtual {v5, v0}, Landroid/content/Context;->getString(I)Ljava/lang/String;

    move-result-object v14

    const v0, 0x7f131778

    invoke-virtual {v5, v0}, Landroid/content/Context;->getString(I)Ljava/lang/String;

    move-result-object v19

    new-instance v7, LX/0afj;

    invoke-direct {v7, v4, v2}, LX/0afj;-><init>(Ljava/lang/Object;I)V

    const v0, 0x7f131779

    invoke-virtual {v5, v0}, Landroid/content/Context;->getString(I)Ljava/lang/String;

    move-result-object v21

    sget-object v9, LX/0afO;->A00:LX/0afO;

    new-instance v4, LX/0IJL;

    move-object v8, v6

    move-object v10, v6

    move-object v11, v6

    move-object v12, v6

    move-object v13, v6

    move-object v15, v6

    move-object/from16 v16, v6

    move-object/from16 v17, v6

    move-object/from16 v20, v6

    move-object/from16 v22, v6

    move/from16 v23, v1

    move/from16 p0, v2

    move/from16 p1, v2

    invoke-direct/range {v4 .. v25}, LX/0IJL;-><init>(Landroid/content/Context;Landroid/content/DialogInterface$OnCancelListener;Landroid/content/DialogInterface$OnClickListener;Landroid/content/DialogInterface$OnClickListener;Landroid/content/DialogInterface$OnClickListener;Landroid/content/DialogInterface$OnClickListener;Landroid/content/DialogInterface$OnDismissListener;Landroid/content/DialogInterface$OnShowListener;Lcom/google/common/collect/ImmutableList;Ljava/lang/CharSequence;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;[Ljava/lang/CharSequence;ZZZ)V

    iget-object v0, v4, LX/0IJL;->A02:LX/0IJM;

    invoke-static {v0}, LX/0IJN;->A00(Landroid/app/Dialog;)V

    :cond_236
    return-void

    :cond_237
    invoke-virtual {v8}, LX/0J8c;->invoke()Ljava/lang/Object;

    return-void
.end method