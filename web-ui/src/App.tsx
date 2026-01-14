import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { ChatSidebar } from "./components/chat/ChatSidebar";
import { ChatInterface } from "./components/chat/ChatInterface";
import { useState, useEffect } from "react";
import { api } from "./services/api";
import type { Conversation } from "./services/api";
import { Separator } from "@/components/ui/separator";

import { ThemeProvider } from "./components/theme-provider";
import { ModeToggle } from "./components/chat/ModeToggle";

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | undefined>();

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const data = await api.getConversations();
      setConversations(data);
    } catch (error) {
      console.error("Failed to fetch conversations", error);
    }
  };

  const handleConversationCreated = (id: number) => {
    setActiveId(id);
    fetchConversations();
  };

  const handleDeleteConversation = async (id: number) => {
    try {
      await api.deleteConversation(id);
      if (activeId === id) setActiveId(undefined);
      fetchConversations();
    } catch (error) {
      console.error("Failed to delete conversation", error);
    }
  };

  const handleNewChat = () => {
    setActiveId(undefined);
  };

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <SidebarProvider>
        <ChatSidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={handleNewChat}
          onDelete={handleDeleteConversation}
        />
        <SidebarInset className="flex flex-col h-screen overflow-hidden">
          <header className="flex h-14 shrink-0 items-center justify-between gap-2 px-4 border-b">
            <div className="flex items-center gap-2">
              <SidebarTrigger />
              <Separator orientation="vertical" className="h-4" />
              <h2 className="text-sm font-semibold truncate max-w-[200px] sm:max-w-none">
                {activeId 
                  ? conversations.find((c: Conversation) => c.id === activeId)?.title 
                  : "New Conversation"}
              </h2>
            </div>
            <ModeToggle />
          </header>
          <main className="flex-1 overflow-hidden">
            <ChatInterface 
              activeId={activeId} 
              onConversationCreated={handleConversationCreated} 
            />
          </main>
        </SidebarInset>
      </SidebarProvider>
    </ThemeProvider>
  );
}

export default App;
