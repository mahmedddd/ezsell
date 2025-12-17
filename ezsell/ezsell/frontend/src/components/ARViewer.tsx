import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Upload, Eye, X, Loader2, Camera } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { arService } from '@/lib/api';

interface ARViewerProps {
  listingId: number;
  listingTitle: string;
  category: string;
}

export function ARViewer({ listingId, listingTitle, category }: ARViewerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [roomImage, setRoomImage] = useState<File | null>(null);
  const [roomImagePreview, setRoomImagePreview] = useState<string | null>(null);
  const [arPreviewUrl, setArPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Only show AR for furniture category
  if (category?.toLowerCase() !== 'furniture') {
    return null;
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast({
        title: "Invalid file type",
        description: "Please select an image file",
        variant: "destructive",
      });
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please select an image smaller than 10MB",
        variant: "destructive",
      });
      return;
    }

    setRoomImage(file);
    setRoomImagePreview(URL.createObjectURL(file));
    setArPreviewUrl(null); // Reset AR preview
  };

  const handleGenerateARPreview = async () => {
    if (!roomImage) {
      toast({
        title: "No image selected",
        description: "Please upload a room image first",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const response = await arService.generateARPreview(listingTitle, roomImage);
      setArPreviewUrl(response.ar_preview_url);
      toast({
        title: "AR Preview Generated!",
        description: "See how this furniture looks in your room",
      });
    } catch (error: any) {
      console.error('AR generation error:', error);
      toast({
        title: "AR Generation Failed",
        description: error.response?.data?.detail || "Failed to generate AR preview",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setRoomImage(null);
    setRoomImagePreview(null);
    setArPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full border-[#143109] text-[#143109] hover:bg-[#143109] hover:text-white">
          <Camera className="mr-2 h-5 w-5" />
          View in Your Room (AR)
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">AR Preview: {listingTitle}</DialogTitle>
          <DialogDescription>
            Upload a photo of your room to see how this furniture would look in your space
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 md:grid-cols-2 mt-4">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">1. Upload Room Photo</CardTitle>
              <CardDescription>Take or upload a photo of your room</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div 
                  className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-[#143109] transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {roomImagePreview ? (
                    <div className="relative">
                      <img 
                        src={roomImagePreview} 
                        alt="Room preview" 
                        className="w-full h-64 object-cover rounded-lg"
                      />
                      <Button
                        variant="destructive"
                        size="icon"
                        className="absolute top-2 right-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleReset();
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <>
                      <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-sm font-medium">Click to upload room photo</p>
                      <p className="text-xs text-gray-500 mt-2">PNG, JPG up to 10MB</p>
                    </>
                  )}
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileSelect}
                />

                {roomImage && !arPreviewUrl && (
                  <Button 
                    onClick={handleGenerateARPreview}
                    disabled={loading}
                    className="w-full bg-[#143109] hover:bg-[#AAAE7F]"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating AR Preview...
                      </>
                    ) : (
                      <>
                        <Eye className="mr-2 h-4 w-4" />
                        Generate AR Preview
                      </>
                    )}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* AR Preview Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">2. AR Preview</CardTitle>
              <CardDescription>
                {arPreviewUrl ? 'See the furniture in your room' : 'Upload and generate to see preview'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {arPreviewUrl ? (
                <div className="space-y-4">
                  <div className="relative">
                    <img 
                      src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${arPreviewUrl}`}
                      alt="AR Preview" 
                      className="w-full h-64 object-cover rounded-lg border-2 border-[#143109]"
                    />
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-sm text-green-800 font-medium">
                      ✓ AR Preview Generated Successfully
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      The green overlay shows approximately where the furniture would be placed
                    </p>
                  </div>
                  <Button 
                    variant="outline" 
                    onClick={handleReset}
                    className="w-full"
                  >
                    Try Another Room
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  <div className="text-center">
                    <Camera className="mx-auto h-12 w-12 text-gray-400 mb-3" />
                    <p className="text-sm text-gray-500">AR preview will appear here</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">Tips for best results:</h4>
          <ul className="text-xs text-blue-700 space-y-1">
            <li>• Take photo from where you want to place the furniture</li>
            <li>• Ensure good lighting in the room</li>
            <li>• Clear the area where furniture would go</li>
            <li>• Hold camera steady for a clear image</li>
          </ul>
        </div>
      </DialogContent>
    </Dialog>
  );
}
