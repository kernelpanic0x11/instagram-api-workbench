    /* JADX INFO: Access modifiers changed from: private */
    public final void sendSkywalkerCommand(String str, List list, List list2, C0T22 c0t22) {
        if (this.mqttClient != null) {
            try {
                publish(str, SkywalkerCommand__JsonHelper.instance.serializeToJson(new SkywalkerCommand(list, list2, null)), c0t22, true);
            } catch (IOException e) {
                throw new IllegalStateException("error serializing skywalker command", e);
            }
        }
    }