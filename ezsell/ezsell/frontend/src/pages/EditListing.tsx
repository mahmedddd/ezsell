import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { listingService } from '@/lib/api';
import CreateListingFormNew from '@/components/CreateListingFormNew';
import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';

export default function EditListing() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    const fetchListing = async () => {
      if (!id) {
        navigate('/');
        return;
      }

      try {
        const data = await listingService.getListingById(parseInt(id));
        
        // Check if user is the owner
        if (data.owner_id !== currentUser?.id) {
          alert('You can only edit your own listings');
          navigate('/');
          return;
        }
        
        setListing(data);
      } catch (error) {
        console.error('Failed to fetch listing:', error);
        alert('Failed to load listing');
        navigate('/');
      } finally {
        setLoading(false);
      }
    };

    fetchListing();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex items-center justify-center">
        <div className="text-slate-900 text-xl font-semibold">Loading...</div>
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc] flex items-center justify-center">
        <div className="text-slate-900 text-xl font-semibold">Listing not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc]">
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => navigate(`/product/${id}`)} className="mb-4 text-[#143109] hover:bg-[#143109]/10">
          <Home className="mr-2 h-4 w-4" />
          Back to Listing
        </Button>
        
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Edit Listing</h1>
          <p className="text-slate-600">Update your listing information</p>
        </div>

        <CreateListingFormNew 
          editMode={true} 
          listingId={parseInt(id!)} 
          existingData={listing} 
        />
      </div>
    </div>
  );
}
