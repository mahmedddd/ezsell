import { useState, useEffect, useRef } from 'react';
import { Send, X, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { messageService } from '@/lib/api';

interface Message {
  id: number;
  content: string;
  sender_id: number;
  receiver_id: number;
  listing_id?: number;
  is_read: boolean;
  created_at: string;
  sender_username?: string;
  receiver_username?: string;
}

interface ChatWindowProps {
  listingId: number;
  listingTitle: string;
  sellerId: number;
  sellerName: string;
  currentUserId: number;
  onClose: () => void;
}

export function ChatWindow({
  listingId,
  listingTitle,
  sellerId,
  sellerName,
  currentUserId,
  onClose,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMessages();
    const interval = setInterval(loadMessages, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, [listingId, sellerId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    try {
      const data = await messageService.getConversationMessages(sellerId, listingId);
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const message = await messageService.sendMessage({
        content: newMessage.trim(),
        receiver_id: sellerId,
        listing_id: listingId,
      });
      setMessages([...messages, message]);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
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

  return (
    <Card className="fixed bottom-4 right-4 w-96 h-[500px] shadow-2xl border-2 border-[#143109] flex flex-col z-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#143109] to-[#AAAE7F] text-white p-4 flex justify-between items-center rounded-t-lg">
        <div>
          <h3 className="font-semibold">{sellerName}</h3>
          <p className="text-xs opacity-90 truncate">{listingTitle}</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="text-white hover:bg-white/20"
        >
          <X className="h-5 w-5" />
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {loading ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-[#143109]" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <p>No messages yet</p>
            <p className="text-sm">Start a conversation about this item</p>
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((message) => {
              const isSender = message.sender_id === currentUserId;
              return (
                <div
                  key={message.id}
                  className={`flex gap-2 ${isSender ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className={isSender ? 'bg-[#143109] text-white' : 'bg-gray-300'}>
                      {isSender ? 'Y' : sellerName[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className={`flex flex-col ${isSender ? 'items-end' : 'items-start'} max-w-[70%]`}>
                    <div
                      className={`rounded-lg px-3 py-2 ${
                        isSender
                          ? 'bg-[#143109] text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm break-words">{message.content}</p>
                    </div>
                    <span className="text-xs text-gray-500 mt-1">
                      {formatTime(message.created_at)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ScrollArea>

      {/* Quick Suggestions */}
      {messages.length === 0 && (
        <div className="px-4 pb-2 border-t pt-2 bg-gray-50">
          <p className="text-xs text-gray-600 mb-2">Quick messages:</p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setNewMessage('Is this still available?')}
              className="text-xs h-7"
            >
              Available?
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setNewMessage('What is your last price?')}
              className="text-xs h-7"
            >
              Last price?
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setNewMessage('What is the condition?')}
              className="text-xs h-7"
            >
              Condition?
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setNewMessage('Can we meet for inspection?')}
              className="text-xs h-7"
            >
              Inspection?
            </Button>
          </div>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSendMessage} className="p-4 border-t bg-white rounded-b-lg">
        <div className="flex gap-2">
          <Input
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={sending}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!newMessage.trim() || sending}
            className="bg-[#143109] hover:bg-[#AAAE7F] text-white"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}
