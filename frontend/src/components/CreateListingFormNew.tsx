import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { authService, listingService, getImageUrl, API_BASE_URL } from './lib/api.ts';
import { Upload, Loader2, Sparkles, TrendingUp, AlertCircle, CheckCircle2, XCircle, Info, PartyPopper, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { formatCurrency } from './lib/utils.ts';

interface CreateListingFormNewProps {
  editMode?: boolean;
  listingId?: number;
  existingData?: any;
}

export function CreateListingFormNew({ editMode = false, listingId, existingData }: CreateListingFormNewProps = {}) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [validatingTitle, setValidatingTitle] = useState(false);
  const [showListings, setShowListings] = useState(false);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [dropdownOptions, setDropdownOptions] = useState<any>({});
  const [dynamicDropdownSelections, setDynamicDropdownSelections] = useState<Record<string, string>>({});
  const [titleValidation, setTitleValidation] = useState<{
    is_valid: boolean;
    message: string;
    missing_fields?: string[];
    suggested_title?: string;
    hints?: any;
  } | null>(null);
  const [prediction, setPrediction] = useState<any | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [createdListing, setCreatedListing] = useState<any | null>(null);
  const [userVerified, setUserVerified] = useState<boolean | null>(null);
  const [checkingVerification, setCheckingVerification] = useState(true);
  const [imageValidations, setImageValidations] = useState<{
    [key: number]: {
      isValid?: boolean;
      confidence?: number;
      bestLabel?: string;
      loading: boolean;
      error?: boolean;
    };
  }>({});
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    category: 'mobile',
    condition: '5',
    city: '',
    area: '',
    location: '',
    // Mobile specs
    brand: '',
    ram: 0,
    storage: 0,
    camera: 0,
    battery: 0,
    screen_size: 0,
    has_5g: false,
    has_pta: false,
    has_amoled: false,
    has_warranty: false,
    has_box: false,
    // Laptop specs
    processor: '',
    generation: 10,
    gpu: '',
    has_ssd: true,
    is_gaming: false,
    is_touchscreen: false,
    has_backlit_keyboard: false,
    // Furniture specs
    material: '',
    furniture_type: '',
    furniture_subtype: '',
    seating_capacity: 0,
    is_imported: false,
    is_handmade: false,
    has_storage: false,
    is_modern: false,
    is_antique: false,
    is_foldable: false,
    is_custom_made: false,
    is_sliding_door: false,
    has_mattress: false,
    mattress_type: 'standard',
    furniture_brand: 'none',
  });

  const getDropdownSchemaKey = (key: string, category: string) => {
    let schemaKey = key.toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[()]/g, '')
      .replace(/gb/g, '')
      .replace(/mp/g, '')
      .trim();

    // Specific mapping overrides
    if (schemaKey.includes('ram')) return 'ram';
    if (schemaKey.includes('storage') || schemaKey.includes('rom')) {
      return category === 'furniture' ? 'has_storage' : 'storage';
    }
    if (schemaKey.includes('camera')) return 'camera';
    if (schemaKey.includes('processor')) return 'processor';
    if (schemaKey.includes('brand')) {
      return category === 'furniture' ? 'furniture_brand' : 'brand';
    }
    if (schemaKey.includes('material')) return 'material';
    if (schemaKey.includes('mattress')) return 'has_mattress';
    if (schemaKey.includes('capacity') || schemaKey.includes('seats')) return 'seating_capacity';
    if (schemaKey.includes('type')) return 'furniture_type';
    if (schemaKey.includes('size') && category === 'furniture') return 'furniture_subtype';

    return schemaKey;
  };

  // Cache for LLM responses to prevent hammering the 70B model rate limit on every keystroke
  const titleValidationCache = useRef<Record<string, any>>({});
  const dynamicDropdownCache = useRef<Record<string, any>>({});

  // Load dynamic dropdown options based on category and title (LLM Augmented) - Sync Fix Applied
  const loadDynamicDropdowns = async (category: string, title: string) => {
    if (!title || title.length < 3) return;

    const cacheKey = `${category}|${title.toLowerCase()}`;

    const syncPrepopulations = (dropdowns: any) => {
      const initialSelections: Record<string, string> = {};
      const formDataUpdates: Record<string, any> = {};
      const numericFields = ['ram', 'storage', 'camera', 'seating_capacity', 'screen_size'];
      const booleanFields = ['has_mattress', 'has_storage', 'is_imported', 'is_handmade', 'is_antique'];

      Object.entries(dropdowns).forEach(([key, options]: [string, any]) => {
        const lowerTitle = title.toLowerCase();
        const schemaKey = getDropdownSchemaKey(key, category);
        const foundOption = options.find((opt: string) => lowerTitle.includes(opt.toLowerCase()));

        // Use found option from title, OR auto-select the first option for material fields
        // so that formData.material is never empty when AI dropdowns are loaded
        const selectedOption = foundOption || (schemaKey === 'material' && options.length > 0 ? options[0] : null);

        if (selectedOption) {
          initialSelections[key] = selectedOption;

          let val: any = selectedOption;
          if (numericFields.includes(schemaKey)) {
            const match = selectedOption.match(/\d+/);
            val = match ? parseInt(match[0]) : 0;
          } else if (booleanFields.includes(schemaKey)) {
            val = selectedOption.toLowerCase().includes('yes') || selectedOption.toLowerCase().includes('included') || selectedOption.toLowerCase().includes('true');
          }
          formDataUpdates[schemaKey] = val;
        }
      });

      if (Object.keys(initialSelections).length > 0) {
        setDynamicDropdownSelections(prev => ({ ...prev, ...initialSelections }));
      }
      if (Object.keys(formDataUpdates).length > 0) {
        setFormData(prev => ({ ...prev, ...formDataUpdates }));
      }
    };

    if (dynamicDropdownCache.current[cacheKey]) {
      const cached = dynamicDropdownCache.current[cacheKey];
      setDropdownOptions(cached);
      syncPrepopulations(cached);
      return;
    }

    try {
      const params = new URLSearchParams({ category, title });
      const response = await fetch(`${API_BASE_URL}/api/v1/dynamic-dropdowns?${params}`);
      if (response.ok) {
        const data = await response.json();
        if (data.dropdowns) {
          dynamicDropdownCache.current[cacheKey] = data.dropdowns;
          setDropdownOptions(data.dropdowns);
          syncPrepopulations(data.dropdowns);
        }
      }
    } catch (err) {
      console.error('Error loading dynamic dropdowns:', err);
    }
  };

  // Validate title in real-time
  const validateTitle = async (category: string, title: string, description: string = '', material: string = '') => {
    if (!title || title.length < 5) {
      setTitleValidation(null);
      return;
    }

    const cacheKey = `${category}|${title.toLowerCase()}|${material.toLowerCase()}`;
    const cachedResult = titleValidationCache.current[cacheKey];
    if (cachedResult && cachedResult.message !== "Validation temporarily unavailable, proceeding.") {
      setTitleValidation(cachedResult);
      return;
    }

    setValidatingTitle(true);
    try {
      const params = new URLSearchParams({
        category,
        title,
        description,
        material
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/validate-title?${params}`);
      if (response.ok) {
        const result = await response.json();
        // ONLY cache if it's a real validation result, not our emergency fallback
        if (result.message !== "Validation temporarily unavailable, proceeding.") {
          titleValidationCache.current[cacheKey] = result;
        }
        setTitleValidation(result);
      }
    } catch (err) {
      console.error('Error validating title:', err);
    } finally {
      setValidatingTitle(false);
    }
  };

  const validateSingleImage = async (file: File, index: number, category: string) => {
    // Avoid redundant calls
    if (imageValidations[index]?.loading) return;

    setImageValidations((prev) => ({
      ...prev,
      [index]: { ...(prev[index] || {}), loading: true, error: false },
    }));

    try {
      const result = await listingService.validateImage(category, file);
      setImageValidations((prev) => ({
        ...prev,
        [index]: {
          isValid: result.is_match,
          confidence: result.confidence,
          bestLabel: result.best_label,
          loading: false,
          error: false
        },
      }));
    } catch (error) {
      console.error('Image validation failed:', error);
      setImageValidations((prev) => ({
        ...prev,
        [index]: { loading: false, error: true },
      }));
    }
  };

  // Automatically re-validate all images when the category changes
  useEffect(() => {
    // Only trigger if we have a category and existing images
    if (!formData.category || imageFiles.length === 0) return;

    imageFiles.forEach((file, index) => {
      validateSingleImage(file, index, formData.category);
    });
  }, [formData.category]);

  // Check user verification status on mount
  useEffect(() => {
    const checkVerification = async () => {
      try {
        const user = await authService.getCurrentUser();
        setUserVerified(user.is_verified);
      } catch (err) {
        console.error('Error checking verification:', err);
      } finally {
        setCheckingVerification(false);
      }
    };
    checkVerification();
  }, []);

  // Load dropdown options when category changes

  // Populate form data in edit mode
  useEffect(() => {
    if (editMode && existingData) {
      console.log('Pre-filling form with existing data:', existingData);

      // 1. First, load the dynamic dropdowns
      if (existingData.category && existingData.title) {
        loadDynamicDropdowns(existingData.category, existingData.title);
      }

      // 2. Parse location if it exists
      let city = '';
      let area = '';
      if (existingData.location) {
        const locationParts = existingData.location.split(',').map((s: string) => s.trim());
        if (locationParts.length >= 2) {
          city = locationParts[0];
          area = locationParts[1];
        } else {
          city = locationParts[0] || '';
        }
      }

      // 3. Set form data
      setFormData({
        title: existingData.title || '',
        description: existingData.description || '',
        price: existingData.price?.toString() || '',
        category: existingData.category || 'mobile',
        condition: existingData.condition?.toString() || '5',
        city: city,
        area: area,
        location: existingData.location || '',
        brand: existingData.brand || '',
        ram: typeof existingData.ram === 'number' ? existingData.ram : 0,
        storage: typeof existingData.storage === 'number' ? existingData.storage : 0,
        camera: typeof existingData.camera === 'number' ? existingData.camera : 0,
        battery: typeof existingData.battery === 'number' ? existingData.battery : 0,
        screen_size: typeof existingData.screen_size === 'number' ? existingData.screen_size : 0,
        has_5g: !!existingData.has_5g,
        has_pta: !!existingData.has_pta,
        has_amoled: !!existingData.has_amoled,
        has_warranty: !!existingData.has_warranty,
        has_box: !!existingData.has_box,
        processor: existingData.processor || '',
        generation: typeof existingData.generation === 'number' ? existingData.generation : 10,
        gpu: existingData.gpu || '',
        has_ssd: existingData.has_ssd !== undefined ? !!existingData.has_ssd : true,
        is_gaming: !!existingData.is_gaming,
        is_touchscreen: !!existingData.is_touchscreen,
        has_backlit_keyboard: !!existingData.has_backlit_keyboard,
        material: existingData.material || '',
        furniture_type: existingData.furniture_type || '',
        furniture_subtype: existingData.furniture_subtype || '',
        seating_capacity: typeof existingData.seating_capacity === 'number' ? existingData.seating_capacity : 0,
        is_imported: !!existingData.is_imported,
        is_handmade: !!existingData.is_handmade,
        has_storage: !!existingData.has_storage,
        is_modern: !!existingData.is_modern,
        is_antique: !!existingData.is_antique,
        is_foldable: !!existingData.is_foldable,
        is_custom_made: !!existingData.is_custom_made,
        is_sliding_door: !!existingData.is_sliding_door,
        has_mattress: !!existingData.has_mattress,
        mattress_type: existingData.mattress_type || 'standard',
        furniture_brand: existingData.furniture_brand || 'none',
      });

      // 4. Load existing images as previews
      if (existingData.images) {
        try {
          const parsedImages = typeof existingData.images === 'string' ? JSON.parse(existingData.images) : existingData.images;
          if (Array.isArray(parsedImages)) {
            const imageUrls = parsedImages.map((img: string) => getImageUrl(img));
            setImagePreviews(imageUrls.filter((url: string | null): url is string => url !== null));
          }
        } catch (e) {
          console.error('Failed to parse existing images:', e);
        }
      } else if (existingData.image_url) {
        const url = getImageUrl(existingData.image_url);
        if (url) setImagePreviews([url]);
      }
    }
  }, [editMode, existingData]);

  // Validate title with debounce
  // NLP-based field extraction to reduce manual dropdown scrolling
  const resolveSmartFields = (title: string, description: string) => {
    const text = (title + ' ' + description).toLowerCase();
    const updates: any = {};

    // 1. Category Detection (if not already set firmly by user)
    if (text.match(/phone|smartphone|mobile|iphone|galaxy|pixel/)) updates.category = 'mobile';
    else if (text.match(/laptop|notebook|macbook|thinkpad|chromebook/)) updates.category = 'laptop';
    else if (text.match(/furniture|sofa|bed|table|wardrobe|chair|desk/)) updates.category = 'furniture';

    const category = updates.category || formData.category;

    // 2. Furniture Extraction
    if (category === 'furniture') {
      // Material detection
      if (text.includes('sheesham') || text.includes('teak') || text.includes('walnut')) updates.material = 'wood';
      else if (text.includes('wood') && !text.includes('mdf')) updates.material = 'wood';
      else if (text.includes('mdf') || text.includes('particle board')) updates.material = 'mdf';
      else if (text.includes('metal') || text.includes('iron') || text.includes('steel') || text.includes('almirah')) updates.material = 'metal';
      else if (text.includes('velvet')) updates.material = 'velvet';
      else if (text.includes('fabric') || text.includes('cloth') || text.includes('suede')) updates.material = 'fabric';
      else if (text.includes('foam') || text.includes('sponge')) updates.material = 'foam';
      else if (text.includes('leather') || text.includes('rexine') || text.includes('pu leather')) updates.material = 'leather';
      else if (text.includes('fiber') || text.includes('fibre') || text.includes('plastic')) updates.material = 'plastic';
      else if (text.includes('glass')) updates.material = 'glass';

      // Furniture type detection (order matters: more specific first)
      if (text.includes('l shape') || text.includes('l-shape') || text.includes('l shaped') || text.includes('corner sofa') || text.includes('sectional')) {
        updates.furniture_type = 'sofa';
        updates.furniture_subtype = 'L-Shape Sofa';
      } else if (text.includes('sofa cum bed') || text.includes('sofa bed') || text.includes('sleeper sofa')) {
        updates.furniture_type = 'sofa';
        updates.furniture_subtype = 'Sofa Cum Bed';
      } else if (text.includes('sofa set') || text.includes('sofa suite')) {
        updates.furniture_type = 'sofa';
        updates.furniture_subtype = 'Sofa Set';
      } else if (text.includes('king size') || text.includes('king sized') || text.includes('queen size') || text.includes('double bed') || text.includes('single bed') || text.includes('bunk bed')) {
        updates.furniture_type = 'bed';
        if (text.includes('king')) updates.furniture_subtype = 'King Size Bed';
        else if (text.includes('queen')) updates.furniture_subtype = 'Queen Size Bed';
        else if (text.includes('double')) updates.furniture_subtype = 'Double Bed';
        else if (text.includes('single')) updates.furniture_subtype = 'Single Bed';
        else if (text.includes('bunk')) updates.furniture_subtype = 'Bunk Bed';
      } else if (text.includes('sofa') || text.includes('couch') || text.includes('settee')) {
        updates.furniture_type = 'sofa';
      } else if (text.includes('bed') && !text.includes('bedroom')) {
        updates.furniture_type = 'bed';
      } else if (text.includes('dining table') || text.includes('dining set') || text.includes('dining chair')) {
        updates.furniture_type = 'table';
        updates.furniture_subtype = 'Dining Table';
      } else if (text.includes('coffee table') || text.includes('center table') || text.includes('side table')) {
        updates.furniture_type = 'table';
      } else if (text.includes('table')) {
        updates.furniture_type = 'table';
      } else if (text.includes('office chair') || text.includes('gaming chair') || text.includes('bar stool')) {
        updates.furniture_type = 'chair';
      } else if (text.includes('chair') || text.includes('stool') || text.includes('ottoman')) {
        updates.furniture_type = 'chair';
      } else if (text.includes('wardrobe') || text.includes('almirah') || text.includes('closet') || text.includes('cupboard')) {
        updates.furniture_type = 'wardrobe';
      } else if (text.includes('study desk') || text.includes('office desk') || text.includes('computer desk') || text.includes('writing desk')) {
        updates.furniture_type = 'desk';
      } else if (text.includes('desk')) {
        updates.furniture_type = 'desk';
      } else if (text.includes('cabinet') || text.includes('drawer') || text.includes('dresser') || text.includes('chest')) {
        updates.furniture_type = 'cabinet';
      } else if (text.includes('bookshelf') || text.includes('bookcase') || text.includes('shelf')) {
        updates.furniture_type = 'cabinet';
      }

      // Brand Detection (Furniture)
      if (text.includes('interwood')) updates.furniture_brand = 'interwood';
      else if (text.includes('habitt')) updates.furniture_brand = 'habitt';
      else if (text.includes('ikea')) updates.furniture_brand = 'ikea';
      else if (text.includes('jw') || text.includes('j.w.')) updates.furniture_brand = 'jw furniture';
    }

    // 3. Tech Extraction (Mobile/Laptop)
    if (category === 'mobile' || category === 'laptop') {
      // Tech Brands — comprehensive Pakistani market coverage
      if (text.includes('apple') || text.includes('iphone') || text.includes('macbook')) updates.brand = 'Apple';
      else if (text.includes('samsung') || text.includes('galaxy')) updates.brand = 'Samsung';
      else if (text.includes('xiaomi') || text.includes('mi ')) updates.brand = 'Xiaomi';
      else if (text.includes('redmi')) updates.brand = 'Xiaomi';
      else if (text.includes('poco')) updates.brand = 'Poco';
      else if (text.includes('infinix')) updates.brand = 'Infinix';
      else if (text.includes('tecno')) updates.brand = 'Tecno';
      else if (text.includes('itel')) updates.brand = 'Itel';
      else if (text.includes('qmobile') || text.includes('voice')) updates.brand = 'Qmobile';
      else if (text.includes('oppo')) updates.brand = 'Oppo';
      else if (text.includes('vivo')) updates.brand = 'Vivo';
      else if (text.includes('realme')) updates.brand = 'Realme';
      else if (text.includes('oneplus') || text.includes('one plus')) updates.brand = 'OnePlus';
      else if (text.includes('huawei')) updates.brand = 'Huawei';
      else if (text.includes('honor')) updates.brand = 'Honor';
      else if (text.includes('nokia')) updates.brand = 'Nokia';
      else if (text.includes('motorola') || text.includes('moto ')) updates.brand = 'Motorola';
      else if (text.includes('google') || text.includes('pixel')) updates.brand = 'Google';
      else if (text.includes('sony') || text.includes('xperia')) updates.brand = 'Sony';
      else if (text.includes('hp')) updates.brand = 'HP';
      else if (text.includes('dell')) updates.brand = 'Dell';
      else if (text.includes('lenovo') || text.includes('thinkpad') || text.includes('ideapad')) updates.brand = 'Lenovo';
      else if (text.includes('asus') || text.includes('vivobook') || text.includes('zenbook') || text.includes('rog')) updates.brand = 'Asus';
      else if (text.includes('acer') || text.includes('aspire') || text.includes('nitro')) updates.brand = 'Acer';
      else if (text.includes('msi')) updates.brand = 'MSI';

      // Specs (Common patterns like 8GB, 256GB)
      const ramMatch = text.match(/(\d+)\s*(?:gb|g)\s*ram/);
      if (ramMatch) updates.ram = parseInt(ramMatch[1]);

      const storageMatch = text.match(/(\d+)\s*(?:gb|g)\s*(?:storage|ssd|hdd|rom)/);
      if (storageMatch) updates.storage = parseInt(storageMatch[1]);

      if (category === 'laptop') {
        const procMatch = text.match(/(i3|i5|i7|i9|ryzen\s*\d|m1|m2|m3)/);
        if (procMatch) updates.processor = procMatch[1].toUpperCase();

        if (text.includes('gaming')) updates.is_gaming = true;
        if (text.includes('touch') || text.includes('touchscreen')) updates.is_touchscreen = true;
        if (text.includes('ssd')) updates.has_ssd = true;
      }

      if (category === 'mobile') {
        if (text.includes('pta approved')) updates.has_pta = true;
        if (text.includes('5g')) updates.has_5g = true;
        if (text.includes('amoled') || text.includes('oled')) updates.has_amoled = true;
      }
    }

    // Filter out updates that are already set (to avoid infinite loops or overwriting manual changes)
    const finalUpdates: any = {};
    Object.keys(updates).forEach(key => {
      if (updates[key] !== (formData as any)[key]) {
        finalUpdates[key] = updates[key];
      }
    });

    if (Object.keys(finalUpdates).length > 0) {
      setFormData(prev => ({ ...prev, ...finalUpdates }));
    }
  };

  // Trigger Smart Field extraction and Title validation
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.title && formData.title.trim().length >= 5) {
        // Wrap in async IIFE to serialize the network requests and prevent Groq 429s (concurrency limit)
        (async () => {
          // First extract fields locally
          resolveSmartFields(formData.title, formData.description);

          // Then validate title (AWAIT it)
          const material = formData.category === 'furniture' ? formData.material : '';
          await validateTitle(formData.category, formData.title, formData.description, material);

          // Fetch dynamic dropdowns ONLY AFTER validation completes
          await loadDynamicDropdowns(formData.category, formData.title);
        })();
      } else {
        // Clear stale validation when title is empty or too short
        setTitleValidation(null);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [formData.title, formData.description, formData.category]);


  // Enhanced canPredict check to delay prediction until mandatory fields are filled
  const canPredict = () => {
    // Never re-trigger while a prediction is already in flight
    if (predicting) return false;
    if (!formData.category || !formData.condition) return false;
    // Require a meaningful title (at least 5 chars, not just generic)
    if (!formData.title || formData.title.trim().length < 5) return false;
    // If LLM validation returned and says it's explicitly invalid (no brand/product), block
    if (titleValidation && !titleValidation.is_valid) return false;

    // Category specific mandatory requirements
    if (formData.category === 'furniture') {
      const hasDynamicSpecs = Object.keys(dynamicDropdownSelections).length > 0;
      if (!formData.material && !hasDynamicSpecs) return false;
    } else if (formData.category === 'mobile') {
      // Require at least one concrete spec to be selected from dropdowns
      if (formData.ram === 0 && formData.storage === 0) return false;
    } else if (formData.category === 'laptop') {
      // Require at least RAM or processor to be set
      if (formData.ram === 0 && !formData.processor) return false;
    }

    return true;
  };

  // Auto-predict price when canPredict is true.
  // dynamicDropdownSelections serialised → stable string dep (avoids new-object-on-every-render)
  const dynamicSpecsKey = JSON.stringify(dynamicDropdownSelections);
  // predictingRef: tracks in-flight state WITHOUT being reactive (doesn't appear in deps)
  const predictingRef = useRef(false);
  // lastPredictedKey: remembers the exact input set that last triggered a prediction,
  // so the same combination never fires twice (e.g. when predicting flips false after completion)
  const lastPredictedKey = useRef('');

  useEffect(() => {
    // Build a key from all price-relevant inputs
    const inputKey = [
      formData.title, formData.category, formData.condition, formData.description,
      formData.material, formData.ram, formData.storage, formData.processor,
      formData.gpu, formData.generation, formData.furniture_type, formData.furniture_subtype,
      formData.seating_capacity, formData.has_pta, formData.has_warranty, formData.has_box,
      formData.has_5g, formData.has_amoled, formData.has_ssd, formData.is_gaming,
      formData.is_touchscreen, formData.is_antique, formData.is_handmade, formData.is_imported,
      formData.has_storage, dynamicSpecsKey,
      // titleValidation.is_valid is included so re-validates correctly update
      titleValidation?.is_valid,
    ].join('|');

    // Don't fire if inputs haven't changed since last prediction, or if one is in flight
    if (predictingRef.current || inputKey === lastPredictedKey.current) return;

    // Validate all required conditions without reading `predicting` state (avoids dep)
    if (!formData.category || !formData.condition) return;
    if (!formData.title || formData.title.trim().length < 5) return;
    if (titleValidation && !titleValidation.is_valid) return;
    if (formData.category === 'furniture') {
      const hasDynamicSpecs = Object.keys(dynamicDropdownSelections).length > 0;
      if (!formData.material && !hasDynamicSpecs) return;
    } else if (formData.category === 'mobile') {
      if (formData.ram === 0 && formData.storage === 0) return;
    } else if (formData.category === 'laptop') {
      if (formData.ram === 0 && !formData.processor) return;
    }

    const timer = setTimeout(() => {
      lastPredictedKey.current = inputKey;  // stamp before firing
      handlePredictPrice();
    }, 1200);
    return () => clearTimeout(timer);
  }, [
    formData.title, formData.category, formData.condition, formData.description,
    formData.material, titleValidation,
    formData.has_pta, formData.has_warranty, formData.has_box, formData.has_5g,
    formData.has_amoled, formData.ram, formData.storage,
    formData.has_ssd, formData.is_gaming, formData.is_touchscreen,
    formData.gpu, formData.processor, formData.generation,
    formData.furniture_type, formData.furniture_subtype, formData.seating_capacity,
    formData.is_antique, formData.is_handmade, formData.is_imported, formData.has_storage,
    dynamicSpecsKey,
  ]);

  const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length === 0) return;

    const totalImages = imageFiles.length + selectedFiles.length;
    if (totalImages > 7) {
      alert('Maximum 7 images allowed');
      return;
    }

    // Validate each file
    for (const file of selectedFiles) {
      if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
        alert('Please upload only JPG, JPEG or PNG images');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert('Each image must be less than 10MB');
        return;
      }
    }

    const startIndex = imageFiles.length;

    // 1. Update files state first
    setImageFiles(prev => [...prev, ...selectedFiles]);

    // 2. Generate previews and trigger validation in parallel
    const previewPromises = selectedFiles.map((file, i) => {
      const globalIndex = startIndex + i;

      // Trigger AI validation
      validateSingleImage(file, globalIndex, formData.category);

      return new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.readAsDataURL(file);
      });
    });

    const newPreviews = await Promise.all(previewPromises);
    setImagePreviews(prev => [...prev, ...newPreviews]);

    // Clear the input value so the same file(s) can be selected again
    e.target.value = '';
  };

  const handlePredictPrice = async () => {
    if (!titleValidation || !titleValidation.is_valid) {
      setPredictionError('Please provide a valid title with relevant product information');
      return;
    }

    predictingRef.current = true;
    setPredicting(true);
    setPredictionError(null);

    try {
      const requestData: any = {
        category: formData.category,
        title: formData.title,
        description: formData.description,
        condition: formData.condition,
      };

      // Add category-specific fields
      if (formData.category === 'mobile') {
        Object.assign(requestData, {
          brand: formData.brand,
          ram: formData.ram,
          storage: formData.storage,
          camera: formData.camera,
          battery: formData.battery,
          screen_size: formData.screen_size,
          has_5g: formData.has_5g,
          has_pta: formData.has_pta,
          has_amoled: formData.has_amoled,
          has_warranty: formData.has_warranty,
          has_box: formData.has_box,
        });
      } else if (formData.category === 'laptop') {
        Object.assign(requestData, {
          brand: formData.brand,
          processor: formData.processor,
          generation: formData.generation,
          ram: formData.ram,
          storage: formData.storage,
          gpu: formData.gpu,
          screen_size: formData.screen_size,
          has_ssd: formData.has_ssd,
          is_gaming: formData.is_gaming,
          is_touchscreen: formData.is_touchscreen,
        });
      } else if (formData.category === 'furniture') {
        Object.assign(requestData, {
          material: formData.material,
          furniture_type: formData.furniture_type,
          furniture_subtype: formData.furniture_subtype,
          seating_capacity: formData.seating_capacity,
          is_imported: formData.is_imported,
          is_handmade: formData.is_handmade,
          has_storage: formData.has_storage,
          is_modern: formData.is_modern,
          is_antique: formData.is_antique,
          is_sliding_door: formData.is_sliding_door,
          has_mattress: formData.has_mattress,
          mattress_type: formData.mattress_type,
          furniture_brand: formData.furniture_brand,
          dynamic_specs: dynamicDropdownSelections,
        });
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/predict-price`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.log('Error response:', errorData);

        // Extract error message from nested detail object
        let errorMsg = 'Prediction failed';
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMsg = errorData.detail;
          } else if (typeof errorData.detail === 'object') {
            errorMsg = errorData.detail.message || errorData.detail.error || JSON.stringify(errorData.detail);
          }
        }
        throw new Error(errorMsg);
      }

      const result = await response.json();
      console.log('Prediction result:', result);

      // Validate result structure
      if (!result || typeof result.predicted_price === 'undefined') {
        console.log('Invalid result structure:', result);
        throw new Error('Invalid prediction response from server');
      }

      setPrediction(result);
      setPredictionError(null);

      // Auto-fill the price using functional form to avoid stale closure overwriting other fields
      setFormData(prev => ({ ...prev, price: Math.round(result.predicted_price).toString() }));
    } catch (error: any) {
      console.error('Prediction error:', error);

      // Extract error message properly
      let errorMessage = 'Unable to predict price';
      if (error.message && typeof error.message === 'string') {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }

      setPredictionError(errorMessage);
      setPrediction(null);
    } finally {
      predictingRef.current = false;
      setPredicting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted, starting validation...');

    // Basic field validation
    if (!formData.title || formData.title.trim().length < 5) {
      alert('❌ Please enter a title (at least 5 characters)');
      return;
    }

    if (!formData.description || formData.description.trim().length < 10) {
      alert('❌ Please enter a description (at least 10 characters)');
      return;
    }

    if (!formData.location || formData.location.trim() === '') {
      alert('❌ Please enter the location');
      return;
    }

    // Title validation check
    if (!titleValidation || !titleValidation.is_valid) {
      alert('❌ Invalid Title: Please provide a valid title with relevant product information (brand, model, specs)');
      return;
    }

    // Only require images for new listings, not when editing
    if (!editMode) {
      if (imageFiles.length < 2) {
        alert('❌ Please upload at least 2 product images');
        return;
      }

      if (imageFiles.length > 10) {
        alert('❌ Maximum 10 images allowed');
        return;
      }
    }

    // Category-specific validation
    if ((formData.category === 'mobile' || formData.category === 'laptop') && !formData.brand) {
      alert('❌ Please select a brand from the dropdown');
      return;
    }

    if (formData.category === 'furniture' && !formData.furniture_type) {
      alert('❌ Please select the furniture type');
      return;
    }

    const hasDynamicSpecs = Object.keys(dynamicDropdownSelections).length > 0;
    if (formData.category === 'furniture' && !formData.material && !hasDynamicSpecs) {
      alert('❌ Please select the material for furniture');
      return;
    }

    if (!formData.price || parseFloat(formData.price) <= 0) {
      alert('❌ Please enter a valid price');
      return;
    }

    // Check if user is logged in
    const token = localStorage.getItem('authToken');
    if (!token) {
      alert('❌ Please login first to create a listing');
      navigate('/login');
      return;
    }

    setLoading(true);
    console.log(editMode ? '=== STARTING LISTING UPDATE ===' : '=== STARTING LISTING CREATION ===');
    console.log('Form data:', formData);
    console.log('Image files:', imageFiles.map(f => f.name));
    console.log('Token present:', !!localStorage.getItem('authToken'));

    try {
      const listingData: any = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        price: parseFloat(formData.price),
        category: formData.category,
        condition: formData.condition,
        location: formData.location.trim(),
        images: imageFiles.length > 0 ? imageFiles : undefined,
        predicted_price: prediction?.predicted_price || undefined,
        brand: formData.brand || undefined,
        material: formData.material || undefined,
        furniture_type: formData.furniture_type || undefined,
        furniture_subtype: formData.furniture_subtype || undefined,
        is_sliding_door: formData.is_sliding_door,
        has_mattress: formData.has_mattress,
        mattress_type: formData.mattress_type || undefined,
        furniture_brand: formData.furniture_brand || undefined,
      };

      console.log('Prepared listing data for API:', listingData);

      let result;
      if (editMode && listingId) {
        console.log('Processing images for update...');
        // Handle images for update
        let finalImageUrls: string[] = [];
        // Keep existing remote URLs (filter out local data URIs)
        const existingUrls = imagePreviews.filter(p => !p.startsWith('data:'));
        finalImageUrls = [...existingUrls];

        // Upload any new selected files
        if (imageFiles.length > 0) {
          for (const file of imageFiles) {
            try {
              const uploadRes = await listingService.uploadImage(file);
              if (uploadRes && uploadRes.image_url) {
                finalImageUrls.push(uploadRes.image_url);
              }
            } catch (err) {
              console.error("Failed to upload image during update", err);
              throw new Error("Failed to upload one or more new images.");
            }
          }
        }

        const updateData = {
          ...listingData,
          images: finalImageUrls.length > 0 ? JSON.stringify(finalImageUrls) : undefined
        };

        console.log('Calling listingService.updateListing with:', updateData);
        result = await listingService.updateListing(listingId, updateData);
        console.log('✅ Listing updated successfully:', result);
        alert('✅ Listing updated successfully!');
        navigate(`/product/${listingId}`);
      } else {
        console.log('Calling listingService.createListing...');
        result = await listingService.createListing(listingData);
        console.log('✅ Listing created successfully:', result);
        // Show preview dialog instead of alert
        setCreatedListing(result);
        setShowPreviewDialog(true);
      }
    } catch (error: any) {
      console.error('=== ERROR CREATING LISTING ===');
      console.error('Error object:', error);
      console.error('Error message:', error.message);
      console.error('Error response:', error.response);
      console.error('Error request:', error.request);
      console.error('Error config:', error.config);

      // Check for network error (no response)
      if (!error.response && !error.request) {
        alert(`❌ Network Error: Unable to connect to server. Please check if the backend is running on ${API_BASE_URL}`);
        return;
      }

      // Check if request was made but no response received
      if (error.request && !error.response) {
        alert('❌ Network Error: No response from server. Please check your internet connection and backend server.');
        return;
      }

      // Check for authentication error
      if (error.response?.status === 401) {
        alert('❌ Session expired. Please login again.');
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        navigate('/login');
        return;
      }

      // Check for validation errors
      if (error.response?.status === 422) {
        const details = error.response?.data?.detail;
        if (Array.isArray(details)) {
          const fieldErrors = details.map((d: any) => `${d.loc?.join('.') || 'field'}: ${d.msg}`).join('\n');
          alert('❌ Validation Error:\n' + fieldErrors);
        } else {
          alert('❌ Validation Error: ' + (details || 'Invalid data'));
        }
        return;
      }

      const errorMsg = error.response?.data?.detail || error.message || 'Failed to create listing. Please try again.';

      // Special handling for CLIP Mismatch
      if (errorMsg.includes('Image-Category Mismatch')) {
        alert('🚫 ' + errorMsg);
      } else {
        alert('❌ Error: ' + errorMsg);
      }
    } finally {
      setLoading(false);
      console.log('=== LISTING CREATION ENDED ===');
    }
  };



  return (
    <div className="container mx-auto py-8 px-4">
      <Card className="max-w-4xl mx-auto">
        <CardHeader className="bg-gradient-to-r from-[#143109] to-[#AAAE7F] text-white">
          <CardTitle className="text-2xl flex items-center gap-2">
            <Sparkles className="h-6 w-6" />
            {editMode ? 'Edit Listing' : 'Create New Listing'}
          </CardTitle>
          <CardDescription className="text-white/90">
            {editMode ? 'Update your product information' : 'Add a new product with AI-powered price prediction'}
          </CardDescription>
        </CardHeader>
        <CardContent className="mt-6">
          {!checkingVerification && userVerified === false && (
            <Alert variant="destructive" className="mb-6 border-2">
              <AlertCircle className="h-5 w-5" />
              <AlertTitle className="font-bold">Email Verification Required</AlertTitle>
              <AlertDescription className="flex flex-col gap-3">
                <p>You must verify your email address before you can post ads on EZSell. This helps maintain a safe community for everyone.</p>
                <Button
                  variant="outline"
                  className="w-fit bg-red-100 hover:bg-red-200 text-red-900 border-red-300"
                  onClick={() => navigate('/settings')}
                >
                  Go to Settings to Verify
                </Button>
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Step 1: Basic Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                📝 Step 1: Product Details
              </h3>

              {/* Category */}
              <div className="space-y-2">
                <Label>Category *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => {
                    setFormData({ ...formData, category: value });
                    setPrediction(null);
                    setTitleValidation(null);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mobile">📱 Mobile</SelectItem>
                    <SelectItem value="laptop">💻 Laptop</SelectItem>
                    <SelectItem value="furniture">🛋️ Furniture</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Condition - 10 Level Scale */}
              <div className="space-y-2">
                <Label>Condition * (Affects Price Prediction)</Label>
                <Select
                  value={formData.condition}
                  onValueChange={(value) => setFormData({ ...formData, condition: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 - Brand New/Sealed (~100% value)</SelectItem>
                    <SelectItem value="9">9 - Excellent/Mint (~95% value)</SelectItem>
                    <SelectItem value="8">8 - Like New (~88% value)</SelectItem>
                    <SelectItem value="7">7 - Very Good (~80% value)</SelectItem>
                    <SelectItem value="6">6 - Good (~70% value)</SelectItem>
                    <SelectItem value="5">5 - Average/Used (~60% value)</SelectItem>
                    <SelectItem value="4">4 - Fair (~48% value)</SelectItem>
                    <SelectItem value="3">3 - Acceptable (~35% value)</SelectItem>
                    <SelectItem value="2">2 - Poor/Damaged (~25% value)</SelectItem>
                    <SelectItem value="1">1 - For Parts/Broken (~15% value)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  Select the condition level that best matches your product. Higher numbers = better condition = higher predicted price.
                </p>
              </div>

              {/* Title with Validation */}
              <div className="space-y-2">
                <Label>Title * (Include brand, model, specs)</Label>
                <Input
                  placeholder={
                    formData.category === 'mobile'
                      ? 'e.g., Samsung Galaxy S23 Ultra 12GB RAM 256GB'
                      : formData.category === 'laptop'
                        ? 'e.g., Dell XPS 15 Intel Core i7 12th Gen 16GB RAM'
                        : 'e.g., Modern 5 Seater L-Shape Sofa Premium Fabric'
                  }
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className={
                    titleValidation
                      ? titleValidation.is_valid
                        ? 'border-green-500'
                        : 'border-red-500'
                      : ''
                  }
                  required
                />
                {validatingTitle && (
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Validating title...
                  </p>
                )}
                {titleValidation && !validatingTitle && (
                  <div className={`flex items-start gap-2 p-3 rounded-lg ${titleValidation.is_valid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                    }`}>
                    {titleValidation.is_valid ? (
                      <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="text-sm w-full">
                      <p className="font-medium">{titleValidation.message}</p>
                      {titleValidation.missing_fields && titleValidation.missing_fields.length > 0 && (
                        <p className="mt-1 text-xs font-semibold">
                          Missing info: {titleValidation.missing_fields.join(', ')}
                        </p>
                      )}
                      {!titleValidation.is_valid && titleValidation.hints && (
                        <p className="mt-1 text-xs">
                          Example: {titleValidation.hints.example}
                        </p>
                      )}
                      {titleValidation.suggested_title && titleValidation.suggested_title !== formData.title && (
                        <div className="mt-2 text-right">
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            className="text-xs py-1 h-7 border-green-600 text-green-700 bg-green-50 hover:bg-green-100"
                            onClick={() => {
                              setFormData(prev => ({ ...prev, title: titleValidation!.suggested_title! }));
                            }}
                          >
                            ✨ Apply Suggestion: {titleValidation.suggested_title}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label>Description *</Label>
                <Textarea
                  placeholder="Add detailed description including features, condition, age..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={4}
                  required
                />
              </div>

              {/* Location - City and Area */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>City *</Label>
                  <Select
                    value={formData.city}
                    onValueChange={(value) => {
                      setFormData({ ...formData, city: value, area: '', location: value });
                    }}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select city" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Islamabad">Islamabad</SelectItem>
                      <SelectItem value="Rawalpindi">Rawalpindi</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Area/Sector *</Label>
                  <Select
                    value={formData.area}
                    onValueChange={(value) => {
                      setFormData({ ...formData, area: value, location: `${formData.city}, ${value}` });
                    }}
                    disabled={!formData.city}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={formData.city ? "Select area" : "Select city first"} />
                    </SelectTrigger>
                    <SelectContent>
                      {formData.city === 'Islamabad' && [
                        'Bahria Town', 'Blue Area', 'DHA Phase 1', 'DHA Phase 2', 'F-6', 'F-7', 'F-8', 'F-10', 'F-11',
                        'G-6', 'G-7', 'G-8', 'G-9', 'G-10', 'G-11', 'G-13', 'G-14', 'G-15',
                        'I-8', 'I-9', 'I-10', 'I-11', 'I-14',
                        'PWD Housing Scheme', 'Sector B-17', 'Sector C-18', 'Sector D-12', 'Sector D-17', 'Sector E-7', 'Sector E-11'
                      ].sort().map(area => (
                        <SelectItem key={area} value={area}>{area}</SelectItem>
                      ))}
                      {formData.city === 'Rawalpindi' && [
                        'Adyala Road', 'Airport Housing Society', 'Allama Iqbal Town', 'Bahria Town Phase 1', 'Bahria Town Phase 2',
                        'Bahria Town Phase 3', 'Bahria Town Phase 4', 'Bahria Town Phase 5', 'Bahria Town Phase 6',
                        'Bahria Town Phase 7', 'Bahria Town Phase 8', 'Chaklala Scheme 3', 'Commercial Market',
                        'Committee Chowk', 'DHA Phase 1', 'DHA Phase 2', 'Gulistan Colony', 'Gulzar-e-Quaid',
                        'Jinnah Garden', 'Korang Town', 'Main Murree Road', 'Misrial Road', 'Model Town',
                        'Peoples Colony', 'PWD Housing Scheme', 'Saddar', 'Satellite Town', 'Shamshabad', 'Shamsabad',
                        'Tench Bhatta', 'Westridge', 'Wah Cantt'
                      ].sort().map(area => (
                        <SelectItem key={area} value={area}>{area}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Image Upload */}
              <div className="space-y-2">
                <Label>Product Images (Up to 7 images)</Label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-[#143109] transition-colors">
                  {imagePreviews.length > 0 ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        {imagePreviews.map((preview, index) => (
                          <div key={index} className="relative group">
                            <img
                              src={preview}
                              alt={`Preview ${index + 1}`}
                              className={`h-32 w-full rounded-lg object-cover transition-all ${imageValidations[index]?.loading ? 'opacity-50' :
                                imageValidations[index]?.isValid === false ? 'ring-2 ring-red-500' :
                                  imageValidations[index]?.isValid === true ? 'ring-2 ring-green-500' : ''
                                }`}
                            />

                            {/* AI Validation Badge */}
                            <div className="absolute top-1 left-1 flex flex-col gap-1">
                              {imageValidations[index]?.loading ? (
                                <div className="bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded flex items-center gap-1 backdrop-blur-sm">
                                  <Loader2 className="h-2 w-2 animate-spin" /> AI Checking...
                                </div>
                              ) : imageValidations[index]?.error ? (
                                <div className="bg-amber-500/90 text-white text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1 backdrop-blur-sm shadow-sm">
                                  <AlertCircle className="h-2.5 w-2.5" /> AI Error
                                </div>
                              ) : imageValidations[index]?.isValid === true ? (
                                <div className="bg-green-500/90 text-white text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1 backdrop-blur-sm shadow-sm">
                                  <CheckCircle2 className="h-2.5 w-2.5" /> AI Verified
                                </div>
                              ) : imageValidations[index]?.isValid === false ? (
                                <div className="bg-red-500/90 text-white text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1 backdrop-blur-sm shadow-sm">
                                  <AlertCircle className="h-2.5 w-2.5" /> Mismatch: {imageValidations[index]?.bestLabel}
                                </div>
                              ) : null}
                            </div>

                            <span className="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                              {index + 1}
                            </span>
                          </div>
                        ))}
                      </div>
                      <p className="text-sm text-green-600 font-medium">
                        ✅ {imagePreviews.length} images uploaded
                      </p>
                      <div className="flex gap-2">
                        {imagePreviews.length < 7 && (
                          <label className="flex-1">
                            <input
                              type="file"
                              accept=".jpg,.jpeg,.png"
                              onChange={handleImageChange}
                              className="hidden"
                              multiple
                            />
                            <Button
                              type="button"
                              variant="default"
                              className="w-full"
                              onClick={(e) => {
                                e.preventDefault();
                                (e.currentTarget.previousElementSibling as HTMLInputElement)?.click();
                              }}
                            >
                              ➕ Add More Images
                            </Button>
                          </label>
                        )}
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            setImageFiles([]);
                            setImagePreviews([]);
                          }}
                        >
                          Remove All Images
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <label className="cursor-pointer block">
                      <input
                        type="file"
                        accept=".jpg,.jpeg,.png"
                        onChange={handleImageChange}
                        className="hidden"
                        multiple
                      />
                      <Upload className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                      <p className="text-sm text-gray-600 font-medium">
                        Click to upload images
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        JPG, JPEG, PNG - Max 10MB each - Up to 7 images
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        📸 Minimum 2 images required - Maximum 7 images allowed
                      </p>
                    </label>
                  )}
                </div>
              </div>
            </div>

            {/* Step 2: Category-Specific Fields */}
            {formData.category && (
              <div className="space-y-4 border-t pt-6">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  🔧 Step 2: {formData.category.charAt(0).toUpperCase() + formData.category.slice(1)} Specifications
                  {Object.keys(dropdownOptions).length > 0 && (
                    <Badge className="bg-purple-100 text-purple-800 border-purple-200"><Sparkles className="w-3 h-3 mr-1 inline" /> AI Guided</Badge>
                  )}
                </h3>

                {/* Dynamic AI Dropdowns */}
                {Object.keys(dropdownOptions).length > 0 ? (
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    {Object.entries(dropdownOptions).map(([key, options]: [string, any]) => {
                      const schemaKey = getDropdownSchemaKey(key, formData.category);

                      const numericFields = ['ram', 'storage', 'camera', 'seating_capacity', 'screen_size'];
                      const booleanFields = ['has_mattress', 'has_storage', 'is_imported', 'is_handmade', 'is_antique'];
                      // For display, use the selection state (raw string from LLM)
                      const displayValue = dynamicDropdownSelections[key] || '';

                      return (
                        <div key={key}>
                          <Label>{key}</Label>
                          <Select
                            value={displayValue}
                            onValueChange={(v) => {
                              // Update the display selection
                              setDynamicDropdownSelections(prev => ({ ...prev, [key]: v }));
                              // Also update the actual form data
                              let val: any = v;
                              if (numericFields.includes(schemaKey)) {
                                const match = v.match(/\d+/);
                                val = match ? parseInt(match[0]) : 0;
                              } else if (booleanFields.includes(schemaKey)) {
                                val = v.toLowerCase().includes('yes') || v.toLowerCase().includes('included') || v.toLowerCase().includes('true');
                              }
                              setFormData(prev => ({ ...prev, [schemaKey]: val }));
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder={`Select ${key}`} />
                            </SelectTrigger>
                            <SelectContent>
                              {options.map((opt: string) => (
                                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      );
                    })}
                  </div>
                ) : null}

                {/* Mobile Fields */}
                {formData.category === 'mobile' && (
                  <div className="grid grid-cols-2 gap-4">
                    {/* Fallback Static Dropdowns */}
                    {Object.keys(dropdownOptions).length === 0 && (
                      <>
                        <div>
                          <Label>Brand *</Label>
                          <Select value={formData.brand} onValueChange={(v) => setFormData({ ...formData, brand: v })} required>
                            <SelectTrigger>
                              <SelectValue placeholder="Select brand" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Apple">Apple</SelectItem>
                              <SelectItem value="Samsung">Samsung</SelectItem>
                              <SelectItem value="Xiaomi">Xiaomi</SelectItem>
                              <SelectItem value="Redmi">Redmi</SelectItem>
                              <SelectItem value="Oppo">Oppo</SelectItem>
                              <SelectItem value="Vivo">Vivo</SelectItem>
                              <SelectItem value="Realme">Realme</SelectItem>
                              <SelectItem value="OnePlus">OnePlus</SelectItem>
                              <SelectItem value="Huawei">Huawei</SelectItem>
                              <SelectItem value="Google">Google</SelectItem>
                              <SelectItem value="Nokia">Nokia</SelectItem>
                              <SelectItem value="Infinix">Infinix</SelectItem>
                              <SelectItem value="Tecno">Tecno</SelectItem>
                              <SelectItem value="Other">Other</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>RAM (GB)</Label>
                          <Select value={String(formData.ram)} onValueChange={(v) => setFormData({ ...formData, ram: parseInt(v) })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0">Unknown</SelectItem>
                              <SelectItem value="2">2 GB</SelectItem>
                              <SelectItem value="3">3 GB</SelectItem>
                              <SelectItem value="4">4 GB</SelectItem>
                              <SelectItem value="6">6 GB</SelectItem>
                              <SelectItem value="8">8 GB</SelectItem>
                              <SelectItem value="12">12 GB</SelectItem>
                              <SelectItem value="16">16 GB</SelectItem>
                              <SelectItem value="18">18 GB</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Storage (GB)</Label>
                          <Select value={String(formData.storage)} onValueChange={(v) => setFormData({ ...formData, storage: parseInt(v) })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0">Unknown</SelectItem>
                              <SelectItem value="16">16 GB</SelectItem>
                              <SelectItem value="32">32 GB</SelectItem>
                              <SelectItem value="64">64 GB</SelectItem>
                              <SelectItem value="128">128 GB</SelectItem>
                              <SelectItem value="256">256 GB</SelectItem>
                              <SelectItem value="512">512 GB</SelectItem>
                              <SelectItem value="1024">1 TB</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Camera (MP)</Label>
                          <Select value={String(formData.camera)} onValueChange={(v) => setFormData({ ...formData, camera: parseInt(v) })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0">Unknown</SelectItem>
                              <SelectItem value="8">8 MP</SelectItem>
                              <SelectItem value="12">12 MP</SelectItem>
                              <SelectItem value="13">13 MP</SelectItem>
                              <SelectItem value="16">16 MP</SelectItem>
                              <SelectItem value="20">20 MP</SelectItem>
                              <SelectItem value="48">48 MP</SelectItem>
                              <SelectItem value="50">50 MP</SelectItem>
                              <SelectItem value="64">64 MP</SelectItem>
                              <SelectItem value="108">108 MP</SelectItem>
                              <SelectItem value="200">200 MP</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </>
                    )}

                    {/* Mobile Boolean Features */}
                    <div className="col-span-2 grid grid-cols-2 gap-3 mt-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_5g}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_5g: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">5G Support</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_pta}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_pta: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">PTA Approved</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_amoled}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_amoled: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">AMOLED Display</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_warranty}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_warranty: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Warranty</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_box}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_box: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Original Box</Label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Laptop Fields */}
                {formData.category === 'laptop' && (
                  <div className="grid grid-cols-2 gap-4">
                    {/* Fallback Static Dropdowns */}
                    {Object.keys(dropdownOptions).length === 0 && (
                      <>
                        <div>
                          <Label>Brand *</Label>
                          <Select value={formData.brand} onValueChange={(v) => setFormData({ ...formData, brand: v })} required>
                            <SelectTrigger>
                              <SelectValue placeholder="Select brand" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="HP">HP</SelectItem>
                              <SelectItem value="Dell">Dell</SelectItem>
                              <SelectItem value="Lenovo">Lenovo</SelectItem>
                              <SelectItem value="Apple">Apple</SelectItem>
                              <SelectItem value="Asus">Asus</SelectItem>
                              <SelectItem value="Acer">Acer</SelectItem>
                              <SelectItem value="MSI">MSI</SelectItem>
                              <SelectItem value="Microsoft">Microsoft</SelectItem>
                              <SelectItem value="Razer">Razer</SelectItem>
                              <SelectItem value="Other">Other</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Processor</Label>
                          <Select value={formData.processor} onValueChange={(v) => setFormData({ ...formData, processor: v })}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select processor" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Intel Core i3">Intel Core i3</SelectItem>
                              <SelectItem value="Intel Core i5">Intel Core i5</SelectItem>
                              <SelectItem value="Intel Core i7">Intel Core i7</SelectItem>
                              <SelectItem value="Intel Core i9">Intel Core i9</SelectItem>
                              <SelectItem value="AMD Ryzen 3">AMD Ryzen 3</SelectItem>
                              <SelectItem value="AMD Ryzen 5">AMD Ryzen 5</SelectItem>
                              <SelectItem value="AMD Ryzen 7">AMD Ryzen 7</SelectItem>
                              <SelectItem value="AMD Ryzen 9">AMD Ryzen 9</SelectItem>
                              <SelectItem value="Apple M1">Apple M1</SelectItem>
                              <SelectItem value="Apple M2">Apple M2</SelectItem>
                              <SelectItem value="Apple M3">Apple M3</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>RAM (GB)</Label>
                          <Select value={String(formData.ram)} onValueChange={(v) => setFormData({ ...formData, ram: parseInt(v) })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0">Unknown</SelectItem>
                              <SelectItem value="4">4 GB</SelectItem>
                              <SelectItem value="8">8 GB</SelectItem>
                              <SelectItem value="12">12 GB</SelectItem>
                              <SelectItem value="16">16 GB</SelectItem>
                              <SelectItem value="24">24 GB</SelectItem>
                              <SelectItem value="32">32 GB</SelectItem>
                              <SelectItem value="64">64 GB</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Storage (GB)</Label>
                          <Select value={String(formData.storage)} onValueChange={(v) => setFormData({ ...formData, storage: parseInt(v) })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0">Unknown</SelectItem>
                              <SelectItem value="128">128 GB</SelectItem>
                              <SelectItem value="256">256 GB</SelectItem>
                              <SelectItem value="512">512 GB</SelectItem>
                              <SelectItem value="1024">1 TB</SelectItem>
                              <SelectItem value="2048">2 TB</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>GPU</Label>
                          <Select value={formData.gpu} onValueChange={(v) => setFormData({ ...formData, gpu: v })}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select GPU" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Integrated">Integrated</SelectItem>
                              <SelectItem value="NVIDIA GTX 1650">NVIDIA GTX 1650</SelectItem>
                              <SelectItem value="NVIDIA RTX 3050">NVIDIA RTX 3050</SelectItem>
                              <SelectItem value="NVIDIA RTX 3060">NVIDIA RTX 3060</SelectItem>
                              <SelectItem value="NVIDIA RTX 4050">NVIDIA RTX 4050</SelectItem>
                              <SelectItem value="NVIDIA RTX 4060">NVIDIA RTX 4060</SelectItem>
                              <SelectItem value="AMD Radeon">AMD Radeon</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </>
                    )}

                    {/* Laptop Boolean Features */}
                    <div className="col-span-2 grid grid-cols-2 gap-3 mt-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_ssd}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_ssd: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">SSD Storage</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_gaming}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_gaming: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Gaming Laptop</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_touchscreen}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_touchscreen: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Touchscreen</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_backlit_keyboard}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_backlit_keyboard: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Backlit Keyboard</Label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Furniture Fields */}
                {formData.category === 'furniture' && (
                  <div className="grid grid-cols-2 gap-4">
                    {/* Fallback Static Dropdowns */}
                    {Object.keys(dropdownOptions).length === 0 && (
                      <>
                        <div>
                          <Label>Material *</Label>
                          <Select value={formData.material} onValueChange={(v) => setFormData({ ...formData, material: v })} required>
                            <SelectTrigger>
                              <SelectValue placeholder="Select material" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="wood">General Wood</SelectItem>
                              <SelectItem value="solid_wood">Solid Wood</SelectItem>
                              <SelectItem value="sheesham">Sheesham / Rosewood</SelectItem>
                              <SelectItem value="teak">Teak Wood</SelectItem>
                              <SelectItem value="oak">Oak Wood</SelectItem>
                              <SelectItem value="walnut">Walnut</SelectItem>
                              <SelectItem value="mahogany">Mahogany</SelectItem>
                              <SelectItem value="mdf">MDF / Engineered Wood</SelectItem>
                              <SelectItem value="metal">Metal</SelectItem>
                              <SelectItem value="stainless_steel">Stainless Steel</SelectItem>
                              <SelectItem value="glass">Glass</SelectItem>
                              <SelectItem value="fabric">Fabric</SelectItem>
                              <SelectItem value="velvet">Velvet</SelectItem>
                              <SelectItem value="leather">Genuine Leather</SelectItem>
                              <SelectItem value="faux_leather">Faux / PU Leather</SelectItem>
                              <SelectItem value="marble">Marble</SelectItem>
                              <SelectItem value="rattan">Rattan / Bamboo</SelectItem>
                              <SelectItem value="other">Other</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Brand (Optional)</Label>
                          <Select value={formData.furniture_brand} onValueChange={(v) => setFormData({ ...formData, furniture_brand: v })}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select brand" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">Unknown/Local</SelectItem>
                              <SelectItem value="interwood">Interwood</SelectItem>
                              <SelectItem value="habitt">Habitt</SelectItem>
                              <SelectItem value="ikea">IKEA</SelectItem>
                              <SelectItem value="chiniot">Chiniot Craft</SelectItem>
                              <SelectItem value="urban_solo">Urban Solo</SelectItem>
                              <SelectItem value="other">Other Designer</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Furniture Type</Label>
                          <Select value={formData.furniture_type} onValueChange={(v) => setFormData({ ...formData, furniture_type: v, furniture_subtype: '' })}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select furniture type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="sofa">Sofa</SelectItem>
                              <SelectItem value="chair">Chair</SelectItem>
                              <SelectItem value="table">Table</SelectItem>
                              <SelectItem value="bed">Bed</SelectItem>
                              <SelectItem value="wardrobe">Wardrobe</SelectItem>
                              <SelectItem value="desk">Desk</SelectItem>
                              <SelectItem value="cabinet">Cabinet</SelectItem>
                              <SelectItem value="shelf">Shelf</SelectItem>
                              <SelectItem value="dressing_table">Dressing Table</SelectItem>
                              <SelectItem value="tv_unit">TV Unit</SelectItem>
                              <SelectItem value="other">Other</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        {/* Dynamic Sub-type based on Furniture Type */}
                        {formData.furniture_type && (
                          <div>
                            <Label>
                              {formData.furniture_type === 'bed' ? 'Bed Size' :
                                formData.furniture_type === 'table' ? 'Table Type' :
                                  formData.furniture_type === 'sofa' ? 'Sofa Type' :
                                    formData.furniture_type === 'chair' ? 'Chair Type' :
                                      formData.furniture_type === 'wardrobe' ? 'Wardrobe Size' :
                                        formData.furniture_type === 'desk' ? 'Desk Type' :
                                          formData.furniture_type === 'cabinet' ? 'Cabinet Type' :
                                            formData.furniture_type === 'shelf' ? 'Shelf Type' :
                                              formData.furniture_type === 'dressing_table' ? 'Dressing Table Type' :
                                                formData.furniture_type === 'tv_unit' ? 'TV Unit Type' :
                                                  'Sub-type'}
                            </Label>
                            <Select value={formData.furniture_subtype} onValueChange={(v) => setFormData({ ...formData, furniture_subtype: v })}>
                              <SelectTrigger>
                                <SelectValue placeholder="Select size/type" />
                              </SelectTrigger>
                              <SelectContent>
                                {/* Bed sizes */}
                                {formData.furniture_type === 'bed' && (
                                  <>
                                    <SelectItem value="single">Single Bed</SelectItem>
                                    <SelectItem value="double">Double Bed</SelectItem>
                                    <SelectItem value="queen">Queen Size</SelectItem>
                                    <SelectItem value="king">King Size</SelectItem>
                                    <SelectItem value="bunk">Bunk Bed</SelectItem>
                                  </>
                                )}
                                {/* Table types */}
                                {formData.furniture_type === 'table' && (
                                  <>
                                    <SelectItem value="dining_4">Dining Table (4 Person)</SelectItem>
                                    <SelectItem value="dining_6">Dining Table (6 Person)</SelectItem>
                                    <SelectItem value="dining_8">Dining Table (8 Person)</SelectItem>
                                    <SelectItem value="coffee">Coffee Table</SelectItem>
                                    <SelectItem value="side">Side Table</SelectItem>
                                    <SelectItem value="console">Console Table</SelectItem>
                                    <SelectItem value="study">Study Table</SelectItem>
                                  </>
                                )}
                                {/* Sofa types */}
                                {formData.furniture_type === 'sofa' && (
                                  <>
                                    <SelectItem value="2_seater">2 Seater</SelectItem>
                                    <SelectItem value="3_seater">3 Seater</SelectItem>
                                    <SelectItem value="5_seater">5 Seater</SelectItem>
                                    <SelectItem value="7_seater">7 Seater</SelectItem>
                                    <SelectItem value="l_shaped">L-Shaped</SelectItem>
                                    <SelectItem value="sectional">Sectional</SelectItem>
                                    <SelectItem value="sofa_cum_bed">Sofa Cum Bed</SelectItem>
                                    <SelectItem value="recliner">Recliner Sofa</SelectItem>
                                  </>
                                )}
                                {/* Chair types */}
                                {formData.furniture_type === 'chair' && (
                                  <>
                                    <SelectItem value="dining">Dining Chair</SelectItem>
                                    <SelectItem value="office">Office Chair</SelectItem>
                                    <SelectItem value="gaming">Gaming Chair</SelectItem>
                                    <SelectItem value="rocking">Rocking Chair</SelectItem>
                                    <SelectItem value="accent">Accent Chair</SelectItem>
                                    <SelectItem value="bean_bag">Bean Bag</SelectItem>
                                  </>
                                )}
                                {/* Wardrobe sizes */}
                                {formData.furniture_type === 'wardrobe' && (
                                  <>
                                    <SelectItem value="2_door">2 Door</SelectItem>
                                    <SelectItem value="3_door">3 Door</SelectItem>
                                    <SelectItem value="4_door">4 Door</SelectItem>
                                    <SelectItem value="sliding">Sliding Door</SelectItem>
                                    <SelectItem value="walk_in">Walk-in Closet</SelectItem>
                                  </>
                                )}
                                {/* Desk types */}
                                {formData.furniture_type === 'desk' && (
                                  <>
                                    <SelectItem value="computer">Computer Desk</SelectItem>
                                    <SelectItem value="executive">Executive Desk</SelectItem>
                                    <SelectItem value="standing">Standing Desk</SelectItem>
                                    <SelectItem value="writing">Writing Desk</SelectItem>
                                    <SelectItem value="l_shaped">L-Shaped Desk</SelectItem>
                                  </>
                                )}
                                {/* Cabinet types */}
                                {formData.furniture_type === 'cabinet' && (
                                  <>
                                    <SelectItem value="kitchen">Kitchen Cabinet</SelectItem>
                                    <SelectItem value="bathroom">Bathroom Cabinet</SelectItem>
                                    <SelectItem value="storage">Storage Cabinet</SelectItem>
                                    <SelectItem value="display">Display Cabinet</SelectItem>
                                    <SelectItem value="filing">Filing Cabinet</SelectItem>
                                  </>
                                )}
                                {/* Shelf types */}
                                {formData.furniture_type === 'shelf' && (
                                  <>
                                    <SelectItem value="bookshelf">Bookshelf</SelectItem>
                                    <SelectItem value="wall_shelf">Wall Shelf</SelectItem>
                                    <SelectItem value="corner">Corner Shelf</SelectItem>
                                    <SelectItem value="floating">Floating Shelf</SelectItem>
                                    <SelectItem value="shoe_rack">Shoe Rack</SelectItem>
                                  </>
                                )}
                                {/* Dressing Table types */}
                                {formData.furniture_type === 'dressing_table' && (
                                  <>
                                    <SelectItem value="with_mirror">With Mirror</SelectItem>
                                    <SelectItem value="with_storage">With Storage</SelectItem>
                                    <SelectItem value="vanity">Vanity Set</SelectItem>
                                    <SelectItem value="simple">Simple</SelectItem>
                                  </>
                                )}
                                {/* TV Unit types */}
                                {formData.furniture_type === 'tv_unit' && (
                                  <>
                                    <SelectItem value="wall_mount">Wall Mount</SelectItem>
                                    <SelectItem value="floor_standing">Floor Standing</SelectItem>
                                    <SelectItem value="entertainment_center">Entertainment Center</SelectItem>
                                    <SelectItem value="simple">Simple</SelectItem>
                                  </>
                                )}
                                {/* Other or unselected */}
                                {formData.furniture_type === 'other' && (
                                  <>
                                    <SelectItem value="other">Other</SelectItem>
                                  </>
                                )}
                              </SelectContent>
                            </Select>
                          </div>
                        )}

                        <div>
                          <Label>Seating Capacity (if applicable)</Label>
                          <Select value={String(formData.seating_capacity)} onValueChange={(v) => setFormData({ ...formData, seating_capacity: parseInt(v) })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="0">N/A</SelectItem>
                              <SelectItem value="1">1 Seater</SelectItem>
                              <SelectItem value="2">2 Seater</SelectItem>
                              <SelectItem value="3">3 Seater</SelectItem>
                              <SelectItem value="4">4 Seater</SelectItem>
                              <SelectItem value="5">5 Seater</SelectItem>
                              <SelectItem value="6">6 Seater</SelectItem>
                              <SelectItem value="7">7 Seater</SelectItem>
                              <SelectItem value="8">8+ Seater</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </>
                    )}

                    {/* Furniture Boolean Features */}
                    <div className="col-span-2 grid grid-cols-2 gap-3 mt-4 border-t pt-4">
                      <h4 className="col-span-2 text-sm font-semibold text-gray-700">Premium Features</h4>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_imported}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_imported: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Imported Furniture</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_handmade}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_handmade: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Handmade / Artisan</Label>
                      </div>

                      {formData.furniture_type === 'wardrobe' && (
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            checked={formData.is_sliding_door}
                            onCheckedChange={(checked) => setFormData({ ...formData, is_sliding_door: checked as boolean })}
                          />
                          <Label className="font-normal cursor-pointer">Sliding Doors</Label>
                        </div>
                      )}

                      {formData.furniture_type === 'bed' && (
                        <div className="col-span-2 space-y-3">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={formData.has_mattress}
                              onCheckedChange={(checked) => setFormData({ ...formData, has_mattress: checked as boolean })}
                            />
                            <Label className="font-normal cursor-pointer">Includes Mattress</Label>
                          </div>
                          {formData.has_mattress && (
                            <div className="pl-6 pt-1">
                              <Label className="text-xs mb-1 block">Mattress Type</Label>
                              <Select value={formData.mattress_type} onValueChange={(v) => setFormData({ ...formData, mattress_type: v })}>
                                <SelectTrigger className="h-8 text-xs">
                                  <SelectValue placeholder="Select mattress type" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="standard">Standard Foam</SelectItem>
                                  <SelectItem value="orthopedic">Orthopedic / Medical</SelectItem>
                                  <SelectItem value="memory_foam">Memory Foam</SelectItem>
                                  <SelectItem value="pocket_spring">Pocket Spring / Luxury</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          )}
                        </div>
                      )}

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.has_storage}
                          onCheckedChange={(checked) => setFormData({ ...formData, has_storage: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">In-built Storage</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_antique}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_antique: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Antique / Vintage</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          checked={formData.is_foldable}
                          onCheckedChange={(checked) => setFormData({ ...formData, is_foldable: checked as boolean })}
                        />
                        <Label className="font-normal cursor-pointer">Foldable</Label>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 3: AI Price Prediction */}
            <div className="space-y-4 border-t pt-6">
              <h3 className="text-lg font-semibold">🤖 Step 3: AI Price Prediction</h3>

              {predicting && (
                <Alert className="bg-blue-50 border-blue-200">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  <AlertDescription className="text-blue-800 ml-2">
                    Analyzing your product and predicting optimal price...
                  </AlertDescription>
                </Alert>
              )}

              {prediction && !predicting && (() => {
                const blendIsLLMDominant = prediction.data_source?.includes('LLM Market Aware');
                const confPct = Math.round((prediction.confidence_score ?? 0) * 100);
                const confColor = confPct >= 75 ? 'bg-green-500' : confPct >= 50 ? 'bg-yellow-500' : 'bg-orange-400';

                return (
                  <div className="rounded-xl border border-green-300 bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 shadow-md overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-green-600 to-emerald-700 px-4 py-3 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-white font-semibold">
                        <Sparkles className="h-4 w-4" />
                        Price Assurance
                      </div>
                      <span className="text-white/80 text-xs">{prediction.data_source || 'AI Powered'}</span>
                    </div>

                    <div className="p-4 space-y-4">
                      {/* Main Price */}
                      <div className="flex items-end justify-between">
                        <div>
                          <p className="text-xs text-green-700 font-medium uppercase tracking-wide">Recommended Price</p>
                          <p className="text-3xl font-extrabold text-green-800">{formatCurrency(prediction.predicted_price)}</p>
                          <p className="text-xs text-green-600 mt-0.5">
                            Range: {formatCurrency(prediction.confidence_lower)} – {formatCurrency(prediction.confidence_upper)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-green-700 font-medium mb-1">AI Confidence</p>
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-green-200 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${confColor}`} style={{ width: `${confPct}%` }} />
                            </div>
                            <span className="text-sm font-bold text-green-800">{confPct}%</span>
                          </div>
                        </div>
                      </div>

                      {/* Price Breakdown */}
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div className="bg-white/70 border border-green-200 rounded-lg p-3">
                          <div className="flex items-center gap-1 mb-1">
                            <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
                            <span className="text-muted-foreground font-medium">OLX Live Market Price</span>
                          </div>
                          <p className="text-base font-bold text-blue-700">
                            {prediction.llm_price ? formatCurrency(prediction.llm_price) : '—'}
                          </p>
                          <p className="text-muted-foreground mt-0.5">From real OLX Pakistan listings</p>
                        </div>
                        <div className="bg-white/70 border border-green-200 rounded-lg p-3">
                          <div className="flex items-center gap-1 mb-1">
                            <span className="w-2 h-2 rounded-full bg-purple-500 inline-block" />
                            <span className="text-muted-foreground font-medium">ML Historical Model</span>
                          </div>
                          <p className="text-base font-bold text-purple-700">
                            {prediction.ml_price ? formatCurrency(prediction.ml_price) : '—'}
                          </p>
                          <p className="text-muted-foreground mt-0.5">From trained dataset patterns</p>
                        </div>
                      </div>

                      {/* Blend indicator */}
                      <div className="bg-white/60 border border-green-100 rounded-lg px-3 py-2 text-xs text-green-800">
                        <span className="font-semibold">Blend: </span>
                        {blendIsLLMDominant
                          ? '70% live OLX market data + 30% ML model (high confidence)'
                          : '30% live OLX data + 70% ML model (lower confidence — limited market data)'}
                      </div>

                      {/* LLM Reasoning */}
                      {prediction.reasoning && (
                        <div className="bg-white/60 border border-emerald-100 rounded-lg p-3 text-xs">
                          <p className="font-semibold text-emerald-800 mb-1">🔍 Market Intelligence</p>
                          <p className="text-green-900 leading-relaxed">{prediction.reasoning}</p>
                        </div>
                      )}

                      {/* Simulated OLX Listings */}
                      {prediction.simulated_market_data && prediction.simulated_market_data.length > 0 && (
                        <div>
                          <button
                            type="button"
                            onClick={() => setShowListings(!showListings)}
                            className="flex items-center gap-1.5 text-xs text-emerald-700 font-medium hover:text-emerald-900 transition-colors"
                          >
                            <span>{showListings ? '▼' : '▶'}</span>
                            {showListings ? 'Hide' : 'Show'} comparable OLX listings ({prediction.simulated_market_data.length})
                          </button>
                          {showListings && (
                            <div className="mt-2 space-y-1.5 max-h-40 overflow-y-auto pr-1">
                              {prediction.simulated_market_data.map((item: any, idx: number) => (
                                <div key={idx} className="flex justify-between items-start bg-white/80 border border-green-200 rounded px-2.5 py-1.5 text-xs">
                                  <span className="text-green-900 flex-1 mr-3">{item.listing}</span>
                                  <span className="font-bold text-green-800 whitespace-nowrap">{formatCurrency(item.price)}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Tips */}
                      {formData.category === 'mobile' && (!formData.ram || !formData.storage) && (
                        <div className="text-xs text-emerald-700 italic bg-emerald-100 px-2.5 py-1.5 rounded">
                          💡 Select {[!formData.ram && 'RAM', !formData.storage && 'Storage'].filter(Boolean).join(' & ')} for a more precise estimate
                        </div>
                      )}
                      {formData.category === 'laptop' && (!formData.processor || !formData.ram) && (
                        <div className="text-xs text-emerald-700 italic bg-emerald-100 px-2.5 py-1.5 rounded">
                          💡 Select {[!formData.processor && 'Processor', !formData.ram && 'RAM'].filter(Boolean).join(' & ')} for a more precise estimate
                        </div>
                      )}
                      {formData.category === 'furniture' && !formData.material && (
                        <div className="text-xs text-emerald-700 italic bg-emerald-100 px-2.5 py-1.5 rounded">
                          💡 Select Material and Furniture Type for a more accurate price estimate
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}

              {predictionError && !predicting && (
                <Alert className="bg-amber-50 border-amber-300">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  <AlertDescription className="text-amber-800 ml-2">
                    {typeof predictionError === 'string' ? predictionError : 'Unable to predict price. Please try again.'}
                  </AlertDescription>
                </Alert>
              )}

              {!titleValidation?.is_valid && formData.title && !predicting && (
                <Alert className="bg-red-50 border-red-300">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <AlertTitle className="text-red-800">Invalid Title</AlertTitle>
                  <AlertDescription className="text-red-700 text-sm">
                    {titleValidation?.message || 'Please provide a valid title with brand and model information.'}
                  </AlertDescription>
                </Alert>
              )}

              {!prediction && !predicting && (() => {
                const missingFields = [];

                if (!formData.title) missingFields.push('Title with brand and model');
                else if (!titleValidation?.is_valid && formData.title) return null; // Error shown above

                if (!formData.condition) missingFields.push('Condition');

                if (formData.category === 'furniture') {
                  const hasDynamicSpecs = Object.keys(dynamicDropdownSelections).length > 0;
                  if (!formData.material && !hasDynamicSpecs) missingFields.push('Material');
                  if (!formData.furniture_type && !hasDynamicSpecs) missingFields.push('Furniture Type');
                } else if (formData.category === 'mobile') {
                  if (!formData.brand) missingFields.push('Brand');
                  if (formData.ram === 0) missingFields.push('RAM (GB)');
                  if (formData.storage === 0) missingFields.push('Storage (GB)');
                } else if (formData.category === 'laptop') {
                  if (!formData.brand) missingFields.push('Brand');
                  if (!formData.processor) missingFields.push('Processor');
                  if (formData.ram === 0) missingFields.push('RAM (GB)');
                }

                if (missingFields.length > 0) {
                  return (
                    <Alert className="bg-blue-50 border-blue-300">
                      <Info className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-blue-700">
                        <strong>Fill required fields to get AI price prediction:</strong>
                        <ul className="list-disc ml-5 mt-2 space-y-1">
                          {missingFields.map((field, idx) => (
                            <li key={idx} className="text-sm">{field}</li>
                          ))}
                        </ul>
                        {formData.category === 'mobile' && (
                          <p className="text-xs mt-3 italic text-blue-600">
                            💡 Optional: Add RAM, Storage, Camera for better accuracy
                          </p>
                        )}
                        {formData.category === 'laptop' && (
                          <p className="text-xs mt-3 italic text-blue-600">
                            💡 Optional: Add Processor, RAM, Storage, GPU for better accuracy
                          </p>
                        )}
                      </AlertDescription>
                    </Alert>
                  );
                }

                return null;
              })()}
            </div>

            {/* Step 4: Set Your Price */}
            <div className="space-y-4 border-t pt-6">
              <h3 className="text-lg font-semibold">💰 Step 4: Set Your Price</h3>

              <div className="space-y-2">
                <Label>Your Price (PKR) *</Label>
                <Input
                  type="number"
                  placeholder="Enter your asking price"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  required
                />
                {prediction && (
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">
                      💡 Recommended: {formatCurrency(prediction.predicted_price)}
                      (±{formatCurrency(prediction.predicted_price - prediction.confidence_lower)})
                    </p>
                    {prediction.allowed_price_min && prediction.allowed_price_max && (
                      <>
                        <p className="text-sm font-medium text-green-700">
                          ✅ Auto-Approval Range: {formatCurrency(prediction.allowed_price_min)} - {formatCurrency(prediction.allowed_price_max)}
                        </p>
                        {formData.price && (
                          Number(formData.price) < prediction.allowed_price_min || Number(formData.price) > prediction.allowed_price_max
                        ) && (
                            <p className="text-sm font-medium text-orange-600 bg-orange-50 p-2 rounded">
                              ⚠️ Price outside auto-approval range. Your listing will be sent for admin review.
                            </p>
                          )}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading || (userVerified === false)}
              className={`w-full ${userVerified === false ? 'bg-gray-400 cursor-not-allowed' : 'bg-[#143109] hover:bg-[#AAAE7F]'}`}
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  {editMode ? 'Updating Listing...' : 'Creating Listing...'}
                </>
              ) : (
                userVerified === false ? 'Verify Email to Post' : (editMode ? 'Update Listing' : 'Create Listing')
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Success Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-2xl">
              <PartyPopper className={`h-6 w-6 ${createdListing?.fraud_flags?.includes('duplicate_detected') ? 'text-amber-600' : 'text-green-600'}`} />
              {createdListing?.fraud_flags?.includes('duplicate_detected') ? 'Listing Under Review' : 'Ad Posted Successfully!'}
            </DialogTitle>
            <DialogDescription>
              {createdListing?.fraud_flags?.includes('duplicate_detected')
                ? 'Your listing has been flagged as a potential duplicate and is pending admin review.'
                : 'Your listing has been created and is now live. Here\'s a preview:'}
            </DialogDescription>
          </DialogHeader>

          {createdListing && (
            <div className="space-y-4 mt-4">
              {/* Preview Card */}
              <Card className="border-2 border-green-200">
                <CardContent className="p-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Image */}
                    <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                      {imagePreviews.length > 0 ? (
                        <img
                          src={imagePreviews[0]}
                          alt={createdListing.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-gray-400">No image</span>
                      )}
                    </div>

                    {/* Details */}
                    <div className="space-y-3">
                      <div>
                        <Badge className="mb-2 font-medium bg-emerald-100 text-emerald-800 border-emerald-200">
                          {createdListing.category}
                        </Badge>
                        <h3 className="text-xl font-bold line-clamp-2">{createdListing.title}</h3>
                        <div className="text-3xl font-bold text-[#143109] text-center mb-6 break-words overflow-hidden max-w-full">
                          {formatCurrency(createdListing.price)}
                        </div>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Condition:</span>
                          <span className="font-medium capitalize">{createdListing.condition}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Location:</span>
                          <span className="font-medium">{createdListing.location}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status:</span>
                          <Badge variant="outline" className={`${createdListing.approval_status === 'approved' ? 'text-green-600 border-green-600' : 'text-yellow-600 border-yellow-600'}`}>
                            {createdListing.approval_status === 'approved' ? 'Live' : 'Pending Approval'}
                          </Badge>
                        </div>
                      </div>

                      <div className="pt-3 border-t">
                        <p className="text-sm text-gray-700 line-clamp-3">
                          {createdListing.description}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Success Message */}
                  <Alert className={`mt-4 ${createdListing.approval_status === 'approved' ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}`}>
                    {createdListing.approval_status === 'approved' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <Info className="h-4 w-4 text-amber-600" />
                    )}
                    <AlertTitle className={createdListing.approval_status === 'approved' ? 'text-green-900' : 'text-amber-900'}>
                      {createdListing.fraud_flags?.includes('duplicate_detected')
                        ? 'Potential Duplicate Detected'
                        : (createdListing.approval_status === 'approved' ? 'Listing Created!' : 'Ad Pending Review')}
                    </AlertTitle>
                    <AlertDescription className={createdListing.approval_status === 'approved' ? 'text-green-700' : 'text-amber-700'}>
                      {createdListing.fraud_flags?.includes('duplicate_detected')
                        ? 'This item looks identical to an existing ad. To prevent spam, our team will manually verify it before it goes live.'
                        : `Your ad is now ${createdListing.approval_status === 'approved' ? 'live and visible to buyers' : 'pending approval by admin'}. You can view it in your dashboard.`}
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={() => navigate(`/product/${createdListing.id}`)}
                  className="flex-1 bg-[#143109] hover:bg-[#AAAE7F]"
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View Listing
                </Button>
                <Button
                  onClick={() => {
                    setShowPreviewDialog(false);
                    navigate('/dashboard');
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  Go to Dashboard
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
