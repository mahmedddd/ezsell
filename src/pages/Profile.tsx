import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Avatar, { parseAvatarUrl } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { authService, supportService, analyticsService, getImageUrl } from '../lib/api.ts';
import { listingService } from '../lib/api.ts';
import { useToast } from '@/components/ui/use-toast';
import {
    User,
    Mail,
    Phone,
    MapPin,
    FileText,
    LifeBuoy,
    Bug,
    History,
    CheckCircle2,
    Clock,
    ShieldCheck,
    Star,
    Heart,
    TrendingUp,
    Award,
    ArrowRight,
    Search as SearchIcon,
    LayoutGrid,
    Package,
    Camera,
    Palette,
    Zap
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

export default function Profile() {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [tickets, setTickets] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [userListings, setUserListings] = useState<any[]>([]);
    const [imgError, setImgError] = useState(false);
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { toast } = useToast();
    const isOwnProfile = !id;

    // Support Form State
    const [supportForm, setSupportForm] = useState({
        ticket_type: 'support',
        subject: '',
        description: ''
    });

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        setImgError(false); // Reset error state when user data changes
    }, [user?.avatar_url]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (id) {
                // Fetch public profile
                const [userData, listingsData] = await Promise.all([
                    authService.getUser(id),
                    listingService.getListings({ owner_id: id })
                ]);
                setUser(userData);
                setUserListings(listingsData);
                // For a public profile, we don't have personal stats/tickets
                setTickets([]);
                setStats({ total_listings: listingsData.length });
            } else {
                // Fetch own profile
                const token = localStorage.getItem('authToken');
                if (!token) {
                    navigate('/login');
                    return;
                }

                const [userData, ticketData, analyticsData, listingsData] = await Promise.all([
                    authService.getCurrentUser(),
                    supportService.getMyTickets(),
                    analyticsService.getDashboard(30),
                    listingService.getMyListings()
                ]);

                setUser(userData);
                setTickets(ticketData);
                setStats(analyticsData);
                setUserListings(listingsData);
            }
        } catch (error) {
            console.error('Failed to fetch data:', error);
            toast({
                title: 'Error',
                description: 'Failed to load profile data',
                variant: 'destructive'
            });
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();

        // Final validation
        if (user.phone && (!/^\d{11}$/.test(user.phone))) {
            toast({
                title: 'Invalid Phone Number',
                description: 'Please enter exactly 11 digits (e.g., 03018738298).',
                variant: 'destructive'
            });
            return;
        }

        setSaving(true);
        try {
            const updatedUser = await authService.updateProfile({
                full_name: user.full_name,
                phone: user.phone,
                bio: user.bio,
                location: user.location,
                avatar_url: user.avatar_url
            });
            toast({
                title: 'Profile Updated',
                description: 'Your changes have been saved successfully! ✨'
            });
            // Update local storage and notify other components
            setUser(updatedUser);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            window.dispatchEvent(new CustomEvent('user-updated'));
        } catch (error) {
            toast({
                title: 'Update Failed',
                description: 'Could not save profile changes.',
                variant: 'destructive'
            });
        } finally {
            setSaving(false);
        }
    };

    const handleSubmitTicket = async (type: 'support' | 'bug') => {
        if (!supportForm.subject || !supportForm.description) {
            toast({
                title: 'Missing Info',
                description: 'Please provide a subject and description.',
                variant: 'destructive'
            });
            return;
        }

        setSaving(true);
        try {
            await supportService.createTicket({
                ...supportForm,
                ticket_type: type
            });
            toast({
                title: type === 'support' ? 'Request Sent!' : 'Bug Reported!',
                description: 'Our team will look into it right away. Thank you for helping us improve! ❤️'
            });
            setSupportForm({ ticket_type: 'support', subject: '', description: '' });
            const updatedTickets = await supportService.getMyTickets();
            setTickets(updatedTickets);
        } catch (error) {
            toast({
                title: 'Submission Failed',
                description: 'Something went wrong. Please try again later.',
                variant: 'destructive'
            });
        } finally {
            setSaving(false);
        }
    };

    const handleAvatarClick = (preset: string) => {
        if (!isOwnProfile) return;
        const newUser = { ...user, avatar_url: preset };
        setUser(newUser);
        // We'll save it when they hit "Save Profile Changes" or immediately?
        // Let's do it immediately for better UX
        authService.updateProfile({ avatar_url: preset }).then((updatedUser) => {
            setUser(updatedUser);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            toast({ title: "Avatar Updated! ✨", description: "Your new stylish look is saved." });
            window.dispatchEvent(new CustomEvent('user-updated'));
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#f5f5f0] flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#2E6091]" />
            </div>
        );
    }

    const avatarPresets = [
        { id: 'init', label: 'Initial', value: `init:${(user?.full_name || user?.username || 'U')[0]}` },
        { id: 'sunset', label: 'Sunset', value: 'style:sunset:1' },
        { id: 'emerald', label: 'Emerald', value: 'style:emerald:0' },
        { id: 'midnight', label: 'Midnight', value: 'style:midnight:2' },
        { id: 'ocean', label: 'Ocean', value: 'style:ocean:3' },
        { id: 'berry', label: 'Berry', value: 'style:berry:4' },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] pb-12">
            {/* Wholesome Hero Section */}
            <div className="bg-[#2E6091] text-white py-16 px-4">
                <div className="container mx-auto max-w-5xl">
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <div className="relative group/avatar">
                            <div className="w-32 h-32 rounded-[2rem] border-4 border-white/20 overflow-hidden shadow-2xl transition-all duration-300 group-hover/avatar:scale-105 group-hover/avatar:border-white/40">
                                {user?.avatar_url && !imgError && (user.avatar_url.startsWith('http') || user.avatar_url.startsWith('/uploads')) ? (
                                    <img
                                        src={getImageUrl(user.avatar_url)}
                                        alt="Avatar"
                                        className="w-full h-full object-cover"
                                        onError={() => setImgError(true)}
                                    />
                                ) : (
                                    <Avatar {...parseAvatarUrl(user?.avatar_url, user?.username)} size={128} className="w-full h-full" />
                                )}
                            </div>
                            <div className="absolute -bottom-2 -right-2 bg-yellow-400 p-2 rounded-full shadow-lg">
                                <Star className="w-5 h-5 text-[#2E6091] fill-current" />
                            </div>
                        </div>
                        <div className="text-center md:text-left space-y-2">
                            <h1 className="text-4xl font-bold tracking-tight">
                                {isOwnProfile
                                    ? `Hey ${user?.full_name?.split(' ')[0] || user?.username}, you're awesome! 🌟`
                                    : `${user?.full_name || user?.username}'s Profile`}
                            </h1>
                            <p className="text-white/80 max-w-2xl text-lg">
                                {isOwnProfile
                                    ? "Welcome to your command center. Whether you're making deals, looking for help, or telling us how we can do better, we're glad you're here."
                                    : `Check out ${user?.full_name || user?.username}'s profile and their amazing listings! 🚀`}
                            </p>
                            <div className="flex flex-wrap justify-center md:justify-start gap-3 pt-2">
                                <Badge className="bg-white/20 hover:bg-white/30 text-white border-0 py-1.5 px-4 rounded-full flex gap-2 items-center">
                                    <ShieldCheck className="w-4 h-4 text-green-300" /> Verified Member
                                </Badge>
                                <Badge className="bg-white/20 hover:bg-white/30 text-white border-0 py-1.5 px-4 rounded-full flex gap-2 items-center">
                                    <Clock className="w-4 h-4 text-blue-300" /> Joined {new Date(user?.created_at).toLocaleDateString()}
                                </Badge>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="container mx-auto max-w-5xl -mt-8 px-4">
                <Tabs defaultValue="profile" className="space-y-6">
                    <TabsList className="bg-white/80 backdrop-blur border-2 border-[#2E6091]/10 p-1 rounded-2xl shadow-lg w-full md:w-auto h-auto flex flex-wrap">
                        <TabsTrigger value="profile" className="rounded-xl px-6 py-3 data-[state=active]:bg-[#2E6091] data-[state=active]:text-white">
                            <User className="w-4 h-4 mr-2" /> {isOwnProfile ? 'My Profile' : 'User Profile'}
                        </TabsTrigger>
                        {isOwnProfile && (
                            <>
                                <TabsTrigger value="support" className="rounded-xl px-6 py-3 data-[state=active]:bg-[#2E6091] data-[state=active]:text-white">
                                    <LifeBuoy className="w-4 h-4 mr-2" /> Support Center
                                </TabsTrigger>
                                <TabsTrigger value="activity" className="rounded-xl px-6 py-3 data-[state=active]:bg-[#2E6091] data-[state=active]:text-white">
                                    <TrendingUp className="w-4 h-4 mr-2" /> My Journey
                                </TabsTrigger>
                            </>
                        )}
                        <TabsTrigger value="listings" className="rounded-xl px-6 py-3 data-[state=active]:bg-[#2E6091] data-[state=active]:text-white">
                            <Package className="w-4 h-4 mr-2" /> {isOwnProfile ? 'My Ads' : 'Active Ads'}
                        </TabsTrigger>
                    </TabsList>

                    {/* Profile Maintenance */}
                    <TabsContent value="profile">
                        <Card className="border-0 shadow-xl rounded-3xl overflow-hidden bg-white/90 backdrop-blur">
                            <CardHeader className="border-b bg-gray-50/50">
                                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                    <div>
                                        <CardTitle className="text-2xl font-bold text-[#2E6091]">
                                            {isOwnProfile ? 'Profile Maintenance' : 'User Information'}
                                        </CardTitle>
                                        <CardDescription>
                                            {isOwnProfile
                                                ? 'Keep your information up to date so people can reach you easily.'
                                                : 'A little more about this member of the community.'}
                                        </CardDescription>
                                    </div>
                                    {isOwnProfile && (
                                        <div className="bg-[#2E6091]/5 rounded-2xl p-4 border border-[#2E6091]/10">
                                            <p className="text-xs font-bold text-[#2E6091] uppercase mb-3 flex items-center gap-2">
                                                <Palette className="w-3 h-3" /> Customize Your Look
                                            </p>
                                            <div className="flex gap-2">
                                                {avatarPresets.map((preset) => (
                                                    <button
                                                        key={preset.id}
                                                        onClick={() => handleAvatarClick(preset.value)}
                                                        className={`relative transition-all hover:scale-110 active:scale-95 rounded-xl overflow-hidden ring-offset-2 hover:ring-2 hover:ring-[#2E6091]/30 ${user?.avatar_url === preset.value ? 'ring-2 ring-[#2E6091]' : ''
                                                            }`}
                                                        title={preset.label}
                                                    >
                                                        <Avatar {...parseAvatarUrl(preset.value, user?.username)} size={32} />
                                                        {user?.avatar_url === preset.value && (
                                                            <div className="absolute inset-0 bg-black/10 flex items-center justify-center">
                                                                <div className="w-1.5 h-1.5 bg-white rounded-full shadow-sm" />
                                                            </div>
                                                        )}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="p-8">
                                <form onSubmit={handleUpdateProfile} className="space-y-6">
                                    <div className="grid md:grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <Label htmlFor="username" className="text-gray-600">Username</Label>
                                            <div className="relative">
                                                <Input id="username" value={user?.username} disabled className="bg-gray-100/50 border-gray-200" />
                                                {user?.is_verified && <ShieldCheck className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-green-500" />}
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="email" className="text-gray-600">Email Address</Label>
                                            <div className="relative">
                                                <Input id="email" value={user?.email} disabled className="bg-gray-100/50 border-gray-200" />
                                                <Mail className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="full_name" className="text-gray-600 font-semibold">Full Name</Label>
                                            <Input
                                                id="full_name"
                                                value={user?.full_name || ''}
                                                onChange={(e) => isOwnProfile && setUser({ ...user, full_name: e.target.value })}
                                                disabled={!isOwnProfile}
                                                className={`border-2 transition-all rounded-xl h-12 ${!isOwnProfile ? 'bg-gray-100/50 cursor-not-allowed' : 'focus:border-[#2E6091]'}`}
                                                placeholder="e.g. Ahmed Ali"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="phone" className="text-gray-600 font-semibold">Phone Number 📱</Label>
                                            <Input
                                                id="phone"
                                                value={user?.phone || ''}
                                                onChange={(e) => {
                                                    if (!isOwnProfile) return;
                                                    const val = e.target.value.replace(/\D/g, '').slice(0, 11);
                                                    setUser({ ...user, phone: val });
                                                }}
                                                disabled={!isOwnProfile}
                                                className={`border-2 transition-all rounded-xl h-12 ${!isOwnProfile ? 'bg-gray-100/50 cursor-not-allowed' : 'focus:border-[#2E6091]'}`}
                                                placeholder="03XXXXXXXXX"
                                                maxLength={11}
                                            />
                                            {isOwnProfile && <p className="text-[11px] text-[#2E6091] font-medium italic">Enter 11 digits (e.g., 03018738298) for easy buyer contact!</p>}
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="location" className="text-gray-600 font-semibold">Primary Location 📍</Label>
                                        <Select
                                            value={user?.location || 'Islamabad'}
                                            onValueChange={(value) => isOwnProfile && setUser({ ...user, location: value })}
                                            disabled={!isOwnProfile}
                                        >
                                            <SelectTrigger className="border-2 focus:border-[#2E6091] transition-all rounded-xl h-12">
                                                <SelectValue placeholder="Select location" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Islamabad">Islamabad</SelectItem>
                                                <SelectItem value="Rawalpindi">Rawalpindi</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <p className="text-[11px] text-[#2E6091] font-medium italic">Service limited to Twin Cities for maximum quality! 🚀</p>
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="bio" className="text-gray-600 font-semibold">About You (Bio) ✨</Label>
                                        <Textarea
                                            id="bio"
                                            value={user?.bio || ''}
                                            onChange={(e) => isOwnProfile && setUser({ ...user, bio: e.target.value })}
                                            disabled={!isOwnProfile}
                                            className={`border-2 transition-all rounded-xl min-h-[120px] resize-none ${!isOwnProfile ? 'bg-gray-100/50 cursor-not-allowed' : 'focus:border-[#2E6091]'}`}
                                            placeholder={isOwnProfile ? "Share a bit about yourself or your trading style..." : "This user hasn't shared a bio yet."}
                                        />
                                    </div>

                                    {isOwnProfile && (
                                        <div className="flex justify-end pt-4">
                                            <Button type="submit" disabled={saving} className="bg-[#2E6091] hover:bg-[#1E4166] text-white rounded-xl px-10 h-14 text-lg font-bold shadow-lg shadow-[#2E6091]/20 transition-all hover:scale-[1.02]">
                                                {saving ? 'Saving Changes...' : 'Save Profile Changes'}
                                            </Button>
                                        </div>
                                    )}
                                </form>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* Support Center */}
                    <TabsContent value="support" className="space-y-6">
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Contact Support Form */}
                            <Card className="border-0 shadow-xl rounded-3xl overflow-hidden bg-white/90 backdrop-blur border-t-4 border-t-blue-500">
                                <CardHeader>
                                    <div className="flex items-center gap-3">
                                        <div className="p-3 bg-blue-50 rounded-2xl">
                                            <LifeBuoy className="w-6 h-6 text-blue-600" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-xl">Contact Support</CardTitle>
                                            <CardDescription>Need help with a deal or account?</CardDescription>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="support-subject">Subject</Label>
                                        <Input
                                            id="support-subject"
                                            placeholder="What do you need help with?"
                                            value={supportForm.subject}
                                            onChange={(e) => setSupportForm({ ...supportForm, subject: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="support-desc">Message</Label>
                                        <Textarea
                                            id="support-desc"
                                            placeholder="Tell us more details..."
                                            className="min-h-[100px]"
                                            value={supportForm.description}
                                            onChange={(e) => setSupportForm({ ...supportForm, description: e.target.value })}
                                        />
                                    </div>
                                    <Button onClick={() => handleSubmitTicket('support')} disabled={saving} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-6 rounded-2xl font-bold">
                                        Send Help Request
                                    </Button>
                                </CardContent>
                            </Card>

                            {/* Bug Reporter Form */}
                            <Card className="border-0 shadow-xl rounded-3xl overflow-hidden bg-white/90 backdrop-blur border-t-4 border-t-red-500">
                                <CardHeader>
                                    <div className="flex items-center gap-3">
                                        <div className="p-3 bg-red-50 rounded-2xl">
                                            <Bug className="w-6 h-6 text-red-600" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-xl">Report a Bug</CardTitle>
                                            <CardDescription>Found something broken? Tell us!</CardDescription>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="bug-subject">Issue Catchy Title</Label>
                                        <Input
                                            id="bug-subject"
                                            placeholder="e.g. Image upload is slow"
                                            value={supportForm.subject}
                                            onChange={(e) => setSupportForm({ ...supportForm, subject: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="bug-desc">Describe the Chaos</Label>
                                        <Textarea
                                            id="bug-desc"
                                            placeholder="How did it happen? What did you see?"
                                            className="min-h-[100px]"
                                            value={supportForm.description}
                                            onChange={(e) => setSupportForm({ ...supportForm, description: e.target.value })}
                                        />
                                    </div>
                                    <Button onClick={() => handleSubmitTicket('bug')} disabled={saving} className="w-full bg-red-600 hover:bg-red-700 text-white py-6 rounded-2xl font-bold">
                                        File Bug Report
                                    </Button>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Ticket History */}
                        <Card className="border-0 shadow-xl rounded-3xl overflow-hidden bg-white/90 backdrop-blur">
                            <CardHeader className="flex flex-row items-center justify-between">
                                <div>
                                    <CardTitle className="text-xl flex items-center gap-2">
                                        <History className="w-5 h-5 text-gray-400" /> Request History
                                    </CardTitle>
                                    <CardDescription>Follow up on your tickets and bug reports.</CardDescription>
                                </div>
                                <Badge variant="outline" className="px-3 py-1">{tickets.length} total</Badge>
                            </CardHeader>
                            <CardContent>
                                {tickets.length === 0 ? (
                                    <div className="text-center py-12 text-gray-400">
                                        No history found. Everything looks perfect! ✨
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {tickets.map((ticket) => (
                                            <div key={ticket.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl border border-gray-100">
                                                <div className="flex items-center gap-4">
                                                    <div className={`p-2 rounded-xl ${ticket.ticket_type === 'bug' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>
                                                        {ticket.ticket_type === 'bug' ? <Bug className="w-4 h-4" /> : <LifeBuoy className="w-4 h-4" />}
                                                    </div>
                                                    <div>
                                                        <p className="font-semibold text-gray-900">{ticket.subject}</p>
                                                        <p className="text-xs text-gray-500">Submitted on {new Date(ticket.created_at).toLocaleDateString()}</p>
                                                    </div>
                                                </div>
                                                <Badge className={`${ticket.status === 'open' ? 'bg-yellow-100 text-yellow-700 border-yellow-200' :
                                                    ticket.status === 'closed' ? 'bg-green-100 text-green-700 border-green-200' :
                                                        'bg-gray-100 text-gray-700 border-gray-200'
                                                    } border-2`}>
                                                    {ticket.status.toUpperCase()}
                                                </Badge>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* Activity/Journey Tab */}
                    <TabsContent value="activity">
                        <div className="grid md:grid-cols-3 gap-6">
                            <Card className="col-span-1 border-0 shadow-xl rounded-3xl bg-gradient-to-br from-[#2E6091] to-[#2d5a18] text-white">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2"><Award className="w-5 h-5 text-yellow-400" /> Achievement</CardTitle>
                                </CardHeader>
                                <CardContent className="text-center space-y-4 py-6">
                                    <div className="w-24 h-24 bg-white/10 rounded-full flex items-center justify-center mx-auto ring-4 ring-white/20">
                                        <Heart className="w-12 h-12 text-pink-400 fill-current" />
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-bold">Top Saver</h3>
                                        <p className="text-white/70 text-sm">You have favorited {stats?.total_favorites || 0} items! You have eye for excellence.</p>
                                    </div>
                                </CardContent>
                            </Card>

                            <div className="col-span-2 space-y-6">
                                <Card className="border-0 shadow-xl rounded-3xl bg-white/90 backdrop-blur">
                                    <CardHeader>
                                        <CardTitle>Wholesome Activity Stats</CardTitle>
                                        <CardDescription>A summary of your interaction with the EZSell community.</CardDescription>
                                    </CardHeader>
                                    <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 pb-8">
                                        <div className="p-4 bg-blue-50 rounded-2xl text-center space-y-1">
                                            <p className="text-2xl font-bold text-blue-700">{stats?.total_views || 0}</p>
                                            <p className="text-xs text-blue-600 font-medium">Items Viewed</p>
                                        </div>
                                        <div className="p-4 bg-green-50 rounded-2xl text-center space-y-1">
                                            <p className="text-2xl font-bold text-green-700">{stats?.total_searches || 0}</p>
                                            <p className="text-xs text-green-600 font-medium">Smart Searches</p>
                                        </div>
                                        <div className="p-4 bg-pink-50 rounded-2xl text-center space-y-1">
                                            <p className="text-2xl font-bold text-pink-700">{stats?.total_favorites || 0}</p>
                                            <p className="text-xs text-pink-600 font-medium">Favorites</p>
                                        </div>
                                        <div className="p-4 bg-purple-50 rounded-2xl text-center space-y-1">
                                            <p className="text-2xl font-bold text-purple-700">{stats?.total_messages || 0}</p>
                                            <p className="text-xs text-purple-600 font-medium">Connections</p>
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card className="border-0 shadow-xl rounded-3xl bg-white/90 backdrop-blur overflow-hidden">
                                    <CardHeader className="bg-gradient-to-r from-orange-50 to-orange-100">
                                        <CardTitle className="text-orange-900">Your Impact</CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-6">
                                        <div className="flex items-center gap-6">
                                            <div className="p-4 bg-orange-600 text-white rounded-3xl shadow-lg ring-4 ring-orange-200">
                                                <CheckCircle2 className="w-8 h-8" />
                                            </div>
                                            <div className="space-y-1">
                                                <p className="text-lg font-bold text-orange-900">Making a Difference</p>
                                                <p className="text-gray-600 text-sm">
                                                    By participating in our marketplace, you've contributed to a more sustainable local economy. Thank you for being a part of EZSell!
                                                </p>
                                                <Button variant="link" className="text-orange-600 p-0 h-auto font-bold flex items-center gap-1">
                                                    View details <ArrowRight className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="listings">
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 pb-20">
                            {userListings.length === 0 ? (
                                <Card className="col-span-full border-0 shadow-xl rounded-2xl overflow-hidden bg-white/90 backdrop-blur py-20 text-center">
                                    <div className="flex flex-col items-center gap-4 text-gray-400">
                                        <Package className="w-16 h-16 opacity-20" />
                                        <div>
                                            <p className="text-xl font-bold">No ads found</p>
                                            <p className="text-sm">This user hasn't posted any listings yet.</p>
                                        </div>
                                        {isOwnProfile && (
                                            <Button
                                                onClick={() => navigate('/create-listing')}
                                                className="bg-[#2E6091] text-white rounded-xl px-8 mt-4"
                                            >
                                                Create Your First Ad
                                            </Button>
                                        )}
                                    </div>
                                </Card>
                            ) : (
                                userListings.map((listing) => {
                                    let images = [];
                                    try {
                                        images = typeof listing.images === 'string' ? JSON.parse(listing.images) : (listing.images || []);
                                    } catch (e) {
                                        images = [];
                                    }
                                    const mainImg = images.length > 0 ? getImageUrl(images[0]) : '/placeholder.png';
                                    return (
                                        <Card
                                            key={listing.id}
                                            className="border-0 shadow-lg rounded-2xl overflow-hidden bg-white/90 backdrop-blur transition-all hover:scale-[1.03] cursor-pointer group"
                                            onClick={() => navigate(`/product/${listing.id}`)}
                                        >
                                            <div className="aspect-[4/3] overflow-hidden relative">
                                                <img
                                                    src={mainImg}
                                                    alt={listing.title}
                                                    className="w-full h-full object-cover transition-transform group-hover:scale-110"
                                                />
                                                <div className="absolute top-3 left-3 flex gap-2">
                                                    <Badge className="bg-white/90 text-gray-900 border-0 backdrop-blur text-[10px] py-0 px-2 h-5">
                                                        {listing.category}
                                                    </Badge>
                                                    <Badge className={`${listing.approval_status === 'approved' ? 'bg-green-500/90' : 'bg-yellow-500/90'} text-white border-0 backdrop-blur capitalize text-[10px] py-0 px-2 h-5`}>
                                                        {listing.approval_status}
                                                    </Badge>
                                                </div>
                                            </div>
                                            <CardContent className="p-4">
                                                <h3 className="font-bold text-gray-900 line-clamp-1 mb-2">{listing.title}</h3>
                                                <div className="flex items-baseline gap-1 text-[#2E6091] mb-4">
                                                    <span className="text-[10px] font-bold uppercase opacity-60">Rs</span>
                                                    <span className="text-xl font-black">{listing.price.toLocaleString()}</span>
                                                </div>
                                                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                                                    <div className="flex items-center gap-1.5 text-[10px] text-gray-400 font-medium">
                                                        <Clock className="w-3 h-3" />
                                                        {new Date(listing.created_at).toLocaleDateString()}
                                                    </div>
                                                    <div className="bg-gray-50 px-2 py-0.5 rounded text-[9px] font-bold text-gray-500 uppercase">
                                                        {listing.condition}
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    );
                                })
                            )}
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
}
