    /* JADX INFO: Access modifiers changed from: private */
    public final void sendRealtimeSubscription(String str, List list, List list2, C0T22 c0t22) {
        ArrayList arrayList;
        ArrayList arrayList2 = null;
        if (list == null || list.isEmpty()) {
            arrayList = null;
        } else {
            HashSet hashSet = new HashSet();
            Iterator it = list.iterator();
            while (it.hasNext()) {
                hashSet.add(((RealtimeSubscription) it.next()).getSubscriptionString(this.realtimeClientConfig.getMqttAnalyticsLoggingEnabled(), false));
            }
            arrayList = new ArrayList(hashSet);
        }
        if (list2 != null && !list2.isEmpty()) {
            HashSet hashSet2 = new HashSet();
            Iterator it2 = list2.iterator();
            while (it2.hasNext()) {
                hashSet2.add(((RealtimeSubscription) it2.next()).getSubscriptionString(this.realtimeClientConfig.getMqttAnalyticsLoggingEnabled(), false));
            }
            arrayList2 = new ArrayList(hashSet2);
        }
        sendSkywalkerCommand(str, arrayList, arrayList2, c0t22);
    }