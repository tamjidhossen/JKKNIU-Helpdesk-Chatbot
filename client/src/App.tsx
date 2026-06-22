import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { ChatSidebar } from "./components/chat/ChatSidebar";
import { ChatInterface } from "./components/chat/ChatInterface";
import React, { useState, useEffect } from "react";
import { api } from "./services/api";
import type { Conversation } from "./services/api";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LoginDialog } from "./components/auth/LoginDialog";
import { RegisterDialog } from "./components/auth/RegisterDialog";
import { ForgotPasswordDialog } from "./components/auth/ForgotPasswordDialog";
import { Toaster } from "@/components/ui/sonner";

import { ThemeProvider } from "./components/theme-provider";
import { ModeToggle } from "./components/chat/ModeToggle";

import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import VerifyEmail from './pages/VerifyEmail';
import ResetPassword from './pages/ResetPassword';

function Dashboard() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | undefined>();
  const [loginOpen, setLoginOpen] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  
  const { logout, user, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
        fetchConversations();
    } else {
        setConversations([]);
        setActiveId(undefined);
    }
  }, [isAuthenticated]);

  const fetchConversations = async () => {
    try {
      const data = await api.getConversations();
      setConversations(data);
    } catch (error) {
    //   console.error("Failed to fetch conversations", error);
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
      <LoginDialog 
        open={loginOpen} 
        onOpenChange={setLoginOpen} 
        onRegisterClick={() => {
            setLoginOpen(false);
            setRegisterOpen(true);
        }}
        onForgotPasswordClick={() => {
            setLoginOpen(false);
            setForgotPasswordOpen(true);
        }}
      />
      <RegisterDialog
        open={registerOpen}
        onOpenChange={setRegisterOpen}
        onLoginClick={() => {
            setRegisterOpen(false);
            setLoginOpen(true);
        }}
      />
      <ForgotPasswordDialog
        open={forgotPasswordOpen}
        onOpenChange={setForgotPasswordOpen}
        onBackToLogin={() => {
            setForgotPasswordOpen(false);
            setLoginOpen(true);
        }}
      />
      
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
            
            {isAuthenticated ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                      <Avatar className="h-8 w-8">
                        {/* <AvatarImage src="/avatars/01.png" alt={user?.full_name} /> */}
                        <AvatarFallback>{user?.full_name?.charAt(0).toUpperCase() || "U"}</AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56" align="end" forceMount>
                    <DropdownMenuLabel className="font-normal">
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{user?.full_name}</p>
                        <p className="text-xs leading-none text-muted-foreground">
                          {user?.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout} className="text-red-500 cursor-pointer">
                      Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
            ) : (
                <Button variant="outline" size="sm" onClick={() => setLoginOpen(true)}>Login</Button>
            )}
          </div>
        </header>
        <main className="flex-1 overflow-hidden">
          <ChatInterface 
            activeId={activeId} 
            onConversationCreated={handleConversationCreated}
            onLoginRequest={() => setLoginOpen(true)}
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
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/" element={<Dashboard />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster />
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
