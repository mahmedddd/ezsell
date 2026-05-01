import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { Users, Package, TrendingUp, ShoppingBag, Trash2, Ban, CheckCircle, Home, AlertCircle, RotateCw, Sparkles, ExternalLink, MapPin, Phone, Mail, Calendar, Info, ShieldAlert, Award, User as UserIcon, LifeBuoy, Bug, MessageSquare } from 'lucide-react';
import { getImageUrl, adminService, listingService, supportService } from './lib/api.ts';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

interface Analytics {
  users: {
    total: number;
    active: number;
    verified: number;
    recent: number;
  };
  listings: {
    total: number;
    active: number;
    sold: number;
    recent: number;
  };
  categories: Array<{ name: string; count: number }>;
}

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  created_at: string;
}

interface Listing {
  id: number;
  title: string;
  price: number;
  category: string;
  condition: string;
  is_sold: boolean;
  created_at: string;
  owner_id: number;
  fraud_flags?: string;
  listing_hash?: string;
  predicted_price?: number;
  images?: string;
  additional_images?: string;
  views: number;
  description?: string;
  location?: string;
  is_featured?: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#A28D00'];

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [listings, setListings] = useState<Listing[]>([]);
  const [allListings, setAllListings] = useState<Listing[]>([]); // for charts (includes pending/rejected)
  const [pendingListings, setPendingListings] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [searchUser, setSearchUser] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; type: 'user' | 'listing'; id: number; name: string }>({
    open: false,
    type: 'user',
    id: 0,
    name: ''
  });
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [isUserSheetOpen, setIsUserSheetOpen] = useState(false);
  const [isListingSheetOpen, setIsListingSheetOpen] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [analyticsData, usersData, allListingsData, pendingData, ticketsData] = await Promise.all([
        adminService.getAnalytics(),
        adminService.getUsers({ limit: 50 }),
        adminService.getAllListings({ limit: 200 }),
        adminService.getPendingListings(),
        supportService.getAllTickets(),
      ]);

      setAnalytics(analyticsData);
      setUsers(usersData);
      setListings(allListingsData);   // table
      setAllListings(allListingsData); // charts
      setPendingListings(pendingData);
      setTickets(ticketsData);
    } catch (error: any) {
      if (error.message === 'Admin access required') {
        toast({
          title: 'Access Denied',
          description: 'You do not have admin privileges',
          variant: 'destructive',
        });
        navigate('/dashboard');
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load admin data',
          variant: 'destructive',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    try {
      await adminService.deleteUser(deleteDialog.id);
      toast({
        title: 'User Deleted',
        description: `User ${deleteDialog.name} has been removed`,
      });
      setUsers(users.filter(u => u.id !== deleteDialog.id));
      setDeleteDialog({ ...deleteDialog, open: false });
      fetchData(); // Refresh analytics
    } catch (error) {
      toast({
        title: 'Delete Failed',
        description: 'Could not delete user',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteListing = async () => {
    try {
      await adminService.deleteListing(deleteDialog.id);
      toast({
        title: 'Listing Deleted',
        description: `Listing "${deleteDialog.name}" has been removed`,
      });
      setListings(listings.filter(l => l.id !== deleteDialog.id));
      setDeleteDialog({ ...deleteDialog, open: false });
      fetchData(); // Refresh analytics
    } catch (error) {
      toast({
        title: 'Delete Failed',
        description: 'Could not delete listing',
        variant: 'destructive',
      });
    }
  };

  const handleToggleUserActive = async (user: User) => {
    try {
      const result = await adminService.toggleUserActive(user.id);
      toast({
        title: 'Status Updated',
        description: result.message,
      });
      setUsers(users.map(u => u.id === user.id ? { ...u, is_active: result.is_active } : u));
      fetchData(); // Refresh analytics
    } catch (error) {
      toast({
        title: 'Update Failed',
        description: 'Could not update user status',
        variant: 'destructive',
      });
    }
  };

  const handleApproveListing = async (listingId: number, title: string) => {
    try {
      await adminService.approveListing(listingId);

      toast({
        title: 'Listing Approved',
        description: `"${title}" has been approved and is now live`,
      });

      setPendingListings(pendingListings.filter(l => l.id !== listingId));
      fetchData();
    } catch (error) {
      toast({
        title: 'Approval Failed',
        description: 'Could not approve listing',
        variant: 'destructive',
      });
    }
  };

  const handleRejectListing = async (listingId: number, title: string) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;

    try {
      await adminService.rejectListing(listingId, reason);

      toast({
        title: 'Listing Rejected',
        description: `"${title}" has been rejected`,
      });

      setPendingListings(pendingListings.filter(l => l.id !== listingId));
      fetchData();
    } catch (error) {
      toast({
        title: 'Rejection Failed',
        description: 'Could not reject listing',
        variant: 'destructive',
      });
    }
  };

  const handleUpdateTicketStatus = async (ticketId: number, status: string) => {
    try {
      await supportService.updateTicketStatus(ticketId, status);
      toast({
        title: 'Ticket Updated',
        description: `Status changed to ${status}`,
      });
      fetchData();
    } catch (error) {
      toast({
        title: 'Update Failed',
        description: 'Could not update ticket status',
        variant: 'destructive',
      });
    }
  };

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchUser.toLowerCase()) ||
    user.email.toLowerCase().includes(searchUser.toLowerCase()) ||
    (user.full_name && user.full_name.toLowerCase().includes(searchUser.toLowerCase()))
  );

  const getBarChartData = () => {
    if (!analytics) return [];
    return [
      { name: 'Users', Total: analytics.users.total, Active: analytics.users.active },
      { name: 'Listings', Total: analytics.listings.total, Active: analytics.listings.active },
    ];
  };

  const getFraudHotspotsData = () => {
    const flagCounts: Record<string, number> = {};
    allListings.forEach(listing => {
      if (listing.fraud_flags) {
        try {
          const flags = typeof listing.fraud_flags === 'string' ? JSON.parse(listing.fraud_flags) : listing.fraud_flags;
          if (Array.isArray(flags)) {
            flags.forEach((f: string) => {
              const name = f.replace(/_/g, ' ');
              flagCounts[name] = (flagCounts[name] || 0) + 1;
            });
          }
        } catch (e) { }
      }
    });

    return Object.entries(flagCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  };

  const getPricingAccuracyData = () => {
    const categories: Record<string, { total_diff: number, count: number }> = {};
    allListings.forEach(l => {
      if (l.predicted_price && l.price) {
        if (!categories[l.category]) categories[l.category] = { total_diff: 0, count: 0 };
        const diffPercent = Math.abs(l.price - l.predicted_price) / l.predicted_price;
        categories[l.category].total_diff += (1 - diffPercent) * 100;
        categories[l.category].count += 1;
      }
    });

    return Object.entries(categories)
      .map(([name, data]) => ({
        name,
        accuracy: Math.max(0, Math.round(data.total_diff / data.count))
      }))
      .sort((a, b) => b.accuracy - a.accuracy);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-transparent">
        <div className="container mx-auto px-4 py-8">
          <p className="text-center">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-transparent">

      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => navigate('/')} className="mb-4 text-[#143109] hover:bg-[#143109]/10">
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
            <p className="text-gray-600">Manage users, listings, and view analytics</p>
          </div>
          <Button onClick={fetchData} variant="outline" className="flex items-center gap-2">
            <RotateCw className="h-4 w-4" />
            Refresh Data
          </Button>
        </div>

        {/* Analytics Cards */}
        {analytics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.users.total}</div>
                <p className="text-xs text-muted-foreground">
                  {analytics.users.recent} new this week
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.users.active}</div>
                <p className="text-xs text-muted-foreground">
                  {analytics.users.verified} verified
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Listings</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.listings.total}</div>
                <p className="text-xs text-muted-foreground">
                  {analytics.listings.recent} new this week
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Listings</CardTitle>
                <ShoppingBag className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.listings.active}</div>
                <p className="text-xs text-muted-foreground">
                  {analytics.listings.sold} sold
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Support Requests</CardTitle>
                <LifeBuoy className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{tickets.length}</div>
                <p className="text-xs text-muted-foreground">
                  {tickets.filter(t => t.status === 'open').length} new tickets
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Pending Listings for Approval */}
        {pendingListings.length > 0 && (
          <Card className="mb-8 border-2 border-yellow-300">
            <CardHeader className="bg-yellow-50">
              <CardTitle className="text-xl flex items-center gap-2">
                <Badge className="bg-yellow-500">{pendingListings.length}</Badge>
                Listings Pending Approval
              </CardTitle>
              <CardDescription>
                These listings have prices that differ significantly from AI predictions and require your review
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {pendingListings.map((listing: any) => (
                  <div
                    key={listing.id}
                    className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => {
                      setSelectedListing(listing);
                      setIsListingSheetOpen(true);
                    }}
                  >
                    <div className="flex gap-4">
                      {(() => {
                        const imgs = listing.images ? (() => { try { return JSON.parse(listing.images); } catch { return []; } })() : [];
                        return imgs[0] ? (
                          <img
                            src={getImageUrl(imgs[0])}
                            alt={listing.title}
                            className="w-24 h-24 object-cover rounded"
                          />
                        ) : null;
                      })()}
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg">{listing.title}</h3>
                        <p className="text-sm text-gray-600 mb-2">
                          by {listing.owner.username} ({listing.owner.email})
                        </p>
                        <div className="grid grid-cols-2 gap-2 text-sm mb-2">
                          <div>
                            <span className="text-gray-600">Listed Price:</span>
                            <span className="font-bold ml-2">PKR {listing.price.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">AI Prediction:</span>
                            <span className="font-bold ml-2">PKR {listing.predicted_price?.toLocaleString()}</span>
                          </div>
                        </div>
                        <div className="mb-2">
                          <Badge variant={listing.price_difference > 0 ? "destructive" : "default"}>
                            {listing.price_difference > 0 ? '+' : ''}{listing.price_difference?.toLocaleString()} PKR difference
                          </Badge>
                          <Badge variant="outline" className="ml-2">{listing.category}</Badge>
                          <Badge variant="outline" className="ml-2">{listing.condition}</Badge>
                        </div>
                        <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                          <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                            onClick={() => handleApproveListing(listing.id, listing.title)}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleRejectListing(listing.id, listing.title)}
                          >
                            <Ban className="h-4 w-4 mr-1" />
                            Reject
                          </Button>
                        </div>

                        {/* Fraud Flags Section */}
                        {listing.fraud_flags && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {(() => {
                              try {
                                const flags = typeof listing.fraud_flags === 'string'
                                  ? JSON.parse(listing.fraud_flags)
                                  : listing.fraud_flags;
                                if (Array.isArray(flags)) {
                                  return flags.map((flag: string) => (
                                    <Badge key={flag} variant="destructive" className="bg-red-100 text-red-800 border-red-200">
                                      ⚠️ {flag.replace(/_/g, ' ')}
                                    </Badge>
                                  ));
                                }
                              } catch (e) {
                                return <Badge variant="destructive">⚠️ Fraud Flags detected</Badge>;
                              }
                            })()}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Visual Analytics Charts */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            {/* Category Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Inventory by Category</CardTitle>
                <CardDescription>Visual breakdown of current listings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analytics.categories}
                        dataKey="count"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        innerRadius={50}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        paddingAngle={5}
                      >
                        {analytics.categories.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value, name, props) => [`${value} listings`, name]} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Platform Health Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Platform Health Overview</CardTitle>
                <CardDescription>Total vs Active metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={getBarChartData()} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="Total" fill="#8884d8" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Active" fill="#82ca9d" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Fraud Hotspots */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-red-600" />
                  Fraud Hotspots
                </CardTitle>
                <CardDescription>Most frequent listing flags detected by AI</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 p-3 bg-red-50 rounded-lg text-[10px] text-red-800 border border-red-100 italic">
                  Hotspots represent platform-wide trends of suspicious activity.
                  Higher counts indicate common fraudulent patterns (e.g., duplicated listings from same IP or unrealistic pricing)
                  that require automated or manual moderation.
                </div>
                {getFraudHotspotsData().length === 0 ? (
                  <div className="h-64 flex flex-col items-center justify-center text-gray-400 gap-2">
                    <ShieldAlert className="h-10 w-10 text-green-300" />
                    <p className="text-sm font-medium text-green-600">No fraud flags detected</p>
                    <p className="text-xs text-gray-400">All listings are clean so far 🎉</p>
                  </div>
                ) : (
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getFraudHotspotsData()} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                        <XAxis type="number" hide />
                        <YAxis dataKey="name" type="category" width={100} fontSize={10} />
                        <Tooltip cursor={{ fill: 'transparent' }} />
                        <Bar dataKey="count" fill="#ef4444" radius={[0, 4, 4, 0]} name="Flag Occurrences" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* AI Pricing Accuracy */}
            <Card>
              <CardHeader>
                <CardTitle>AI pricing Accuracy</CardTitle>
                <CardDescription>Average prediction confidence by category</CardDescription>
              </CardHeader>
              <CardContent>
                {getPricingAccuracyData().length === 0 ? (
                  <div className="h-72 flex flex-col items-center justify-center text-gray-400 gap-2">
                    <TrendingUp className="h-10 w-10 text-blue-200" />
                    <p className="text-sm font-medium text-gray-500">No pricing data yet</p>
                    <p className="text-xs text-gray-400">Accuracy will appear once listings with AI predictions are posted</p>
                  </div>
                ) : (
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getPricingAccuracyData()}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                        <XAxis dataKey="name" fontSize={10} />
                        <YAxis domain={[0, 100]} />
                        <Tooltip formatter={(val) => [`${val}%`, 'Accuracy']} />
                        <Bar dataKey="accuracy" fill="#10b981" radius={[4, 4, 0, 0]} name="Accuracy %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Users Management */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Users Management</CardTitle>
            <CardDescription>View and manage all registered users</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Input
                placeholder="Search users by username, email, or name..."
                value={searchUser}
                onChange={(e) => setSearchUser(e.target.value)}
              />
            </div>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Username</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground">
                        No users found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredUsers.map((user) => (
                      <TableRow
                        key={user.id}
                        className="cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => {
                          setSelectedUser(user);
                          setIsUserSheetOpen(true);
                        }}
                      >
                        <TableCell className="font-medium">{user.username}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                            <Badge variant={user.is_active ? "default" : "secondary"}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                            {user.is_verified && (
                              <Badge variant="outline" className="text-green-600">
                                Verified
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {user.is_admin ? (
                            <Badge variant="destructive">Admin</Badge>
                          ) : (
                            <Badge variant="outline">User</Badge>
                          )}
                        </TableCell>
                        <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleToggleUserActive(user)}
                              disabled={user.is_admin}
                            >
                              {user.is_active ? <Ban className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => setDeleteDialog({ open: true, type: 'user', id: user.id, name: user.username })}
                              disabled={user.is_admin}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Listings Management */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Listings Management</CardTitle>
            <CardDescription>View and manage all product listings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">Image</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Clicks</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {listings.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground">
                        No listings found
                      </TableCell>
                    </TableRow>
                  ) : (
                    listings.map((listing) => (
                      <TableRow
                        key={listing.id}
                        className="cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => {
                          setSelectedListing(listing);
                          setIsListingSheetOpen(true);
                        }}
                      >
                        <TableCell>
                          {(() => {
                            const imgs = listing.images ? (() => { try { return JSON.parse(listing.images); } catch { return []; } })() : [];
                            return imgs[0] ? (
                              <img
                                src={getImageUrl(imgs[0])}
                                alt={listing.title}
                                className="w-12 h-12 object-cover rounded bg-gray-100"
                              />
                            ) : (
                              <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                                <Package className="h-6 w-6 text-gray-400" />
                              </div>
                            );
                          })()}
                        </TableCell>
                        <TableCell className="font-medium">
                          <div className="flex flex-col">
                            <span>{listing.title}</span>
                            {listing.is_featured && <span className="text-[10px] text-yellow-600 font-bold uppercase">Featured</span>}
                          </div>
                        </TableCell>
                        <TableCell>PKR {listing.price.toLocaleString()}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{listing.category}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <Badge variant={listing.is_sold ? "secondary" : "default"}>
                              {listing.is_sold ? 'Sold' : 'Available'}
                            </Badge>
                            {(listing as any).approval_status && (listing as any).approval_status !== 'approved' && (
                              <Badge
                                variant="outline"
                                className={
                                  (listing as any).approval_status === 'pending'
                                    ? 'border-yellow-400 text-yellow-700 bg-yellow-50'
                                    : 'border-red-400 text-red-700 bg-red-50'
                                }
                              >
                                {(listing as any).approval_status === 'pending' ? '⏳ Pending' : '❌ Rejected'}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3 text-green-600" />
                            {listing.views || 0}
                          </div>
                        </TableCell>
                        <TableCell>{new Date(listing.created_at).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          <div onClick={(e) => e.stopPropagation()}>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => setDeleteDialog({ open: true, type: 'listing', id: listing.id, name: listing.title })}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Support & Bug Reports Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LifeBuoy className="h-5 w-5 text-blue-600" />
              Support & Bug Reports
            </CardTitle>
            <CardDescription>Directly respond to user requests and issues</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50/50">
                    <TableHead>Type</TableHead>
                    <TableHead>User / Contact</TableHead>
                    <TableHead>Subject & Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tickets.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                        No support tickets or bug reports found
                      </TableCell>
                    </TableRow>
                  ) : (
                    tickets.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map((ticket) => (
                      <TableRow key={ticket.id} className="hover:bg-gray-50/50 transition-colors">
                        <TableCell>
                          <Badge variant={ticket.ticket_type === 'bug' ? "destructive" : "default"} className="flex w-fit items-center gap-1">
                            {ticket.ticket_type === 'bug' ? <Bug className="h-3 w-3" /> : <LifeBuoy className="h-3 w-3" />}
                            {ticket.ticket_type.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div
                            className="flex items-center gap-2 cursor-pointer group"
                            onClick={() => {
                              setSelectedUser(ticket.user);
                              setIsUserSheetOpen(true);
                            }}
                          >
                            <div className="w-8 h-8 rounded-full bg-[#143109] text-white flex items-center justify-center text-xs font-bold group-hover:ring-2 ring-[#143109]/20 transition-all">
                              {ticket.user?.username[0].toUpperCase()}
                            </div>
                            <div className="flex flex-col">
                              <span className="font-medium text-sm group-hover:text-[#143109] transition-colors">{ticket.user?.full_name || ticket.user?.username}</span>
                              <span className="text-[10px] text-gray-500">{ticket.user?.email}</span>
                              {ticket.user?.phone && <span className="text-[10px] text-blue-600 font-medium">{ticket.user.phone}</span>}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-[300px]">
                          <div className="flex flex-col gap-1">
                            <span className="font-bold text-sm">{ticket.subject}</span>
                            <span className="text-xs text-gray-600 line-clamp-2 italic">"{ticket.description}"</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={`${ticket.status === 'open' ? 'bg-yellow-100 text-yellow-700 border-yellow-200' :
                            ticket.status === 'working' ? 'bg-blue-100 text-blue-700 border-blue-200' :
                              'bg-green-100 text-green-700 border-green-200'
                            } border shadow-none`}>
                            {ticket.status.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-gray-500">
                          {new Date(ticket.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-2 justify-end">
                            {ticket.status !== 'working' && ticket.status !== 'done' && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-8 border-blue-200 text-blue-600 hover:bg-blue-50"
                                onClick={() => handleUpdateTicketStatus(ticket.id, 'working')}
                              >
                                <RotateCw className="h-3 w-3 mr-1" />
                                Working
                              </Button>
                            )}
                            {ticket.status !== 'done' && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-8 border-green-200 text-green-600 hover:bg-green-50"
                                onClick={() => handleUpdateTicketStatus(ticket.id, 'done')}
                              >
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Done
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ ...deleteDialog, open })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete {deleteDialog.type === 'user' ? 'user' : 'listing'} "{deleteDialog.name}".
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteDialog.type === 'user' ? handleDeleteUser : handleDeleteListing}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* User Detail Drawer */}
      <Sheet open={isUserSheetOpen} onOpenChange={setIsUserSheetOpen}>
        <SheetContent className="sm:max-w-md overflow-y-auto">
          <SheetHeader className="mb-6">
            <SheetTitle className="text-2xl font-bold flex items-center gap-2">
              <UserIcon className="h-6 w-6 text-[#143109]" />
              User Profile
            </SheetTitle>
            <SheetDescription>
              Managing account for "{selectedUser?.username}"
            </SheetDescription>
          </SheetHeader>

          {selectedUser && (
            <div className="space-y-6">
              <div className="flex flex-col items-center p-6 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                <div className="w-20 h-20 bg-[#143109] text-white rounded-full flex items-center justify-center text-3xl font-bold mb-4">
                  {selectedUser.username[0].toUpperCase()}
                </div>
                <h3 className="text-xl font-bold">{selectedUser.full_name || selectedUser.username}</h3>
                <p className="text-sm text-gray-500">{selectedUser.email}</p>
                <div className="flex gap-2 mt-4">
                  {selectedUser.is_admin && <Badge variant="destructive">Admin</Badge>}
                  {selectedUser.is_verified ? <Badge className="bg-green-100 text-green-800 border-green-200">Verified</Badge> : <Badge variant="secondary">Unverified</Badge>}
                  <Badge variant={selectedUser.is_active ? "default" : "secondary"}>
                    {selectedUser.is_active ? 'Active' : 'Suspended'}
                  </Badge>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-semibold text-gray-700 flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  Account Details
                </h4>
                <div className="grid grid-cols-1 gap-3">
                  <div className="flex items-center gap-3 p-3 bg-white rounded-xl border">
                    <Mail className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-[10px] text-gray-500 uppercase font-bold">Email Address</p>
                      <p className="text-sm">{selectedUser.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-white rounded-xl border">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-[10px] text-gray-500 uppercase font-bold">Member Since</p>
                      <p className="text-sm">{new Date(selectedUser.created_at).toLocaleDateString(undefined, { dateStyle: 'long' })}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t space-y-3">
                <h4 className="font-semibold text-gray-700">Management Actions</h4>
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleToggleUserActive(selectedUser)}
                    disabled={selectedUser.is_admin}
                  >
                    {selectedUser.is_active ? <Ban className="h-4 w-4 mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                    {selectedUser.is_active ? 'Suspend' : 'Activate'}
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={() => {
                      setIsUserSheetOpen(false);
                      setDeleteDialog({ open: true, type: 'user', id: selectedUser.id, name: selectedUser.username });
                    }}
                    disabled={selectedUser.is_admin}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </div>
                <Button variant="secondary" className="w-full" onClick={() => navigate(`/dashboard?user=${selectedUser.id}`)}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View User Listings
                </Button>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Listing Detail Drawer */}
      <Sheet open={isListingSheetOpen} onOpenChange={setIsListingSheetOpen}>
        <SheetContent className="sm:max-w-lg overflow-y-auto">
          <SheetHeader className="mb-6">
            <SheetTitle className="text-2xl font-bold flex items-center gap-2">
              <Package className="h-6 w-6 text-[#143109]" />
              Listing Details
            </SheetTitle>
            <SheetDescription>
              In-depth analysis for "{selectedListing?.title}"
            </SheetDescription>
          </SheetHeader>

          {selectedListing && (
            <div className="space-y-6">
              {/* Image Preview */}
              <div className="aspect-video bg-gray-100 rounded-2xl overflow-hidden border-2 border-gray-100 shadow-inner relative group">
                {(() => {
                  const imgs = selectedListing.images ? (() => { try { return JSON.parse(selectedListing.images); } catch { return []; } })() : [];
                  return imgs[0] ? (
                    <img
                      src={getImageUrl(imgs[0])}
                      alt={selectedListing.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <ShoppingBag className="h-12 w-12" />
                    </div>
                  );
                })()}
                <Badge className="absolute top-4 right-4 bg-black/60 backdrop-blur-md">
                  PKR {selectedListing.price.toLocaleString()}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-xl border">
                  <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Status</p>
                  <Badge variant={selectedListing.is_sold ? "secondary" : "default"}>
                    {selectedListing.is_sold ? 'Sold' : 'Active Listing'}
                  </Badge>
                </div>
                <div className="p-4 bg-gray-50 rounded-xl border">
                  <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Views</p>
                  <div className="flex items-center gap-2 font-bold text-lg">
                    <TrendingUp className="h-4 w-4 text-green-600" />
                    {selectedListing.views || 0}
                  </div>
                </div>
              </div>

              {/* AI Analysis Section */}
              <div className="p-5 bg-[#143109]/5 rounded-2xl border-2 border-[#143109]/10 space-y-4">
                <h4 className="font-bold text-[#143109] flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  AI Market Analysis
                </h4>
                <div className="grid grid-cols-1 gap-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Predicted Fair Price:</span>
                    <span className="font-bold">PKR {selectedListing.predicted_price?.toLocaleString() || 'N/A'}</span>
                  </div>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#143109]"
                      style={{ width: selectedListing.predicted_price ? `${Math.min((selectedListing.price / selectedListing.predicted_price) * 100, 100)}%` : '0%' }}
                    />
                  </div>
                  {selectedListing.fraud_flags && (
                    <div className="pt-2">
                      <p className="text-[10px] text-red-600 font-bold uppercase mb-2 flex items-center gap-1">
                        <ShieldAlert className="h-3 w-3" />
                        Risk Flags Detected
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {(() => {
                          try {
                            const flags = typeof selectedListing.fraud_flags === 'string' ? JSON.parse(selectedListing.fraud_flags) : selectedListing.fraud_flags;
                            return Array.isArray(flags) ? flags.map((f: string) => (
                              <Badge key={f} variant="destructive" className="text-[10px]">
                                {f.replace(/_/g, ' ')}
                              </Badge>
                            )) : null;
                          } catch { return null; }
                        })()}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-semibold text-gray-700">Listing Info</h4>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <MapPin className="h-4 w-4 text-gray-400 mt-1" />
                    <p className="text-sm text-gray-600">{selectedListing.location || 'Pakistan'}</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <Info className="h-4 w-4 text-gray-400 mt-1" />
                    <p className="text-sm text-gray-600 leading-relaxed line-clamp-4">
                      {selectedListing.description || 'No description provided.'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1 border-[#143109] text-[#143109] hover:bg-[#143109]/10"
                  onClick={() => navigate(`/product/${selectedListing.id}`)}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Page
                </Button>
                <Button
                  variant="destructive"
                  className="flex-1"
                  onClick={() => {
                    setIsListingSheetOpen(false);
                    setDeleteDialog({ open: true, type: 'listing', id: selectedListing.id, name: selectedListing.title });
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Remove
                </Button>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
