import { create } from 'zustand';
import type { Conversation, Message } from '@/types';
import { conversations as conversationsApi, chat as chatApi } from '@/api/client';

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  isLoading: boolean;
  streamBuffer: string;
  statusMessage: string | null;
  error: string | null;
}

interface ChatActions {
  sendMessage: (query: string) => Promise<void>;
  regenerate: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  clearConversation: () => Promise<void>;
  fetchConversations: () => Promise<void>;
}

type ChatStore = ChatState & ChatActions;

export const useChatStore = create<ChatStore>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  isLoading: false,
  streamBuffer: '',
  statusMessage: null,
  error: null,

  fetchConversations: async () => {
    set({ error: null, isLoading: true });
    try {
      const res = await conversationsApi.list();
      set({ conversations: res.conversations, isLoading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load conversations';
      set({ error: message, isLoading: false });
    }
  },

  selectConversation: async (id: string) => {
    set({ activeConversationId: id, error: null, isLoading: true });
    try {
      const res = await conversationsApi.messages(id);
      set({ messages: res.messages, isLoading: false });
    } catch {
      set({ error: 'Failed to load messages', isLoading: false });
    }
  },

  sendMessage: async (query: string) => {
    const { activeConversationId } = get();

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConversationId ?? '',
      role: 'user',
      content: query,
      citations: null,
      token_count: null,
      generation_ms: null,
      created_at: new Date().toISOString(),
    };

    set((s) => ({
      messages: [...s.messages, userMessage],
      isStreaming: true,
      streamBuffer: '',
      statusMessage: 'Thinking...',
      error: null,
    }));

    try {
      const convId = activeConversationId ?? (await conversationsApi.create()).id;
      if (!activeConversationId) {
        set({ activeConversationId: convId });
        await get().fetchConversations();
      }

      let assistantMessageId = '';
      let assistantMessageCreatedAt = new Date().toISOString();
      let textBuffer = '';
      let citationsList: any[] | null = null;
      let tokenCount: number | null = null;
      let genMs: number | null = null;

      // Add a temporary assistant message to the state while streaming
      const assistantMessageTempId = `temp-assistant-${Date.now()}`;
      set((s) => ({
        messages: [
          ...s.messages,
          {
            id: assistantMessageTempId,
            conversation_id: convId,
            role: 'assistant',
            content: '',
            citations: null,
            token_count: null,
            generation_ms: null,
            created_at: new Date().toISOString(),
          },
        ],
      }));

      await chatApi.sendStream(
        {
          conversation_id: convId,
          query,
        },
        (event, data) => {
          if (event === 'status') {
            if (data.status === 'searching') {
              set({ statusMessage: `Searching... (${data.documents} docs)` });
            } else if (data.status === 'generating') {
              set({ statusMessage: null });
            }
          } else if (event === 'token') {
            textBuffer += data.token;
            set((s) => ({
              streamBuffer: textBuffer,
              messages: s.messages.map((m) =>
                m.id === assistantMessageTempId ? { ...m, content: textBuffer } : m
              ),
            }));
          } else if (event === 'done') {
            assistantMessageId = data.message.id;
            assistantMessageCreatedAt = data.message.created_at;
            citationsList = data.citations;
            tokenCount = data.token_count;
            genMs = data.generation_ms;
          } else if (event === 'error') {
            throw new Error(data.message || 'Stream error');
          }
        }
      );

      // Finalize the messages state with the completed assistant message
      set((s) => ({
        isStreaming: false,
        streamBuffer: '',
        statusMessage: null,
        messages: s.messages.map((m) =>
          m.id === assistantMessageTempId
            ? {
                ...m,
                id: assistantMessageId || m.id,
                content: textBuffer,
                citations: citationsList,
                token_count: tokenCount,
                generation_ms: genMs,
                created_at: assistantMessageCreatedAt,
              }
            : m
        ),
      }));

      await get().fetchConversations();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Chat request failed';
      set((s) => ({
        isStreaming: false,
        streamBuffer: '',
        statusMessage: null,
        error: message,
        messages: s.messages.filter((m) => m.content !== '' || m.role === 'user'),
      }));
    }
  },

  regenerate: async () => {
    const { messages } = get();
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      const filtered = messages[messages.length - 1]?.role === 'assistant'
        ? messages.slice(0, -1)
        : messages;
      set({ messages: filtered });
      await get().sendMessage(lastUserMsg.content);
    }
  },

  clearConversation: async () => {
    const { activeConversationId } = get();
    if (activeConversationId) {
      try {
        await conversationsApi.delete(activeConversationId);
      } catch {
        // ignore cleanup errors
      }
    }
    set({
      activeConversationId: null,
      messages: [],
      error: null,
    });
    await get().fetchConversations();
  },
}));
