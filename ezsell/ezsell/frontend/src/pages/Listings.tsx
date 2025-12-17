import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { listingService, getImageUrl } from '@/lib/api';
import { Search, Filter, Home, X } from 'lucide-react';

export default function Listings() {
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 500000]);
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(true);
  
  const conditions = ['new', 'like-new', 'good', 'fair'];
  const brands = ['Apple', 'Samsung', 'Huawei', 'Oppo', 'Vivo', 'Xiaomi', 'Realme', 'OnePlus', 'Google', 'HP', 'Dell', 'Lenovo', 'Asus', 'Acer', 'MSI'];

  useEffect(() => {
    fetchListings();
  }, [category, selectedConditions, priceRange, selectedBrands]);

  const fetchListings = async () => {
    try {
      const params: any = {};
      if (category) params.category = category;
      if (search) params.search = search;
      if (priceRange[0] > 0) params.min_price = priceRange[0];
      if (priceRange[1] < 500000) params.max_price = priceRange[1];
      
      let data = await listingService.getAllListings(params);
      
      // Client-side filtering for conditions and brands
      if (selectedConditions.length > 0) {
        data = data.filter((listing: any) => selectedConditions.includes(listing.condition));
      }
      if (selectedBrands.length > 0) {
        data = data.filter((listing: any) => listing.brand && selectedBrands.includes(listing.brand));
      }
      
      setListings(data);
    } catch (error) {
      console.error('Failed to fetch listings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchListings();
  };

  const handleConditionChange = (condition: string, checked: boolean) => {
    setSelectedConditions(prev => 
      checked ? [...prev, condition] : prev.filter(c => c !== condition)
    );
  };

  const handleBrandChange = (brand: string, checked: boolean) => {
    setSelectedBrands(prev => 
      checked ? [...prev, brand] : prev.filter(b => b !== brand)
    );
  };

  const resetFilters = () => {
    setCategory('');
    setSelectedConditions([]);
    setPriceRange([0, 500000]);
    setSelectedBrands([]);
    setSearch('');
  };

  const activeFilterCount = selectedConditions.length + selectedBrands.length + (category ? 1 : 0) + (priceRange[0] > 0 || priceRange[1] < 500000 ? 1 : 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f5f0] to-[#e8e8dc]">
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => window.location.href = '/'} className="mb-4 text-[#143109] hover:bg-[#143109]/10">
          <Home className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
        
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Browse Listings</h1>
          
          {/* Search Bar */}
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            <Button variant="outline" onClick={() => setShowFilters(!showFilters)} className="lg:hidden">
              <Filter className="h-4 w-4 mr-2" />
              Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
            </Button>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Sidebar Filters */}
          <aside className={`${showFilters ? 'block' : 'hidden'} lg:block w-full lg:w-64 flex-shrink-0`}>
            <Card className="sticky top-4">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Filter className="h-5 w-5" />
                    Filters
                  </CardTitle>
                  {activeFilterCount > 0 && (
                    <Button variant="ghost" size="sm" onClick={resetFilters}>
                      <X className="h-4 w-4 mr-1" />
                      Clear
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Category Filter */}
                <div>
                  <Label className="text-sm font-semibold mb-3 block">Category</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Categories" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value=" ">All Categories</SelectItem>
                      <SelectItem value="mobile">Mobile</SelectItem>
                      <SelectItem value="laptop">Laptop</SelectItem>
                      <SelectItem value="furniture">Furniture</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Condition Filter */}
                <div>
                  <Label className="text-sm font-semibold mb-3 block">Condition</Label>
                  <div className="space-y-2">
                    {conditions.map((cond) => (
                      <div key={cond} className="flex items-center space-x-2">
                        <Checkbox
                          id={`condition-${cond}`}
                          checked={selectedConditions.includes(cond)}
                          onCheckedChange={(checked) => handleConditionChange(cond, checked as boolean)}
                        />
                        <label
                          htmlFor={`condition-${cond}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 capitalize cursor-pointer"
                        >
                          {cond}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Price Range Filter */}
                <div>
                  <Label className="text-sm font-semibold mb-3 block">Price Range</Label>
                  <div className="space-y-4">
                    <Slider
                      min={0}
                      max={500000}
                      step={5000}
                      value={priceRange}
                      onValueChange={(value) => setPriceRange(value as [number, number])}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>PKR {priceRange[0].toLocaleString()}</span>
                      <span>PKR {priceRange[1].toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                {/* Brand/Model Filter */}
                <div>
                  <Label className="text-sm font-semibold mb-3 block">Brand</Label>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {brands.map((brand) => (
                      <div key={brand} className="flex items-center space-x-2">
                        <Checkbox
                          id={`brand-${brand}`}
                          checked={selectedBrands.includes(brand)}
                          onCheckedChange={(checked) => handleBrandChange(brand, checked as boolean)}
                        />
                        <label
                          htmlFor={`brand-${brand}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                        >
                          {brand}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Active Filters Summary */}
                {activeFilterCount > 0 && (
                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground mb-2">
                      {activeFilterCount} active filter{activeFilterCount !== 1 ? 's' : ''}
                    </p>
                    <p className="text-sm font-semibold">
                      {listings.length} result{listings.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </aside>

          {/* Listings Grid */}
          <div className="flex-1">
            {loading ? (
              <div className="text-center py-12">
                <div className="text-lg text-slate-600">Loading listings...</div>
              </div>
            ) : listings.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Filter className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-xl font-semibold mb-2">No listings found</p>
                  <p className="text-muted-foreground mb-4">Try adjusting your filters or search terms</p>
                  {activeFilterCount > 0 && (
                    <Button onClick={resetFilters} variant="outline">
                      Clear all filters
                    </Button>
                  )}
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="mb-4 flex justify-between items-center">
                  <p className="text-sm text-muted-foreground">
                    Showing {listings.length} listing{listings.length !== 1 ? 's' : ''}
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {listings.map((listing) => (
                    <Link key={listing.id} to={`/product/${listing.id}`}>
                      <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                        <CardHeader>
                          <div className="aspect-video bg-slate-200 rounded-md mb-4 flex items-center justify-center relative">
                            {getImageUrl(listing.image_url) ? (
                              <img src={getImageUrl(listing.image_url)!} alt={listing.title} className="w-full h-full object-cover rounded-md" />
                            ) : (
                              <span className="text-slate-500">No image</span>
                            )}
                            {listing.additional_images && JSON.parse(listing.additional_images).length > 0 && (
                              <Badge className="absolute bottom-2 left-2 bg-black/70 text-white text-xs">
                                📷 {JSON.parse(listing.additional_images).length + 1}
                              </Badge>
                            )}
                          </div>
                          <div className="flex justify-between items-start mb-2">
                            <CardTitle className="text-lg line-clamp-1">{listing.title}</CardTitle>
                            <Badge variant="secondary" className="ml-2">{listing.category}</Badge>
                          </div>
                          <CardDescription className="line-clamp-2">{listing.description}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="flex justify-between items-center">
                            <span className="text-2xl font-bold text-primary">PKR {listing.price.toLocaleString()}</span>
                            <Badge variant="outline">{listing.condition}</Badge>
                          </div>
                          <div className="text-sm text-muted-foreground mt-2">
                            {listing.views} views
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
