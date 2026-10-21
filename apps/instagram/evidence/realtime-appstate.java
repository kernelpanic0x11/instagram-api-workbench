    /* JADX INFO: Access modifiers changed from: private */
    public final void updateAppStateInternal(final boolean z) {
        if (this.mqttClient != null) {
            C01me.A00().BES(new C01mp() { // from class: com.instagram.realtimeclient.RealtimeClientManager.updateAppStateInternal.1
                /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
                {
                    super(2096100312, 2, false, true);
                }

                @Override // java.lang.Runnable
                public void run() {
                    RealtimeClientManager realtimeClientManager = RealtimeClientManager.this;
                    Companion companion = RealtimeClientManager.Companion;
                    C0yb6 c0yb6 = realtimeClientManager.mqttClient;
                    if (c0yb6 != null) {
                        c0yb6.HlT(z, !C06sx.A02(realtimeClientManager.userSession));
                    }
                }
            });
        }
    }