import React from "react";
import type { Message } from "../../services/api";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { MetadataCard } from "./MetadataCard";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";

interface MessageItemProps {
  message: Message;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isAssistant = message.role === "assistant";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.5, 
        ease: [0.16, 1, 0.3, 1] 
      }}
      className={cn(
        "flex w-full gap-4 px-4 py-8 md:px-6",
        isAssistant ? "bg-muted/30" : "bg-transparent"
      )}
    >
      <div className="max-w-3xl mx-auto flex w-full gap-4 px-2">
        <Avatar className="w-8 h-8 rounded-lg shrink-0 border">
          <AvatarImage src={isAssistant ? "/bot-avatar.png" : "/user-avatar.png"} />
          <AvatarFallback className={isAssistant ? "bg-primary text-primary-foreground font-medium" : "bg-background font-medium"}>
            {isAssistant ? "AI" : "U"}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 space-y-4 min-w-0">
          <div className="prose prose-slate dark:prose-invert max-w-none text-[15px] leading-relaxed break-words">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
          {isAssistant && <MetadataCard message={message} />}
        </div>
      </div>
    </motion.div>
  );
};
