import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { Users, Package, TrendingUp, ShoppingBag, Trash2, Ban, CheckCircle, Home } from 'lucide-react';
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
}

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [listings, setListings] = useState<Listing[]>([]);
  const [pendingListings, setPendingListings] = useState<any[]>([]);
  const [searchUser, setSearchUser] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; type: 'user' | 'listing'; id: number; name: string }>({ 
    open: false, 
    type: 'user', 
    id: 0, 
    name: '' 
  });
  const navigate = useNavigate();
  const { toast } = useToast();

  const apiClient = {
    get: async (url: string) => {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:8000/api/v1${url}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Admin access required');
        }
        throw new Error('Failed to fetch data');
      }
      return response.json();
    },
    delete: async (url: string) => {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:8000/api/v1${url}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to delete');
      return response.json();
    },
    patch: async (url: string) => {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:8000/api/v1${url}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Failed to update');
      return response.json();
    },
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [analyticsData, usersData, listingsData, pendingData] = await Promise.all([
        apiClient.get('/admin/analytics'),
        apiClient.get('/admin/users?limit=50'),
        apiClient.get('/listings?limit=50'),
        apiClient.get('/admin/pending-listings'),
      ]);
      
      setAnalytics(analyticsData);
      setUsers(usersData);
      setListings(listingsData);
      setPendingListings(pendingData);
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
      await apiClient.delete(`/admin/users/${deleteDialog.id}`);
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
      await apiClient.delete(`/admin/listings/${deleteDialog.id}`);
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
      const result = await apiClient.patch(`/admin/users/${user.id}/toggle-active`);
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
      const token = localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:8000/api/v1/admin/approve-listing/${listingId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to approve listing');
      
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
      const token = localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:8000/api/v1/admin/reject-listing/${listingId}?reason=${encodeURIComponent(reason)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to reject listing');
      
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

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchUser.toLowerCase()) ||
    user.email.toLowerCase().includes(searchUser.toLowerCase()) ||
    (user.full_name && user.full_name.toLowerCase().includes(searchUser.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <p className="text-center">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => navigate('/')} className="mb-4 text-[#143109] hover:bg-[#143109]/10">
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <p className="text-gray-600">Manage users, listings, and view analytics</p>
        </div>

        {/* Analytics Cards */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
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
                  <div key={listing.id} className="p-4 hover:bg-gray-50">
                    <div className="flex gap-4">
                      {listing.image_url && (
                        <img 
                          src={`http://localhost:8000${listing.image_url}`}
                          alt={listing.title}
                          className="w-24 h-24 object-cover rounded"
                        />
                      )}
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
                        <div className="flex gap-2">
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
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Category Statistics */}
        {analytics && analytics.categories.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Listings by Category</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 flex-wrap">
                {analytics.categories.map(cat => (
                  <Badge key={cat.name} variant="secondary" className="text-sm px-4 py-2">
                    {cat.name}: {cat.count}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
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
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">{user.username}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
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
                          <div className="flex gap-2 justify-end">
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
        <Card>
          <CardHeader>
            <CardTitle>Listings Management</CardTitle>
            <CardDescription>View and manage all product listings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
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
                      <TableRow key={listing.id}>
                        <TableCell className="font-medium">{listing.title}</TableCell>
                        <TableCell>PKR {listing.price.toLocaleString()}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{listing.category}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={listing.is_sold ? "secondary" : "default"}>
                            {listing.is_sold ? 'Sold' : 'Available'}
                          </Badge>
                        </TableCell>
                        <TableCell>{new Date(listing.created_at).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => setDeleteDialog({ open: true, type: 'listing', id: listing.id, name: listing.title })}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
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
    </div>
  );
}
