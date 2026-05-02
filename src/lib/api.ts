import axios from 'axios';

// Auto-detect backend host so phone testing works without any config change.
// - localhost: always uses http://localhost:8000
// - Phone on same WiFi (opens http://192.168.x.x:8080): auto-targets http://192.168.x.x:8000
// - Production: set VITE_BACKEND_URL=https://api.yourdomain.com in .env
export const API_BASE_URL: string = (() => {
  // If we are in production (running on the EC2 IP), use a relative path
  // This allows Nginx to handle the proxying to port 8000 internally.
  if (import.meta.env.PROD) {
    return '/api/v1';
  }
  
  const explicit = import.meta.env.VITE_BACKEND_URL as string | undefined;
  if (explicit && !explicit.includes('localhost') && !explicit.includes('127.0.0.1')) {
    return explicit;
  }
  
  if (typeof window !== 'undefined'
    && window.location.hostname !== 'localhost'
    && window.location.hostname !== '127.0.0.1') {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
})();
const API_V1 = `${API_BASE_URL}/api/v1`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_V1,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken') || localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('authToken');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Helper to get image URL
export const getImageUrl = (imagePath: string | null | undefined): string => {
  if (!imagePath) return '/placeholder-image.jpg';
  if (imagePath.startsWith('http')) return imagePath;
  
  const v = `?v=${new Date().getTime()}`;
  if (imagePath.startsWith('/uploads')) {
    return `${API_BASE_URL}${imagePath}${v}`;
  }
  const cleanPath = imagePath.startsWith('/') ? imagePath : `/${imagePath}`;
  return `${API_BASE_URL}${cleanPath}${v}`;
};

// Session management for anonymous tracking
export const getSessionId = (): string => {
  let sid = localStorage.getItem('sessionId');
  if (!sid) {
    sid = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('sessionId', sid);
  }
  return sid;
};

export const rotateSessionId = (): string => {
  const sid = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  localStorage.setItem('sessionId', sid);
  return sid;
};

// Auth Service
export const authService = {
  async register(data: any) {
    const response = await apiClient.post('/register', data);
    return response.data;
  },

  async login(credentials: { username: string; password: string }) {
    const response = await apiClient.post('/login', credentials);

    if (response.data.access_token) {
      localStorage.setItem('authToken', response.data.access_token);
      localStorage.setItem('token', response.data.access_token); // Also store as 'token' for compatibility
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }

    return response.data;
  },

  async logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    rotateSessionId(); // Ensure next session starts fresh
  },

  async getCurrentUser() {
    const response = await apiClient.get('/me');
    return response.data;
  },

  getLoginUrl() {
    return `${API_V1}/auth/google/login`;
  },

  async forgotPassword(email: string) {
    const response = await apiClient.post('/forgot-password', { email });
    return response.data;
  },

  async updateProfile(data: any) {
    const response = await apiClient.patch('/me', data);
    return response.data;
  },

  async sendVerificationCode(data: { email: string; phone?: string }) {
    const response = await apiClient.post('/send-verification-code', data);
    return response.data;
  },

  async verifyCode(data: { email: string; code: string }) {
    const response = await apiClient.post('/verify-code', data);
    return response.data;
  },

  async checkUsername(username: string) {
    const response = await apiClient.get(`/check-username/${username}`);
    return response.data;
  },

  async requestPasswordReset(data: { email: string }) {
    const response = await apiClient.post('/request-password-reset', data);
    return response.data;
  },

  async verifyResetCode(data: { email: string; code: string }) {
    const response = await apiClient.post('/verify-reset-code', data);
    return response.data;
  },

  async resetPassword(data: { email: string; code: string; new_password: string }) {
    const response = await apiClient.post('/reset-password', data);
    return response.data;
  },

  async getUser(idOrUsername: string | number) {
    console.log('DEBUG: authService.getUser called with:', idOrUsername);
    const response = await apiClient.get(`/user-profile/${idOrUsername}`);
    return response.data;
  },
};

