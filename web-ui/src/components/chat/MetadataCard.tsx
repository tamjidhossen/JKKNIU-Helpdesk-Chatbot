import React from "react";
import type { Message } from "../../services/api";
import { Card, CardContent } from "@/components/ui/card";
import { Clock, Database } from "lucide-react";
import { motion } from "framer-motion";

interface MetadataCardProps {
  message: Message;
}

export const MetadataCard: React.FC<MetadataCardProps> = ({ message }) => {
  if (message.role === "user" || !message.query_type) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 260, damping: 20, delay: 0.2 }}
    >
      <Card className="mt-2 bg-muted/50 border-none shadow-none hover:bg-muted/70 transition-colors">
        <CardContent className="p-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{message.elapsed_time?.toFixed(2)}s</span>
          </div>
          <div className="flex items-center gap-1">
            <Database className="w-3 h-3" />
            <span>{message.docs_retrieved} docs</span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
