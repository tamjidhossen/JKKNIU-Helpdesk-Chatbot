import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import type { Conversation } from "../../services/api";
import { MessageSquare, Trash2, Plus, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId?: number;
  onSelect: (id: number) => void;
  onNew: () => void;
  onDelete: (id: number) => void;
}

export function ChatSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: ChatSidebarProps) {
  return (
    <Sidebar className="border-r border-muted-foreground/10">
      <SidebarHeader className="p-4 bg-background">
        <div className="flex items-center gap-2 px-2 py-4 mb-4">
           <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
             <Sparkles className="w-5 h-5 text-primary-foreground" />
           </div>
           <span className="font-semibold text-lg tracking-tight">JKKNIU Helpdesk AI</span>
        </div>
        <Button
          onClick={onNew}
          variant="outline"
          className="w-full justify-start gap-2 border-muted-foreground/10 hover:bg-muted/50 rounded-xl transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          <span className="font-medium">New Chat</span>
        </Button>
      </SidebarHeader>
      <SidebarContent className="bg-background">
        <SidebarGroup>
          <SidebarGroupLabel className="px-4 text-[11px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-2">History</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="px-2 space-y-1">
              {conversations.map((conv) => (
                <SidebarMenuItem key={conv.id}>
                  <SidebarMenuButton
                    isActive={activeId === conv.id}
                    onClick={() => onSelect(conv.id)}
                    className="group rounded-xl px-3 py-5 transition-all duration-200 active:scale-[0.98] data-[active=true]:bg-muted/80"
                  >
                    <MessageSquare className="w-4 h-4 shrink-0 opacity-60" />
                    <span className="truncate flex-1 text-sm font-medium mr-2">{conv.title}</span>
                    
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Trash2
                          className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-destructive pointer-events-auto hover:scale-110 transition-transform"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete Chat?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to delete this conversation? This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel onClick={(e) => e.stopPropagation()}>Cancel</AlertDialogCancel>
                          <AlertDialogAction 
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={(e) => {
                              e.stopPropagation();
                              onDelete(conv.id);
                            }}
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>

                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