// Listing Service
export const listingService = {
  async getListings(params?: any) {
    const response = await apiClient.get('/listings', { params });
    return response.data;
  },

  async getListing(id: number) {
    const response = await apiClient.get(`/listings/${id}`);
    return response.data;
  },

  async createListing(data: any) {
    const formData = new FormData();

    // Add basic fields
    formData.append('title', data.title);
    formData.append('description', data.description);
    formData.append('price', data.price.toString());
    formData.append('category', data.category);
    formData.append('condition', data.condition);
    formData.append('location', data.location);

    // Add optional fields
    if (data.brand) formData.append('brand', data.brand);
    if (data.model) formData.append('model', data.model);
    if (data.material) formData.append('material', data.material);
    if (data.furniture_type) formData.append('furniture_type', data.furniture_type);
    if (data.furniture_subtype) formData.append('furniture_subtype', data.furniture_subtype);
    if (data.is_sliding_door !== undefined) formData.append('is_sliding_door', data.is_sliding_door.toString());
    if (data.has_mattress !== undefined) formData.append('has_mattress', data.has_mattress.toString());
    if (data.mattress_type) formData.append('mattress_type', data.mattress_type);
    if (data.furniture_brand) formData.append('furniture_brand', data.furniture_brand);
    if (data.predicted_price) formData.append('predicted_price', data.predicted_price.toString());

    // Add images
    if (data.images && data.images.length > 0) {
      data.images.forEach((file: File) => {
        formData.append('images', file);
      });
    }

    const response = await apiClient.post('/listings', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async validateImage(category: string, image: File) {
    const formData = new FormData();
    formData.append('category', category);
    formData.append('image', image);

    const response = await apiClient.post('/validate-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async updateListing(id: number, data: any) {
    const response = await apiClient.put(`/listings/${id}`, data);
    return response.data;
  },

  async toggleListingStatus(id: number, updates: { is_active?: boolean; is_sold?: boolean }) {
    const response = await apiClient.patch(`/listings/${id}/status`, updates);
    return response.data;
  },

  async deleteListing(id: number) {
    const response = await apiClient.delete(`/listings/${id}`);
    return response.data;
  },

  async getMyListings() {
    const response = await apiClient.get('/my-listings');
    return response.data;
  },

  async uploadImage(file: File) {
    const formData = new FormData();
    formData.append('image', file);

    const response = await apiClient.post('/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  async uploadImages(files: File[]) {
    const uploadPromises = files.map(file => this.uploadImage(file));
    return Promise.all(uploadPromises);
  },

  async trackCall(listingId: number) {
    const response = await apiClient.post(`/listings/${listingId}/track-call`);
    return response.data;
  },
};

// Prediction Service
export const predictionService = {
  async predictPrice(data: any) {
    const response = await apiClient.post('/predict-price', data);
    return response.data;
  },

  async predictPriceWithDropdowns(data: any) {
    const response = await apiClient.post('/predict-price-with-dropdowns', data);
    return response.data;
  },

  async validateTitle(params: { category: string; title: string; description?: string }) {
    const response = await apiClient.get('/validate-title', { params });
    return response.data;
  },

  async getDropdownOptions(category: string) {
    const response = await apiClient.get(`/dropdown-options/${category}`);
    return response.data;
  },

  async getValidationHints(category: string) {
    const response = await apiClient.get(`/validation-hints/${category}`);
    return response.data;
  },

  async getModelInfo(category: string) {
    const response = await apiClient.get(`/model-info/${category}`);
    return response.data;
  },
};

// Favorites Service
export const favoritesService = {
  async getFavorites() {
    const response = await apiClient.get('/favorites/');
    return response.data;
  },

  async addFavorite(listingId: number) {
    const response = await apiClient.post(`/favorites/${listingId}`);
    return response.data;
  },

  async removeFavorite(listingId: number) {
    const response = await apiClient.delete(`/favorites/${listingId}`);
    return response.data;
  },

  async checkFavorite(listingId: number) {
    const response = await apiClient.get(`/favorites/check/${listingId}`);
    return response.data;
  },
};

// Message Service
export const messageService = {
  async getConversations() {
    const response = await apiClient.get('/messages/conversations');
    return response.data;
  },

  async getConversationMessages(userId: number, listingId: number) {
    const response = await apiClient.get(`/messages/conversation/${userId}/${listingId}`);
    return response.data;
  },

  async getListingMessages(listingId: number) {
    const response = await apiClient.get(`/messages/listing/${listingId}`);
    return response.data;
  },

  async sendMessage(data: { receiver_id: number; listing_id: number; content: string }) {
    const response = await apiClient.post('/messages/', data);
    return response.data;
  },

  async markAsRead(messageId: number) {
    const response = await apiClient.patch(`/messages/${messageId}/read`);
    return response.data;
  },

  async getUnreadCount() {
    const response = await apiClient.get('/messages/unread/count');
    return response.data;
  },

  async deleteConversation(userId: number) {
    const response = await apiClient.delete(`/messages/conversation/${userId}`);
    return response.data;
  },
};

// AR Service
export const arService = {
  async createARPreview(data: any) {
    const response = await apiClient.post('/ar-preview', data);
    return response.data;
  },

  async getARPreview(filename: string) {
    const response = await apiClient.get(`/ar-preview/${filename}`);
    return response.data;
  },

  async getFurnitureItems() {
    const response = await apiClient.get('/furniture-items');
    return response.data;
  },

  async analyzeRoom(formData: FormData) {
    const response = await apiClient.post('/ar/analyze-room', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async generatePreview(data: any) {
    const response = await apiClient.post('/ar/generate-preview', data);
    return response.data;
  },

  async getFurnitureMaterials() {
    const response = await apiClient.get('/ar/furniture-materials');
    return response.data;
  },

  async getRoomStyles() {
    const response = await apiClient.get('/ar/room-styles');
    return response.data;
  },
};

// Recommendation Service
export const recommendationService = {
  async trackActivity(data: any) {
    const response = await apiClient.post('/recommendations/track-activity', data);
    return response.data;
  },

  async getPersonalized(params?: any) {
    const response = await apiClient.get('/recommendations/personalized', { params });
    return response.data;
  },

  async getSimilar(listingId: number, limit?: number) {
    const response = await apiClient.post('/recommendations/similar', {
      listing_id: listingId,
      limit
    });
    return response.data;
  },

  async getTrending(params?: any) {
    const response = await apiClient.get('/recommendations/trending', { params });
    return response.data;
  },

  async trackClick(listingId: number) {
    const response = await apiClient.post(`/recommendations/click/${listingId}`, {});
    return response.data;
  },

  async getCategories() {
    const response = await apiClient.get('/recommendations/categories');
    return response.data;
  },

  async getForYou(params?: any) {
    const response = await apiClient.get('/recommendations/for-you', { params });
    return response.data;
  },
};

// Analytics Service
export const analyticsService = {
  async trackActivity(data: any) {
    const response = await apiClient.post('/analytics/track', data);
    return response.data;
  },

  async getDashboard(days: number = 30) {
    const response = await apiClient.get('/analytics/dashboard', { params: { days } });
    return response.data;
  },

  async getActivities(params?: any) {
    const response = await apiClient.get('/analytics/activities', { params });
    return response.data;
  },

  async getInterests() {
    const response = await apiClient.get('/analytics/interests');
    return response.data;
  },

  async getSearchInsights() {
    const response = await apiClient.get('/analytics/search-insights');
    return response.data;
  },

  async getRecommendationPerformance() {
    const response = await apiClient.get('/analytics/recommendation-performance');
    return response.data;
  },

  async clearHistory() {
    const response = await apiClient.delete('/analytics/clear-history');
    return response.data;
  },
};

// Admin Service
export const adminService = {
  async getAnalytics() {
    const response = await apiClient.get('/admin/analytics');
    return response.data;
  },

  async getUsers(params?: any) {
    const response = await apiClient.get('/admin/users', { params });
    return response.data;
  },

  async deleteUser(userId: number) {
    const response = await apiClient.delete(`/admin/users/${userId}`);
    return response.data;
  },

  async toggleUserActive(userId: number) {
    const response = await apiClient.patch(`/admin/users/${userId}/toggle-active`);
    return response.data;
  },

  async getPendingListings() {
    const response = await apiClient.get('/admin/pending-listings');
    return response.data;
  },

  async approveListing(listingId: number) {
    const response = await apiClient.post(`/admin/approve-listing/${listingId}`);
    return response.data;
  },

  async rejectListing(listingId: number, reason?: string) {
    const response = await apiClient.post(`/admin/reject-listing/${listingId}`, { reason });
    return response.data;
  },

  async deleteListing(listingId: number) {
    const response = await apiClient.delete(`/admin/listings/${listingId}`);
    return response.data;
  },

  async getAllListings(params?: { limit?: number }) {
    const response = await apiClient.get('/admin/all-listings', { params });
    return response.data;
  },
};

// Google Auth Service
export const googleAuthService = {
  async testConnection() {
    const response = await apiClient.get('/auth/google/test');
    return response.data;
  },

  getLoginUrl() {
    return `${API_V1}/auth/google/login`;
  },

  async getCurrentUser() {
    const response = await apiClient.get('/auth/user');
    return response.data;
  },
};

// Support Service
export const supportService = {
  async createTicket(data: { ticket_type: string; subject: string; description: string; attachment_url?: string }) {
    const response = await apiClient.post('/support/tickets', data);
    return response.data;
  },

  async getMyTickets() {
    const response = await apiClient.get('/support/my-tickets');
    return response.data;
  },

  async getAllTickets() {
    const response = await apiClient.get('/support/admin/tickets');
    return response.data;
  },

  async updateTicketStatus(ticketId: number, status: string) {
    const response = await apiClient.patch(`/support/admin/tickets/${ticketId}/status`, { status });
    return response.data;
  },
};

// ─── AR Assets Service ────────────────────────────────────────────────────────
export const arAssetsService = {
  /** Fetch AR model metadata (GLB/USDZ URLs + dimensions) for a listing */
  async getAssets(listingId: number) {
    try {
      const response = await apiClient.get(`/products/${listingId}/assets`);
      return response.data as {
        listing_id: number;
        model_glb_url: string | null;
        model_usdz_url: string | null;
        dimensions_cm: { l: number; w: number; h: number } | null;
        polygon_count: number | null;
        furniture_type: string | null;
      };
    } catch {
      return null;
    }
  },

  /** Admin: update AR model metadata for a listing */
  async updateAssets(
    listingId: number,
    data: {
      model_glb_url?: string;
      model_usdz_url?: string;
      dimensions_cm?: { l: number; w: number; h: number };
      polygon_count?: number;
    }
  ) {
    const response = await apiClient.put(`/products/${listingId}/assets`, data);
    return response.data;
  },

  /** Admin: upload a GLB file directly */
  async uploadGLB(listingId: number, glbFile: File) {
    const form = new FormData();
    form.append('glb_file', glbFile);
    const response = await apiClient.post(
      `/products/${listingId}/assets/upload-glb`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  /** AI Generation: Start a task */
  async generate3D(listingId: number, imageUrl?: string, allImages: boolean = false) {
    const params = new URLSearchParams();
    if (imageUrl) params.append('image_url', imageUrl);
    if (allImages) params.append('all_images', 'true');
    const response = await apiClient.post(
      `/products/${listingId}/assets/generate-3d?${params.toString()}`
    );
    return response.data as { task_id: string; status: string };
  },

  /** AI Generation: Poll status */
  async poll3DStatus(listingId: number, taskId: string) {
    const response = await apiClient.get(
      `/products/${listingId}/assets/generate-3d/${taskId}`
    );
    return response.data as {
      task_id: string;
      status: string;
      progress: number;
      model_urls?: { glb?: string };
      local_url?: string;
      error?: string;
    };
  },

};

export const notificationService = {
  getNotifications: async (): Promise<any[]> => {
    const response = await apiClient.get('/notifications');
    return response.data;
  },
  getUnreadCount: async (): Promise<{ count: number }> => {
    const response = await apiClient.get('/notifications/unread/count');
    return response.data;
  },
  markAsRead: async (id: number): Promise<void> => {
    await apiClient.post(`/notifications/${id}/read`);
  },
  markAllAsRead: async (): Promise<void> => {
    await apiClient.post('/notifications/read-all');
  },
};

export default {
  authService,
  listingService,
  predictionService,
  favoritesService,
  messageService,
  arService,
  arAssetsService,
  recommendationService,
  analyticsService,
  adminService,
  googleAuthService,
  supportService,
  notificationService,
  getImageUrl,
};
