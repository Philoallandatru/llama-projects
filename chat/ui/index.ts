import { LlamaIndexServer } from "@llamaindex/server";

new LlamaIndexServer({
  port: 9876,
  uiConfig: {
    componentsDir: "components",
    layoutDir: "layout",
    llamaDeploy: { deployment: "chat", workflow: "workflow" },
  },
}).start();
