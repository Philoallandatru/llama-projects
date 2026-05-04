import { AbstractChatProvider, XRequest } from '@ant-design/x-sdk';
import type { XRequestOptions } from '@ant-design/x-sdk';
import type { TransformMessage } from '@ant-design/x-sdk';
import type { ChatMessage, ChatInput, ChatOutput } from '@/lib/types';

/**
 * SSD Quality Platform Chat Provider
 * 处理与后端 FastAPI 的通信和数据转换
 */
export class SSDChatProvider extends AbstractChatProvider<
  ChatMessage,
  ChatInput,
  ChatOutput
> {
  /**
   * 转换请求参数
   * 将前端的请求参数转换为后端 API 需要的格式
   */
  transformParams(
    requestParams: Partial<ChatInput>,
    options: XRequestOptions<ChatInput, ChatOutput, ChatMessage>
  ): any {
    console.log('[ChatProvider] transformParams called:', requestParams, options);
    // 后端期望 snake_case: datasources, 不是 dataSources
    const params = {
      query: requestParams.query || '',
      datasources: requestParams.dataSources || [],
      top_k: 3,
      ...options.params,
    };
    console.log('[ChatProvider] Transformed params:', params);
    return params;
  }

  /**
   * 转换本地消息（用户发送的消息）
   * 用于在 UI 中立即显示用户输入
   */
  transformLocalMessage(requestParams: Partial<ChatInput>): ChatMessage {
    console.log('[ChatProvider] transformLocalMessage called:', requestParams);
    const message = {
      role: 'user',
      content: requestParams.query || '',
      timestamp: Date.now(),
    };
    console.log('[ChatProvider] Local message:', message);
    return message;
  }

  /**
   * 转换响应消息
   * 处理流式响应，累积内容并提取引用
   */
  transformMessage(info: TransformMessage<ChatMessage, ChatOutput>): ChatMessage {
    console.log('[ChatProvider] transformMessage called:', info);
    const { originMessage, chunk, chunks, responseHeaders } = info;

    // 累积内容
    let content = originMessage?.content || '';
    let citations = originMessage?.citations;

    if (chunk) {
      console.log('[ChatProvider] Processing chunk:', chunk);

      // chunk.data 是 JSON 字符串，需要解析
      if (chunk.data) {
        try {
          const parsed = JSON.parse(chunk.data);
          console.log('[ChatProvider] Parsed chunk data:', parsed);

          if (parsed.content) {
            content += parsed.content;
          }

          if (parsed.citations) {
            citations = parsed.citations;
          }
        } catch (e) {
          console.error('[ChatProvider] Failed to parse chunk.data:', e);
        }
      }
    }

    const result = {
      role: 'assistant',
      content,
      citations,
      timestamp: Date.now(),
    };

    console.log('[ChatProvider] Returning message:', result);
    return result;
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
