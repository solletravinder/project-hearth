import { create } from 'zustand';
import type { Conversation, Message } from '@/types';
import { conversations as conversationsApi, chat as chatApi } from '@/api/client';

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
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
  streamBuffer: '',
  statusMessage: null,
  error: null,

  fetchConversations: async () => {
    try {
      const res = await conversationsApi.list();
      set({ conversations: res.conversations });
    } catch {
      set({ error: 'Failed to load conversations' });
    }
  },

  selectConversation: async (id: string) => {
    set({ activeConversationId: id, error: null });
    try {
      const res = await conversationsApi.messages(id);
      set({ messages: res.messages });
    } catch {
      set({ error: 'Failed to load messages' });
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

      const res = await chatApi.send({
        conversation_id: convId,
        message: query,
      });

      const assistantMessage: Message = {
        id: res.message.id,
        conversation_id: convId,
        role: 'assistant',
        content: res.message.content,
        citations: res.citations ?? null,
        token_count: res.token_count,
        generation_ms: res.generation_ms,
        created_at: res.message.created_at,
      };

      set((s) => ({
        messages: [...s.messages, assistantMessage],
        isStreaming: false,
        streamBuffer: '',
        statusMessage: null,
      }));
    } catch (err) {
      set({
        isStreaming: false,
        streamBuffer: '',
        statusMessage: null,
        error: err instanceof Error ? err.message : 'Chat request failed',
      });
    }
  },

  regenerate: async () => {
    const { messages } = get();
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      // Remove last assistant message if it exists
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
        // ignore
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
