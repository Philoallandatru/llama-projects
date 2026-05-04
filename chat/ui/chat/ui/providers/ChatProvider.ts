import { AbstractChatProvider, XRequest } from '@ant-design/x-sdk';
import type { XRequestOptions } from '@ant-design/x-sdk';
import type { TransformMessage } from '@ant-design/x-sdk';
import type { ChatMessage, ChatInput, ChatOutput } from '@/lib/types';

const DEFAULT_TOP_K = 3;

/**
 * 解析 SSE chunk 数据
 */
function parseSSEChunk(chunk: any): { content?: string; citations?: any[] } {
  if (!chunk?.data) {
    return {};
  }

  try {
    return JSON.parse(chunk.data);
  } catch (e) {
    console.error('[ChatProvider] Failed to parse SSE chunk:', e);
    return {};
  }
}

/**
 * SSD Quality Platform Chat Provider
 * 处理与后端 FastAPI 的通信和数据转换
 */
export class SSDChatProvider extends AbstractChatProvider<
  ChatMessage,
  ChatInput,
  ChatOutput
> {
  transformParams(
    requestParams: Partial<ChatInput>,
    options: XRequestOptions<ChatInput, ChatOutput, ChatMessage>
  ): any {
    return {
      ...options.params,
      query: requestParams.query || '',
      datasources: requestParams.dataSources || [],
      top_k: DEFAULT_TOP_K,
    };
  }

  transformLocalMessage(requestParams: Partial<ChatInput>): ChatMessage {
    return {
      role: 'user',
      content: requestParams.query || '',
      timestamp: Date.now(),
    };
  }

  transformMessage(info: TransformMessage<ChatMessage, ChatOutput>): ChatMessage {
    const { originMessage, chunk } = info;

    let content = originMessage?.content || '';
    let citations = originMessage?.citations;

    if (chunk) {
      const parsed = parseSSEChunk(chunk);

      if (parsed.content) {
        content += parsed.content;
      }

      if (parsed.citations) {
        citations = parsed.citations;
      }
    }

    return {
      role: 'assistant',
      content,
      citations,
      timestamp: Date.now(),
    };
  }
}

/**
 * 创建 Chat Provider 实例
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const chatProvider = new SSDChatProvider({
  request: XRequest(`${API_BASE}/query/stream`, {
    manual: true,
    timeout: 300000, // 5 分钟超时（本地 LLM 较慢）
    streamTimeout: 60000, // 流式超时 1 分钟
  }),
});
