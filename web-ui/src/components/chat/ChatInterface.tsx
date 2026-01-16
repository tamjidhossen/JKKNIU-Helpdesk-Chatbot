import React, { useState, useEffect, useRef } from "react";
import { api } from "../../services/api";
import type { Message } from "../../services/api";
import { MessageItem } from "./MessageItem";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Loader2, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { TextShimmerWave } from '@/components/motion-primitives/text-shimmer-wave';

interface ChatInterfaceProps {
  activeId?: number;
  onConversationCreated: (id: number) => void;
}

const SUGGESTED_QUESTIONS = [
  "How to get admission at JKKNIU?",
  "Tell me about the Computer Science department.",
  "What are the academic regulations?",
  "How can I contact the administration?",
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  activeId,
  onConversationCreated,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [responseType, setResponseType] = useState("elaborative");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (activeId) {
      loadMessages(activeId);
    } else {
      setMessages([]);
    }
  }, [activeId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "inherit";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`;
    }
  }, [input]);

  const loadMessages = async (id: number) => {
    try {
      const msgs = await api.getMessages(id);
      setMessages(msgs);
      setError(null);
    } catch (err) {
      console.error("Failed to load messages", err);
      setError("Failed to load conversation history. The server might be down.");
    }
  };

  const handleSend = async (forcedInput?: string) => {
    const textToSend = typeof forcedInput === "string" ? forcedInput : input;
    if (!textToSend.trim() || isLoading) return;

    setError(null);
    const userMsg: Message = { role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    if (typeof forcedInput !== "string") setInput("");
    setIsLoading(true);

    try {
      const data = await api.chat(textToSend, activeId, responseType);
      
      if (!activeId) {
        onConversationCreated(data.conversation_id);
      }

      const assistantMsg: Message = {
        role: "assistant",
        content: data.response,
        query_type: data.metadata.query_type,
        elapsed_time: data.metadata.elapsed_time,
        docs_retrieved: data.metadata.docs_retrieved,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("Failed to send message", err);
      let errorMessage = "Sorry, I encountered an error. Please try again.";
      
      if (err.message?.includes("429")) {
        errorMessage = "Experiencing heavy load. Please wait a moment before trying again.";
      } else if (err.message?.includes("500")) {
        errorMessage = "Server error. The AI model might be temporarily unavailable.";
      }
      
      setError(errorMessage);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: errorMessage },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background selection:bg-primary/20">
      <ScrollArea className="flex-1 overflow-x-hidden">
        <div className="flex flex-col min-h-full">
          <AnimatePresence initial={false}>
            {messages.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                className="flex-1 flex flex-col items-center justify-center text-center px-4 pt-20 pb-10"
              >
                <div className="mb-6">
                  <img 
                    src="/uni-logo-black.png" 
                    alt="JKKNIU Logo" 
                    className="h-24 w-auto object-contain block dark:hidden opacity-90"
                  />
                  <img 
                    src="/uni-logo-white.png" 
                    alt="JKKNIU Logo" 
                    className="h-24 w-auto object-contain hidden dark:block opacity-90"
                  />
                </div>
                <h1 className="text-4xl font-semibold tracking-tight mb-4 text-foreground/90">
                  How can <span className="text-primary font-bold">JKKNIU Helpdesk</span> assist you?
                </h1>
                <p className="text-muted-foreground/80 max-w-lg text-[16px] leading-relaxed mb-10">
                  I can help with academic regulations, department inquiries, 
                  course details, and more. Try asking something complex!
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
                  {SUGGESTED_QUESTIONS.map((q, i) => (
                    <motion.button
                      key={q}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 + 0.3 }}
                      onClick={() => handleSend(q)}
                      className="text-left px-4 py-3 rounded-xl border bg-card hover:bg-muted/50 hover:border-primary/20 transition-all duration-200 text-sm font-medium flex items-center gap-3 group"
                    >
                      <span className="flex-1 truncate">{q}</span>
                      <Send className="w-3.5 h-3.5 opacity-0 group-hover:opacity-40 transition-opacity" />
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            ) : (
              <div className="flex flex-col">
                {messages.map((msg, i) => <MessageItem key={i} message={msg} />)}
                {isLoading && (
                   <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex w-full gap-4 px-4 py-8 md:px-6 bg-muted/10 rounded-lg"
                   >
                    <div className="max-w-3xl mx-auto flex w-full gap-4 px-2 items-center">
                       <div className="w-8 h-8 rounded-lg shrink-0 border bg-background flex items-center justify-center animate-pulse">
                         <div className="w-2 h-2 bg-primary/40 rounded-full" />
                       </div>
                       <TextShimmerWave className='font-medium text-sm' duration={1}>
                        Thinking...
                       </TextShimmerWave>
                    </div>
                   </motion.div>
                )}
              </div>
            )}
          </AnimatePresence>
          <div ref={scrollRef} className="h-32" />
        </div>
      </ScrollArea>

      <div className="px-4 pb-6 pt-2 bg-gradient-to-t from-background via-background to-transparent sticky bottom-0 z-10">
        <div className="max-w-3xl mx-auto space-y-4">
          <div className="flex justify-between items-center px-1">
             <div className="flex gap-2">
                 <select 
                    value={responseType} 
                    onChange={(e) => setResponseType(e.target.value)}
                    className="text-xs border rounded px-2 py-1 bg-background"
                 >
                     <option value="concise">Concise Response</option>
                     <option value="elaborative">Elaborative Response</option>
                 </select>
             </div>
          </div>

          {error && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <Alert variant="destructive" className="rounded-xl border-destructive/20 bg-destructive/5 text-destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </motion.div>
          )}

          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/10 to-primary/20 rounded-[22px] blur opacity-0 group-focus-within:opacity-100 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative flex flex-col bg-background border rounded-[20px] shadow-lg transition-all duration-200 focus-within:ring-1 focus-within:ring-primary/20 focus-within:border-primary/30 overflow-hidden">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask anything..."
                className="min-h-[60px] max-h-[200px] w-full resize-none bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 px-4 pt-4 pb-12 text-[15px] leading-relaxed"
                disabled={isLoading}
              />
              <div className="absolute bottom-3 right-3 flex items-center gap-2">
                <Button 
                  onClick={() => handleSend()} 
                  disabled={isLoading || !input.trim()}
                  size="icon"
                  className="h-8 w-8 rounded-xl shadow-sm transition-all duration-200 active:scale-95 disabled:opacity-50"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
              </div>
              <div className="absolute bottom-3 left-4 text-[11px] text-muted-foreground/60 flex items-center gap-2">
                 <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-muted/50 border border-muted-foreground/20">Enter</kbd> to send</span>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-center text-muted-foreground/50 font-medium tracking-tight">
            AI helps JKKNIU students. official site: <a href="https://jkkniu.edu.bd" className="hover:text-primary transition-colors">jkkniu.edu.bd</a>
          </p>
        </div>
      </div>
    </div>
  );
};
