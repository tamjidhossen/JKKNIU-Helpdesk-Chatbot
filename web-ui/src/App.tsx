import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { ChatSidebar } from "./components/chat/ChatSidebar";
import { ChatInterface } from "./components/chat/ChatInterface";
import React, { useState, useEffect } from "react";
import { api } from "./services/api";
import type { Conversation } from "./services/api";
import { Separator } from "@/components/ui/separator";

import { ThemeProvider } from "./components/theme-provider";
import { ModeToggle } from "./components/chat/ModeToggle";

import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyEmail from './pages/VerifyEmail';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;
  
  return children;
}

function Dashboard() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | undefined>();
  const { logout } = useAuth();

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
          <div className="flex items-center gap-2">
            <ModeToggle />
            <button onClick={logout} className="text-xs text-red-500 hover:underline">Logout</button>
          </div>
        </header>
        <main className="flex-1 overflow-hidden">
          <ChatInterface 
            activeId={activeId} 
            onConversationCreated={handleConversationCreated} 
          />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <Router>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
          </Routes>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
