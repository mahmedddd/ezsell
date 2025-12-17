import { useEffect, useState } from 'react';
import { MessageCircle, Loader2, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatWindow } from '@/components/ChatWindow';
import { messageService } from '@/lib/api';

interface Conversation {
  user_id: number;
  username: string;
  avatar_url?: string;
  listing_id?: number;
  listing_title?: string;
  last_message: string;
  last_message_time: string;
  unread_count: number;
}

export default function Messages() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChat, setSelectedChat] = useState<Conversation | null>(null);
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

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

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
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

  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc]">
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => navigate('/')} className="mb-4 text-[#143109] hover:bg-[#143109]/10">
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
        <Card>
          <CardHeader className="bg-gradient-to-r from-[#143109] to-[#AAAE7F] text-white rounded-t-lg">
            <div className="flex justify-between items-center">
              <CardTitle className="text-2xl flex items-center gap-2">
                <MessageCircle className="h-6 w-6" />
                Messages
              </CardTitle>
              {totalUnread > 0 && (
                <Badge className="bg-red-500 text-white">
                  {totalUnread} unread
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-[#143109]" />
              </div>
            ) : conversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <MessageCircle className="h-16 w-16 mb-4 opacity-50" />
                <p className="text-lg font-semibold">No messages yet</p>
                <p className="text-sm">Start chatting with sellers on their listings</p>
              </div>
            ) : (
              <ScrollArea className="h-[600px]">
                <div className="divide-y">
                  {conversations.map((conversation) => (
                    <div
                      key={`${conversation.user_id}-${conversation.listing_id}`}
                      onClick={() => setSelectedChat(conversation)}
                      className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className="flex gap-4">
                        <Avatar className="h-12 w-12">
                          <AvatarFallback className="bg-[#143109] text-white text-lg">
                            {conversation.username[0]?.toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start mb-1">
                            <div>
                              <h3 className="font-semibold text-slate-900 truncate">
                                {conversation.username}
                              </h3>
                              {conversation.listing_title && (
                                <p className="text-xs text-gray-500 truncate">
                                  About: {conversation.listing_title}
                                </p>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500 whitespace-nowrap">
                                {formatTime(conversation.last_message_time)}
                              </span>
                              {conversation.unread_count > 0 && (
                                <Badge className="bg-[#143109] text-white">
                                  {conversation.unread_count}
                                </Badge>
                              )}
                            </div>
                          </div>
                          
                          <p className="text-sm text-gray-600 truncate">
                            {conversation.last_message}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Chat Window */}
      {selectedChat && selectedChat.listing_id && (
        <ChatWindow
          listingId={selectedChat.listing_id}
          listingTitle={selectedChat.listing_title || 'Chat'}
          sellerId={selectedChat.user_id}
          sellerName={selectedChat.username}
          currentUserId={currentUser.id}
          onClose={() => setSelectedChat(null)}
        />
      )}
    </div>
  );
}
