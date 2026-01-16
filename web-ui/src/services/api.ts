const API_URL = "http://localhost:8000";
const getAuthHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('token');
    return token ? { "Authorization": `Bearer ${token}` } : {};
};

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
  async chat(message: string, conversation_id?: number, response_type: string = "elaborative") {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ message, conversation_id, response_type }),
    });
    if (!response.ok) {
        if (response.status === 401) {
            // Check if we need to redirect or handle it in component
            localStorage.removeItem('token');
            // window.location.href = '/login'; // Don't redirect, just clear token
            throw new Error("Unauthorized");
        }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to send message: ${response.status}`);
    }
    return response.json();
  },

  async getConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_URL}/conversations`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) {
        if (response.status === 401) return []; // Or throw to handle in UI
        throw new Error("Failed to fetch conversations");
    }
    return response.json();
  },

  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error("Failed to fetch messages");
    return response.json();
  },

  async deleteConversation(conversationId: number) {
    const response = await fetch(`${API_URL}/conversations/${conversationId}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error("Failed to delete conversation");
    return response.json();
  },
};
