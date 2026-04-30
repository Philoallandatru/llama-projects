import { LlamaIndexServer } from "@llamaindex/server";

new LlamaIndexServer({
  uiConfig: {
    starterQuestions: [
      "分析 issue NVME-777",
      "批量分析 NVME-777, NVME-778, NVME-779",
      "使用严格模式分析 PROJ-123",
    ],
    componentsDir: "components",
    layoutDir: "layout",
    llamaDeploy: {
      deployment: "jira-analysis",
      workflow: "deep-analysis"
    },
  },
}).start();
