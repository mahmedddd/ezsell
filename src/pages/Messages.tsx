import { useEffect, useState } from 'react';
import { MessageCircle, Loader2, Home, Trash2, MoreVertical, ShieldAlert, Ban } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { messageService, authService, getImageUrl } from '../lib/api.ts';
import { toast } from '@/components/ui/use-toast';
import Avatar from '@/components/ui/avatar';
import { ChatWindow } from '@/components/ChatWindow';

interface Conversation {
  user_id: number;
  username: string;
  avatar_url?: string;
  listing_id?: number;
  listing_title?: string;
  listing_image?: string;
  listing_price?: number;
  last_message: string;
  last_message_time: string;
  unread_count: number;
  is_online: boolean;
  last_seen?: string;
}

export default function Messages() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChat, setSelectedChat] = useState<Conversation | null>(null);
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const navigate = useNavigate();

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadConversations = async () => {
    try {
      const data = await messageService.getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (userId: number, e: React.MouseEvent) => {
    e.stopPropagation(); // prevent opening chat
    if (!confirm('Are you sure you want to delete this entire conversation?')) return;
    try {
      await messageService.deleteConversation(userId);
      toast({ title: 'Conversation deleted' });
      if (selectedChat?.user_id === userId) {
        setSelectedChat(null);
      }
      loadConversations();
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      toast({ title: 'Failed to delete conversation', variant: 'destructive' });
    }
  };

  const handleBlockUser = async (userId: number, username: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to block ${username}?`)) return;
    try {
      await authService.blockUser(userId);
      toast({ title: `Blocked @${username}` });
      loadConversations();
    } catch (error) {
      console.error('Failed to block user:', error);
      toast({ title: 'Failed to block user', variant: 'destructive' });
    }
  };

  const handleReportUser = async (userId: number, username: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const reason = prompt(`Enter reason for reporting @${username}:`);
    if (!reason) return;
    try {
      await authService.reportUser(userId, reason);
      toast({ title: `Reported @${username}` });
    } catch (error) {
      console.error('Failed to report user:', error);
      toast({ title: 'Failed to report user', variant: 'destructive' });
    }
  };

  const formatTime = (dateString: string) => {
    const utcDateString = dateString.endsWith('Z') || dateString.includes('+') ? dateString : `${dateString}Z`;
    const date = new Date(utcDateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const totalUnread = conversations.reduce((sum, conv) => sum + conv.unread_count, 0);

  const [convImgErrors, setConvImgErrors] = useState<Record<number, boolean>>({});

  const handleImgError = (userId: number) => {
    setConvImgErrors(prev => ({ ...prev, [userId]: true }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex flex-col">
      <div className="container mx-auto px-4 py-8 flex-1 flex flex-col h-[calc(100vh-80px)]">

        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <Button variant="ghost" onClick={() => navigate('/')} className="text-[#2E6091] hover:bg-[#2E6091]/10 -ml-4">
            <Home className="mr-2 h-4 w-4" /> Back to Home
          </Button>
          <div className="flex items-center gap-2 text-[#2E6091]">
            <MessageCircle className="h-6 w-6 sm:h-8 sm:w-8" />
            <h1 className="text-xl sm:text-2xl font-bold">Messages Dashboard</h1>
            {totalUnread > 0 && (
              <Badge className="bg-red-500 text-white ml-2">
                {totalUnread} New
              </Badge>
            )}
          </div>
        </div>

        {/* Main Split Pane */}
        <Card className="flex-1 flex overflow-hidden shadow-2xl rounded-2xl border-0 bg-white/90 backdrop-blur">

          {/* Left Pane: Conversation List */}
          <div className={`${selectedChat ? 'hidden md:flex' : 'flex'} w-full md:w-[350px] lg:w-[400px] border-r border-gray-100 flex-col bg-gray-50/50`}>
            <div className="p-4 border-b border-gray-100 bg-white">
              <h2 className="font-semibold text-lg text-gray-800">Inbox</h2>
            </div>

            {loading ? (
              <div className="flex justify-center items-center flex-1">
                <Loader2 className="h-8 w-8 animate-spin text-[#2E6091]" />
              </div>
            ) : conversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center flex-1 text-gray-400">
                <MessageCircle className="h-12 w-12 mb-3 opacity-20" />
                <p>No messages yet</p>
              </div>
            ) : (
              <ScrollArea className="flex-1">
                <div className="divide-y divide-gray-100">
                  {conversations.map((conversation) => {
                    const isActive = selectedChat?.user_id === conversation.user_id;
                    return (
                      <div
                        key={conversation.user_id}
                        onClick={() => setSelectedChat(conversation)}
                        className={`p-4 cursor-pointer transition-all hover:bg-[#2E6091]/5 group relative ${isActive ? 'bg-[#2E6091]/10 border-l-4 border-l-[#2E6091]' : 'border-l-4 border-transparent'
                          }`}
                      >
                        <div className="flex gap-4 items-center">
                          <div className="relative">
                            {conversation.avatar_url && !convImgErrors[conversation.user_id] ? (
                              <img
                                src={getImageUrl(conversation.avatar_url)}
                                alt={conversation.username}
                                className="h-12 w-12 rounded-xl object-cover border-2 border-white shadow-sm"
                                onError={() => handleImgError(conversation.user_id)}
                              />
                            ) : (
                              <Avatar seed={conversation.username} size={48} className="rounded-xl" />
                            )}
                            {conversation.is_online && (
                              <span className="absolute bottom-0 right-0 h-3.5 w-3.5 bg-green-500 border-2 border-white rounded-full shadow-sm" title="Online" />
                            )}
                          </div>

                          <div className="flex-1 min-w-0 pr-10">
                            <div className="flex justify-between items-baseline mb-0.5">
                              <h3 className={`font-semibold truncate ${isActive ? 'text-[#2E6091]' : 'text-gray-900'}`}>
                                {conversation.username}
                              </h3>
                              <span className="text-xs text-gray-400 font-medium whitespace-nowrap ml-2">
                                {formatTime(conversation.last_message_time)}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <p className={`text-sm truncate ${conversation.unread_count > 0 ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
                                {conversation.last_message}
                              </p>
                              {!conversation.is_online && conversation.last_seen && (
                                <span className="text-[10px] text-gray-400 whitespace-nowrap italic">
                                  Seen {formatTime(conversation.last_seen)}
                                </span>
                              )}
                            </div>

                            {conversation.unread_count > 0 && (
                              <Badge className="bg-[#4591CB] text-white mt-2 absolute top-1/2 -translate-y-1/2 right-12 shadow-sm border-0">
                                {conversation.unread_count}
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Dropdown Menu (Visible on hover on desktop, always visible on mobile) */}
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-gray-400 hover:text-gray-600 hover:bg-gray-100 focus:opacity-100"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-40">
                              <DropdownMenuItem 
                                className="text-gray-700 cursor-pointer"
                                onClick={(e) => handleBlockUser(conversation.user_id, conversation.username, e as any)}
                              >
                                <Ban className="mr-2 h-4 w-4 text-red-600" />
                                <span>Block User</span>
                              </DropdownMenuItem>
                              <DropdownMenuItem 
                                className="text-gray-700 cursor-pointer"
                                onClick={(e) => handleReportUser(conversation.user_id, conversation.username, e as any)}
                              >
                                <ShieldAlert className="mr-2 h-4 w-4" />
                                <span>Report User</span>
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-red-600 focus:bg-red-50 focus:text-red-700 cursor-pointer"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteConversation(conversation.user_id, e as any);
                                }}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                <span>Delete Chat</span>
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </div>

          {/* Right Pane: Chat Window / Empty State */}
          <div className={`${selectedChat ? 'flex' : 'hidden md:flex'} flex-1 flex-col bg-white relative`}>
            {selectedChat ? (
              <ChatWindow
                listingId={selectedChat.listing_id || 0}
                listingTitle={selectedChat.listing_title || 'General Chat'}
                sellerId={selectedChat.user_id}
                sellerName={selectedChat.username}
                sellerAvatar={selectedChat.avatar_url}
                currentUserId={currentUser.id}
                onClose={() => setSelectedChat(null)}
                inline={true}
                isOnline={selectedChat.is_online}
                lastSeen={selectedChat.last_seen}
                listingImage={selectedChat.listing_image}
                listingPrice={selectedChat.listing_price}
              />
            ) : (
              <div className="flex flex-col items-center justify-center flex-1 text-gray-400 bg-gray-50/50">
                <MessageCircle className="h-20 w-20 mb-6 opacity-10" />
                <h3 className="text-xl font-medium text-gray-500 mb-2">Select a Conversation</h3>
                <p className="border-t border-gray-200 pt-3 max-w-sm text-center">
                  Choose a chat from the sidebar to view the full message history, make an offer, or delete the conversation.
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
