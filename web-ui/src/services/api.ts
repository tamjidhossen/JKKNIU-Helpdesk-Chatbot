const API_URL = "http://localhost:8000";

export interface Message {
  id?: number;
  role: "user" | "assistant";
  content: string;
  query_type?: string;
  elapsed_time?: number;
  docs_retrieved?: number;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
}

export const api = {
  async chat(message: string, conversation_id?: number) {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to send message: ${response.status}`);
    }
    return response.json();
  },

  async getConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_URL}/conversations`);
    if (!response.ok) throw new Error("Failed to fetch conversations");
    return response.json();
  },

  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await fetch(`${API_URL}/conversations/${conversationId}/messages`);
    if (!response.ok) throw new Error("Failed to fetch messages");
    return response.json();
  },

  async deleteConversation(conversationId: number) {
    const response = await fetch(`${API_URL}/conversations/${conversationId}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete conversation");
    return response.json();
  },
};
