import { LlamaIndexServer } from "@llamaindex/server";

new LlamaIndexServer({
  port: 9876,
  uiConfig: {
    llamaDeploy: { deployment: "chat", workflow: "workflow" },
  },
}).start();
