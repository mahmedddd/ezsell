import { useState, useEffect, useRef } from 'react';
import { Send, X, Loader2, Check, CheckCheck, ExternalLink, MoreVertical, ShieldAlert, Ban, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import Avatar from './ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "./ui/dropdown-menu";
import { toast } from './ui/use-toast';
import { messageService, authService, getImageUrl } from '../lib/api.ts';

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
  listing_title?: string;
  listing_image?: string;
  listing_price?: number;
}

interface ChatWindowProps {
  listingId: number;
  listingTitle: string;
  sellerId: number;
  sellerName: string;
  currentUserId: number;
  onClose: () => void;
  inline?: boolean;
  isOnline?: boolean;
  lastSeen?: string;
  sellerAvatar?: string;
  listingImage?: string;
  listingPrice?: number;
}

export function ChatWindow({
  listingId,
  listingTitle,
  sellerId,
  sellerName,
  currentUserId,
  onClose,
  inline = false,
  isOnline = false,
  lastSeen,
  sellerAvatar,
  listingImage,
  listingPrice,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isOffering, setIsOffering] = useState(false);
  const [offerAmount, setOfferAmount] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [isBlocked, setIsBlocked] = useState(false);
  const [blocking, setBlocking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMessages();
    checkBlockedStatus();
    setImgError(false);
    const interval = setInterval(loadMessages, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, [listingId, sellerId]);

  const checkBlockedStatus = async () => {
    try {
      const data = await authService.getBlockedStatus(sellerId);
      setIsBlocked(data.is_blocked);
    } catch (error) {
      console.error('Failed to check blocked status:', error);
    }
  };

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

  const handleDeleteChat = async () => {
    try {
      await messageService.deleteConversation(sellerId);
      toast({
        title: "Chat Deleted",
        description: "The conversation has been removed.",
      });
      onClose(); // Close window if deleted
    } catch (error) {
      console.error('Failed to delete chat:', error);
      toast({
        title: "Error",
        description: "Could not delete conversation.",
        variant: "destructive"
      });
    }
  const handleBlockToggle = async () => {
    setBlocking(true);
    try {
      if (isBlocked) {
        await authService.unblockUser(sellerId);
        setIsBlocked(false);
        toast({
          title: "User Unblocked",
          description: "You can now send and receive messages.",
        });
      } else {
        await authService.blockUser(sellerId);
        setIsBlocked(true);
        toast({
          title: "User Blocked",
          description: "You will no longer receive messages from this user.",
        });
      }
    } catch (error) {
      console.error('Failed to toggle block:', error);
      toast({
        title: "Error",
        description: "Could not update block status.",
        variant: "destructive"
      });
    } finally {
      setBlocking(false);
    }
  };

  const handleReport = async () => {
    const reason = prompt("Please enter the reason for reporting this user:");
    if (!reason) return;

    try {
      await authService.reportUser(sellerId, reason);
      toast({
        title: "User Reported",
        description: "Your report has been submitted to admin.",
      });
    } catch (error) {
      console.error('Failed to report user:', error);
      toast({
        title: "Error",
        description: "Could not submit report.",
        variant: "destructive"
      });
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (sending) return;

    let contentToSend = newMessage.trim();

    if (isOffering) {
      if (!offerAmount || isNaN(Number(offerAmount))) return;
      contentToSend = JSON.stringify({ type: 'offer', amount: Number(offerAmount) });
    } else if (!contentToSend) {
      return;
    }

    setSending(true);
    try {
      const message = await messageService.sendMessage({
        content: contentToSend,
        receiver_id: sellerId,
        listing_id: listingId,
      });
      setMessages([...messages, message]);
      setNewMessage('');
      setOfferAmount('');
      setIsOffering(false);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
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

  return (
    <div className={`flex flex-col bg-white border shadow-xl overflow-hidden ${inline ? 'h-full w-full' : 'fixed bottom-4 right-4 w-[380px] h-[550px] z-50 rounded-lg'}`}>
      {/* Header */}
      <div className="p-4 border-b bg-[#143109] text-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to={`/profile/${sellerId}`} className="hover:opacity-80 transition-opacity flex items-center gap-3">
            <div className="relative">
              {sellerAvatar && !imgError ? (
                <img
                  src={getImageUrl(sellerAvatar)}
                  alt={sellerName}
                  className="w-10 h-10 rounded-xl object-cover border-2 border-white/20"
                  onError={() => setImgError(true)}
                />
              ) : (
                <Avatar seed={sellerName} size={40} className="border-2 border-white/20" />
              )}
              {isOnline && (
                <span className="absolute bottom-0 right-0 h-3 w-3 bg-green-400 border-2 border-[#143109] rounded-full shadow-sm" />
              )}
            </div>
            <div className="flex flex-col">
              <span className="font-bold leading-tight">{sellerName}</span>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-400' : 'bg-gray-400'}`} />
                <span className="text-[11px] text-white/70">
                  {isOnline ? 'Online' : lastSeen ? `Last seen ${formatTime(lastSeen)}` : 'Offline'}
                </span>
              </div>
            </div>
          </Link>
        </div>
        <div className="flex items-center gap-1">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-white hover:bg-white/10">
                <MoreVertical className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuItem 
                className="text-gray-700 cursor-pointer"
                disabled={blocking}
                onClick={(e) => {
                  e.stopPropagation();
                  handleBlockToggle();
                }}
              >
                <Ban className={`mr-2 h-4 w-4 ${isBlocked ? 'text-green-600' : 'text-red-600'}`} />
                <span>{isBlocked ? 'Unblock User' : 'Block User'}</span>
              </DropdownMenuItem>
              <DropdownMenuItem 
                className="text-gray-700 cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  handleReport();
                }}
              >
                <ShieldAlert className="mr-2 h-4 w-4" />
                <span>Report User</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                className="text-red-600 focus:bg-red-50 focus:text-red-700 cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteChat();
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                <span>Delete Chat</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {!inline && (
            <Button variant="ghost" size="icon" onClick={onClose} className="text-white hover:bg-white/10">
              <X className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>

      {/* Ad Reference Card */}
      <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
        <Link to={`/product/${listingId}`} className="flex items-center gap-3 flex-1 hover:bg-gray-100 p-1 rounded-lg transition-colors overflow-hidden">
          <div className="w-10 h-10 rounded-md overflow-hidden bg-gray-200 flex-shrink-0">
            {listingImage ? (
              <img
                src={getImageUrl(listingImage)}
                alt={listingTitle}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-[10px] text-gray-400">No img</div>
            )}
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="text-xs font-semibold text-gray-900 truncate">{listingTitle}</span>
            {listingPrice && <span className="text-[11px] text-[#143109] font-bold">Rs {listingPrice.toLocaleString()}</span>}
          </div>
        </Link>
        <Link to={`/product/${listingId}`} className="text-[#143109] hover:text-[#1e4d10] p-2">
          <ExternalLink className="w-4 h-4" />
        </Link>
      </div>

      {/* Messages area */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {loading ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-[#143109]" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <p className="font-medium">No messages yet</p>
            <p className="text-sm">Start a conversation about this item</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => {
              const isSender = message.sender_id === currentUserId;
              let isOffer = false;
              let offerVal = 0;
              let displayContent = message.content;

              try {
                const parsed = JSON.parse(message.content);
                if (parsed.type === 'offer') {
                  isOffer = true;
                  offerVal = parsed.amount;
                }
              } catch (e) { }

              return (
                <div key={message.id} className={`flex gap-2 ${isSender ? 'flex-row-reverse' : 'flex-row'}`}>
                  <Avatar seed={isSender ? (localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')!).username : 'YOU') : sellerName} size={32} className="mt-1" />
                  <div className={`flex flex-col ${isSender ? 'items-end' : 'items-start'} max-w-[80%]`}>
                    {isOffer ? (
                      <div className={`rounded-2xl px-4 py-3 border-2 ${isSender ? 'border-[#143109] bg-[#143109]/5' : 'border-[#AAAE7F] bg-[#AAAE7F]/10'}`}>
                        <div className="font-semibold text-xs text-gray-500 mb-1">OFFER MADE</div>
                        <div className="text-lg font-bold text-[#143109]">
                          Rs {offerVal.toLocaleString()}
                        </div>
                      </div>
                    ) : (
                      <div className={`rounded-2xl px-4 py-2.5 shadow-sm text-sm ${isSender ? 'bg-[#143109] text-white rounded-tr-none' : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'}`}>
                        <p className="whitespace-pre-wrap break-words">{displayContent}</p>
                      </div>
                    )}
                    <div className="flex items-center gap-1 mt-1 px-1">
                      <span className="text-[10px] text-gray-400">{formatTime(message.created_at)}</span>
                      {isSender && (
                        message.is_read ? <CheckCheck className="h-3 w-3 text-blue-500" /> : <Check className="h-3 w-3 text-gray-300" />
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {isBlocked && (
              <div className="flex justify-center my-4">
                <div className="bg-red-50 text-red-600 px-4 py-2 rounded-full text-xs font-medium border border-red-100">
                  You have blocked this user
                </div>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* Input area */}
      <div className="p-4 border-t bg-white">
        {isOffering && (
          <div className="mb-3 p-3 bg-gray-50 rounded-xl border border-dashed border-[#143109]/30 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#143109]">MAKE AN OFFER</span>
              <Button variant="ghost" size="sm" onClick={() => setIsOffering(false)} className="h-6 w-6 p-0 text-gray-400 hover:text-red-500">
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">Rs</span>
                <Input
                  type="number"
                  value={offerAmount}
                  onChange={(e) => setOfferAmount(e.target.value)}
                  placeholder="0.00"
                  className="pl-10 h-10 rounded-lg border-gray-200 focus:border-[#143109]"
                  autoFocus
                />
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!offerAmount || sending}
                className="bg-[#143109] text-white rounded-lg px-4"
              >
                Send Offer
              </Button>
            </div>
          </div>
        )}

        <div className="flex gap-2 items-center">
          {!isOffering && (
            <Button
              variant="outline"
              onClick={() => setIsOffering(true)}
              className="rounded-full w-10 h-10 p-0 border-[#143109]/20 text-[#143109] hover:bg-[#143109]/5 flex-shrink-0"
            >
              <span className="text-xs font-bold">Rs</span>
            </Button>
          )}
          <div className="relative flex-1">
            <Input
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isOffering && handleSendMessage(e)}
              placeholder={isBlocked ? "Unblock to send messages" : "Type a message..."}
              disabled={isBlocked}
              className="rounded-full bg-gray-100 border-none h-10 px-4 focus-visible:ring-1 focus-visible:ring-[#143109] disabled:opacity-50"
            />
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={(!newMessage.trim() && !isOffering) || sending || isBlocked}
            className="rounded-full w-10 h-10 p-0 bg-[#143109] hover:bg-[#1e4d10] flex-shrink-0"
          >
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}
