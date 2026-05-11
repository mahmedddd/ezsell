/**
 * FurnitureGLBGenerator â€” v2 Enhanced
 * â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
 * Generates true-to-type, real-scale 3-D furniture GLBs via Three.js.
 *
 * 18 distinct furniture types, each with a fully detailed multi-component
 * geometry: cushions, legs, drawers, doors, shelves, headboards, etc.
 *
 * Type resolution scans THREE text sources in priority order:
 *   1. database `furniture_type` field
 *   2. listing title
 *   3. listing description
 * so the correct model is shown no matter which field the seller filled in.
 *
 * All measurements are in centimetres and converted Ã·100 â†’ metres so the
 * GLB matches 1:1 real-world scale inside WebXR / AR QuickLook.
 */

import * as THREE from 'three';
// @ts-ignore
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';

// â”€â”€â”€ Public Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface FurnitureDimensions {
  /** Depth (front-to-back) in cm */
  l: number;
  /** Width (left-to-right) in cm */
  w: number;
  /** Height in cm */
  h: number;
}

export type FurnitureType =
  | 'sofa'
  | 'armchair'
  | 'chair'
  | 'dining_chair'
  | 'office_chair'
  | 'table'
  | 'dining_table'
  | 'coffee_table'
  | 'desk'
  | 'bed'
  | 'wardrobe'
  | 'bookshelf'
  | 'cabinet'
  | 'dresser'
  | 'ottoman'
  | 'lamp'
  | 'sideboard'
  | 'generic';

/** Human-readable display label for each type (shown in AR UI) */
export const FURNITURE_TYPE_LABELS: Record<FurnitureType, string> = {
  sofa: 'Sofa / Couch',
  armchair: 'Armchair',
  chair: 'Chair',
  dining_chair: 'Dining Chair',
  office_chair: 'Office Chair',
  table: 'Table',
  dining_table: 'Dining Table',
  coffee_table: 'Coffee Table',
  desk: 'Desk',
  bed: 'Bed',
  wardrobe: 'Wardrobe',
  bookshelf: 'Bookshelf',
  cabinet: 'Cabinet',
  dresser: 'Dresser',
  ottoman: 'Ottoman',
  lamp: 'Floor Lamp',
  sideboard: 'Sideboard',
  generic: 'Furniture',
};

/** Real-world default dimensions in cm for each type */
export const FURNITURE_DEFAULTS: Record<FurnitureType, FurnitureDimensions> = {
  sofa: { l: 90, w: 220, h: 85 },
  armchair: { l: 80, w: 85, h: 90 },
  chair: { l: 50, w: 48, h: 88 },
  dining_chair: { l: 50, w: 48, h: 95 },
  office_chair: { l: 65, w: 65, h: 120 },
  table: { l: 80, w: 160, h: 75 },
  dining_table: { l: 90, w: 180, h: 76 },
  coffee_table: { l: 60, w: 120, h: 45 },
  desk: { l: 70, w: 140, h: 75 },
  bed: { l: 210, w: 160, h: 55 },
  wardrobe: { l: 55, w: 120, h: 210 },
  bookshelf: { l: 30, w: 90, h: 180 },
  cabinet: { l: 45, w: 90, h: 90 },
  dresser: { l: 50, w: 110, h: 115 },
  ottoman: { l: 60, w: 70, h: 45 },
  lamp: { l: 40, w: 40, h: 155 },
  sideboard: { l: 48, w: 150, h: 85 },
  generic: { l: 60, w: 80, h: 70 },
};

// â”€â”€â”€ Smart Type Resolution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function matchText(text: string): FurnitureType {
  const t = text.toLowerCase();

  // Coffee/side table BEFORE generic "table"
  if (/coffee[\s-]*table|center[\s-]*table|centre[\s-]*table|side[\s-]*table|end[\s-]*table|tea[\s-]*table/.test(t)) return 'coffee_table';

  // Sofa / couch family
  if (/\bsofa\b|couch|settee|sectional|loveseat|recliner/.test(t)) return 'sofa';

  // Chair variants â€” specific before generic
  if (/arm[\s-]*chair|lounge[\s-]*chair|accent[\s-]*chair|reading[\s-]*chair/.test(t)) return 'armchair';
  if (/office[\s-]*chair|computer[\s-]*chair|gaming[\s-]*chair|task[\s-]*chair|revolving|swivel[\s-]*chair|ergonomic/.test(t)) return 'office_chair';
  if (/dining[\s-]*chair|kitchen[\s-]*chair/.test(t)) return 'dining_chair';
  if (/\bchair\b/.test(t)) return 'chair';

  // Bed family
  if (/\bbed\b|\bmattress\b|\bbunk\b|\bdivan\b|\bcot\b/.test(t)) return 'bed';

  // Storage & shelving â€” specific before generic cabinet
  if (/wardrobe|armoire|closet|almirah|almari/.test(t)) return 'wardrobe';
  if (/book[\s-]*shelf|book[\s-]*case|\bshelv|\brack\b|display[\s-]*unit/.test(t)) return 'bookshelf';
  if (/dresser|chest[\s-]*of[\s-]*draw|draw.*chest|tallboy|highboy/.test(t)) return 'dresser';
  if (/sideboard|buffet|credenza|console[\s-]*(table|unit)/.test(t)) return 'sideboard';
  if (/cabinet|showcase|display[\s-]*cabinet|cupboard/.test(t)) return 'cabinet';

  // Tables â€” specific before generic
  if (/dining[\s-]*table|dinner[\s-]*table/.test(t)) return 'dining_table';
  if (/\bdesk\b|study[\s-]*table|writing[\s-]*table|computer[\s-]*table|workstation/.test(t)) return 'desk';
  if (/\btable\b/.test(t)) return 'table';

  // Misc
  if (/ottoman|pouf|footrest|footstool/.test(t)) return 'ottoman';
  if (/\blamp\b|floor[\s-]*light/.test(t)) return 'lamp';

  return 'generic';
}

/**
 * Resolves the correct 3-D model type from multiple listing fields.
 * Checks each source in priority order and returns the first confident match.
 *
 * @param furnitureTypeField  listing.furniture_type (most reliable)
 * @param listingTitle        listing.title (fallback)
 * @param listingDescription  listing.description (last resort)
 */
export function resolveFurnitureType(
  furnitureTypeField?: string | null,
  listingTitle?: string | null,
  listingDescription?: string | null,
): FurnitureType {
  for (const src of [furnitureTypeField, listingTitle, listingDescription]) {
    if (!src?.trim()) continue;
    const resolved = matchText(src);
    if (resolved !== 'generic') return resolved;
  }
  return 'generic';
}

// â”€â”€â”€ Geometry / Material helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function pbr(color: number, roughness = 0.8, metalness = 0): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness });
}
function box(w: number, h: number, d: number, mat: THREE.Material): THREE.Mesh {
  return new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
}
function cyl(rTop: number, rBot: number, h: number, mat: THREE.Material, segs = 12): THREE.Mesh {
  return new THREE.Mesh(new THREE.CylinderGeometry(rTop, rBot, h, segs), mat);
}
function at(g: THREE.Group, mesh: THREE.Object3D, x: number, y: number, z: number) {
  mesh.position.set(x, y, z); g.add(mesh);
}
function legs4(g: THREE.Group, W: number, D: number, legH: number, legR: number, mat: THREE.Material, inset = 0.06) {
  for (const [xs, zs] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
    const leg = cyl(legR, legR * 1.15, legH, mat);
    leg.position.set(xs * (W / 2 - inset), legH / 2, zs * (D / 2 - inset));
    leg.userData.part = 'leg';
    g.add(leg);
  }
}

/**
 * Tags a mesh/group with its surface role so the material pass can target it.
 * Roles: 'upholstery' | 'cushion' | 'trim' | 'frame' | 'leg' | 'mattress'
 */
function tag<T extends THREE.Object3D>(obj: T, part: string): T {
  obj.userData.part = part;
  return obj;
}

// â”€â”€â”€ SOFA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

// ─── Product Detail Parsing ────────────────────────────────────────────────────
/**
 * Structural details extracted from the full styleHints string
 * (title + description + furniture_subtype + furniture_material DB fields).
 * These drive geometry variations so every listing detail influences the 3-D model.
 */
interface ProductDetails {
  seatCount: number;   // explicit seat count (0 = auto from dims width)
  isLshaped: boolean;  // sofa: L-shaped / corner / sectional
  isRecliner: boolean;  // sofa/chair: includes recliner
  tableSeats: number;   // dining table: explicit seating capacity (0 = auto)
  isRoundTable: boolean;  // table: round / circular / oval top
  isExtendable: boolean;  // table: extendable / foldable leaf
  hasGlassTop: boolean;  // table: glass surface
  shelfCount: number;   // bookshelf: tier count (0 = auto from height)
  drawerRows: number;   // dresser: drawer row count (0 = default 4)
  hasStorage: boolean;  // bed/ottoman: built-in storage
  isRoundOttoman: boolean;  // ottoman: round / pouf shape
}

function parseProductDetails(hints: string): ProductDetails {
  const t = hints.toLowerCase();

  // Seat count: "3 seater", "3-seater", "3 seat"
  const seatM = t.match(/(\d)[\s-]*seater|(\d)[\s-]*seat(?!\s*ing)/);
  const seatCount = seatM ? parseInt(seatM[1] ?? seatM[2]!) : 0;

  // Shelf / tier count: "5 shelf", "5 tier", "6 shelves"
  const shelfM = t.match(/(\d+)[\s-]*(?:tier|shelf|shelves)/);
  const shelfCount = shelfM ? parseInt(shelfM[1]!) : 0;

  // Drawer count: "6 drawer chest" → ceil(6/2) = 3 rows of 2 columns
  const drawerM = t.match(/(\d+)[\s-]*drawer/);
  const drawerRows = drawerM ? Math.max(1, Math.round(parseInt(drawerM[1]!) / 2)) : 0;

  // Table seating
  const tableSeatsM = t.match(/(\d+)[\s-]*(?:person|seater|seat)/);
  const tableSeats = tableSeatsM ? parseInt(tableSeatsM[1]!) : 0;

  return {
    seatCount,
    isLshaped: /l[\s-]*shap|corner[\s-]*sofa|sectional/.test(t),
    isRecliner: /recliner/.test(t),
    tableSeats,
    isRoundTable: /\bround\b|circular|\boval\b/.test(t),
    isExtendable: /extendable|extensible|foldable|folding/.test(t),
    hasGlassTop: /glass[\s-]*top|\bglass[\s-]*table\b/.test(t),
    shelfCount,
    drawerRows,
    hasStorage: /with[\s-]*storage|storage[\s-]*bed|\bdivan\b|storage[\s-]*ottoman|box[\s-]*storage/.test(t),
    isRoundOttoman: /\bround\b|circular|\bpouf\b/.test(t),
  };
}

/**
 * Returns a hex colour for a named colour keyword in listing text.
 * Used as fallback primaryColor when image extraction returns the default beige.
 */
function parseNamedColor(text: string): number | null {
  const t = text.toLowerCase();
  if (/\bwhite\b|off[\s-]*white|\bcream\b|\bivory\b/.test(t)) return 0xf0ece4;
  if (/\bblack\b|jet[\s-]*black|\bespresso\b|\bcharcoal\b/.test(t)) return 0x1a1a1a;
  if (/\bgrey\b|\bgray\b/.test(t)) return 0x7a7a7a;
  if (/dark[\s-]*brown|chocolate|mahogany/.test(t)) return 0x4a2a0a;
  if (/\bbrown\b|light[\s-]*brown/.test(t)) return 0x8a5530;
  if (/\bbeige\b|\bsand\b|\bwheat\b/.test(t)) return 0xd4b896;
  if (/\bnavy\b/.test(t)) return 0x1a2060;
  if (/\bblue\b|royal[\s-]*blue/.test(t)) return 0x2060a0;
  if (/\bteal\b|turquoise/.test(t)) return 0x1a8078;
  if (/\bgreen\b|\bolive\b|forest/.test(t)) return 0x2a5a28;
  if (/\bred\b|\bmaroon\b|crimson|burgundy/.test(t)) return 0x7a1818;
  if (/\byellow\b|mustard/.test(t)) return 0xc8a020;
  if (/\bpink\b|\brose\b|\bblush\b/.test(t)) return 0xd08080;
  if (/\borange\b|terracotta/.test(t)) return 0xc05820;
  if (/\bpurple\b|violet|lavender/.test(t)) return 0x704090;
  if (/walnut/.test(t)) return 0x4a2a10;
  if (/\boak\b/.test(t)) return 0xb8905a;
  if (/\bteak\b/.test(t)) return 0x8a5a28;
  if (/sheesham/.test(t)) return 0x6a3a18;
  if (/\bwood\b|wooden|timber/.test(t)) return 0x8a5530;  // generic warm brown wood
  return null;
}

function buildSofa(dims: FurnitureDimensions, d: ProductDetails): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const fabricMat = pbr(0xb8a898, 0.92);
  const cushMat = pbr(0xcab9a8, 0.95);
  const bCushMat = pbr(0xd0c0b0, 0.95);
  const legMat = pbr(0x3d2b1a, 0.65);

  const LEG_H = 0.12, ARM_W = W * 0.09, ARM_H = H * 0.70;
  const SEAT_P = H * 0.20, SEAT_C = H * 0.16;
  const BACK_T = D * 0.20, BACK_H = H * 0.60;
  const INNER = W - ARM_W * 2;
  // Explicit seat count from text beats width-based auto-guess
  const N = d.seatCount > 0
    ? Math.max(1, Math.min(d.seatCount, Math.round(INNER / 0.35)))
    : Math.max(2, Math.min(7, Math.round(INNER / 0.65)));

  // Seat platform
  at(g, tag(box(W, SEAT_P, D, fabricMat), 'upholstery'), 0, LEG_H + SEAT_P / 2, 0);
  // Backrest panel
  at(g, tag(box(W, BACK_H, BACK_T, fabricMat), 'upholstery'), 0, LEG_H + SEAT_P + BACK_H / 2, D / 2 - BACK_T / 2);

  // Armrests + top caps (right arm skipped when L-shaped — chaise connects there)
  for (const s of [-1, 1] as const) {
    if (d.isLshaped && s === 1) continue;
    at(g, tag(box(ARM_W, ARM_H, D, fabricMat), 'upholstery'), s * (W / 2 - ARM_W / 2), LEG_H + ARM_H / 2, 0);
    at(g, tag(box(ARM_W * 1.05, 0.04, D * 1.02, pbr(0xa09080, 0.70)), 'trim'), s * (W / 2 - ARM_W / 2), LEG_H + ARM_H + 0.02, 0);
  }

  // Seat cushions
  const cushW = INNER / N, cushD = D - BACK_T - 0.04;
  for (let i = 0; i < N; i++) {
    const cx = -INNER / 2 + cushW * i + cushW / 2;
    at(g, tag(box(cushW * 0.91, SEAT_C, cushD, cushMat), 'cushion'), cx, LEG_H + SEAT_P + SEAT_C / 2, -BACK_T * 0.1);
  }

  // Back cushions (leaning against backrest)
  const bCH = BACK_H * 0.78, bCD = BACK_T * 0.55;
  for (let i = 0; i < N; i++) {
    const cx = -INNER / 2 + cushW * i + cushW / 2;
    at(g, tag(box(cushW * 0.88, bCH, bCD, bCushMat), 'cushion'), cx, LEG_H + SEAT_P + bCH / 2, D / 2 - BACK_T + bCD / 2);
  }

  legs4(g, W, D, LEG_H, 0.025, legMat);

  // ── L-shaped chaise extension ────────────────────────────────────────────────────
  // The chaise attaches at the RIGHT end of the main sofa and extends deeper.
  if (d.isLshaped) {
    const cW = D + 0.30;          // chaise Z length (deeper than main sofa)
    const cD = W * 0.36;          // chaise X width (one section of seating)
    const cx = W / 2 + cD / 2 - ARM_W * 0.5;  // X: overlaps slightly with right arm stub
    const cz = cW / 2 - D / 2;               // Z: front edge flush with main sofa front

    at(g, tag(box(cD, SEAT_P, cW, fabricMat), 'upholstery'), cx, LEG_H + SEAT_P / 2, cz);
    // Chaise back — outer right wall
    at(g, tag(box(BACK_T, BACK_H, cW, fabricMat), 'upholstery'), cx + cD / 2 - BACK_T / 2, LEG_H + SEAT_P + BACK_H / 2, cz);
    // Chaise seat cushion
    at(g, tag(box(cD - BACK_T - 0.03, SEAT_C, cW * 0.90, cushMat), 'cushion'), cx - BACK_T * 0.5, LEG_H + SEAT_P + SEAT_C / 2, cz);
    // Far-end armrest
    at(g, tag(box(cD - BACK_T, ARM_H * 0.65, ARM_W, fabricMat), 'upholstery'), cx - BACK_T * 0.5, LEG_H + (ARM_H * 0.65) / 2, cz + cW / 2 - ARM_W / 2);
    // Chaise legs
    for (const [xs, zs] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
      const legMesh = tag(cyl(0.025, 0.025, LEG_H, legMat), 'leg');
      legMesh.position.set(cx + xs * (cD / 2 - 0.05), LEG_H / 2, cz + zs * (cW / 2 - 0.05));
      g.add(legMesh);
    }
  }

  return g;
}

// â”€â”€â”€ ARMCHAIR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildArmchair(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const fabricMat = pbr(0x9a8a7a, 0.92);
  const cushMat = pbr(0xb0a090, 0.95);
  const legMat = pbr(0x3d2b1a, 0.65);

  const LEG_H = 0.14, ARM_W = W * 0.11, ARM_H = H * 0.72;
  const SEAT_P = H * 0.22, SEAT_C = H * 0.18;
  const BACK_T = D * 0.22, BACK_H = H * 0.58;
  const INNER = W - ARM_W * 2;

  at(g, tag(box(W, SEAT_P, D, fabricMat), 'upholstery'), 0, LEG_H + SEAT_P / 2, 0);
  at(g, tag(box(W, BACK_H, BACK_T, fabricMat), 'upholstery'), 0, LEG_H + SEAT_P + BACK_H / 2, D / 2 - BACK_T / 2);

  for (const s of [-1, 1] as const) {
    at(g, tag(box(ARM_W, ARM_H, D, fabricMat), 'upholstery'), s * (W / 2 - ARM_W / 2), LEG_H + ARM_H / 2, 0);
    at(g, tag(box(ARM_W * 1.05, 0.035, D * 1.02, pbr(0x806858, 0.75)), 'trim'), s * (W / 2 - ARM_W / 2), LEG_H + ARM_H + 0.017, 0);
  }

  at(g, tag(box(INNER * 0.92, SEAT_C, D - BACK_T - 0.04, cushMat), 'cushion'), 0, LEG_H + SEAT_P + SEAT_C / 2, -BACK_T * 0.1);
  at(g, tag(box(INNER * 0.88, BACK_H * 0.78, BACK_T * 0.55, cushMat), 'cushion'), 0, LEG_H + SEAT_P + BACK_H * 0.78 / 2, D / 2 - BACK_T + BACK_T * 0.55 / 2);

  legs4(g, W, D, LEG_H, 0.022, legMat);
  return g;
}

// â”€â”€â”€ CHAIR (side/accent) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildChair(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const woodMat = pbr(0xc8a060, 0.72);
  const padMat = pbr(0xd0b888, 0.90);

  const SEAT_Y = H * 0.46, SEAT_H = 0.04;
  const BACK_H = H - SEAT_Y - SEAT_H;

  // Seat board + pad
  at(g, tag(box(W, SEAT_H, D, woodMat), 'frame'), 0, SEAT_Y + SEAT_H / 2, 0);
  at(g, tag(box(W * 0.92, SEAT_H * 1.4, D * 0.92, padMat), 'upholstery'), 0, SEAT_Y + SEAT_H * 1.7, 0);

  // Back: 2 vertical side posts
  for (const xs of [-1, 1] as const) {
    at(g, tag(box(0.035, BACK_H, 0.035, woodMat), 'frame'), xs * (W / 2 - 0.025), SEAT_Y + SEAT_H + BACK_H / 2, -(D / 2 - 0.025));
  }
  // 3 horizontal slats
  for (let i = 0; i < 3; i++) {
    at(g, tag(box(W - 0.06, 0.055, 0.025, woodMat), 'frame'), 0, SEAT_Y + SEAT_H + BACK_H * (0.2 + i * 0.3), -(D / 2 - 0.025));
  }

  // 4 tapered legs
  const legH = SEAT_Y;
  for (const [xs, zs] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
    at(g, tag(cyl(0.016, 0.026, legH, woodMat), 'leg'), xs * (W / 2 - 0.03), legH / 2, zs * (D / 2 - 0.03));
  }
  return g;
}

// â”€â”€â”€ DINING CHAIR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildDiningChair(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const woodMat = pbr(0x7a5630, 0.68);
  const seatMat = pbr(0xc0a880, 0.88);

  const SEAT_Y = H * 0.47, BACK_H = H - SEAT_Y - 0.06;

  // Upholstered seat
  at(g, tag(box(W, 0.06, D, seatMat), 'upholstery'), 0, SEAT_Y + 0.03, 0);
  // Back frame + upholstered back panel
  at(g, tag(box(W, BACK_H, 0.04, woodMat), 'frame'), 0, SEAT_Y + 0.06 + BACK_H / 2, -(D / 2 - 0.02));
  at(g, tag(box(W * 0.80, BACK_H * 0.72, 0.055, seatMat), 'upholstery'), 0, SEAT_Y + 0.06 + BACK_H * 0.36, -(D / 2 - 0.045));

  // 4 straight legs
  const legH = SEAT_Y;
  for (const [xs, zs] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
    at(g, tag(cyl(0.02, 0.022, legH, woodMat), 'leg'), xs * (W / 2 - 0.025), legH / 2, zs * (D / 2 - 0.025));
  }
  return g;
}

// â”€â”€â”€ OFFICE CHAIR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildOfficeChair(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const fabricMat = pbr(0x2a2a2a, 0.85);
  const plasticMat = pbr(0x1a1a1a, 0.60, 0.10);
  const metalMat = pbr(0x909090, 0.30, 0.80);

  const SEAT_H = H * 0.40, BACK_H = H * 0.46;
  const baseH = 0.06, poleH = SEAT_H - baseH - 0.04;

  // 5-spoke base
  at(g, tag(new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.27, baseH, 5), plasticMat), 'frame'), 0, baseH / 2, 0);
  // Wheels
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    const w = tag(new THREE.Mesh(new THREE.SphereGeometry(0.034, 6, 4), plasticMat), 'frame');
    w.position.set(Math.cos(a) * 0.25, 0.034, Math.sin(a) * 0.25);
    g.add(w);
  }
  // Gas lift
  at(g, tag(cyl(0.034, 0.04, poleH, metalMat), 'frame'), 0, baseH + poleH / 2, 0);
  // Seat + back
  at(g, tag(box(W, 0.08, D, fabricMat), 'upholstery'), 0, SEAT_H + 0.04, 0);
  at(g, tag(box(W * 0.88, BACK_H, 0.10, fabricMat), 'upholstery'), 0, SEAT_H + 0.08 + BACK_H / 2, -(D / 2 - 0.08));
  // Lumbar bump
  at(g, tag(box(W * 0.58, BACK_H * 0.28, 0.04, pbr(0x333333, 0.9)), 'upholstery'), 0, SEAT_H + 0.08 + BACK_H * 0.24, -(D / 2 - 0.13));
  // Armrests
  for (const s of [-1, 1] as const) {
    at(g, tag(box(0.055, 0.035, D * 0.48, plasticMat), 'frame'), s * (W / 2 + 0.026), SEAT_H + 0.12, 0);
  }
  return g;
}

// â”€â”€â”€ DINING TABLE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildDiningTable(dims: FurnitureDimensions, d: ProductDetails): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const topMat = d.hasGlassTop ? pbr(0xd0e8f0, 0.05, 0.0) : pbr(0xc8a860, 0.55, 0.02);
  const legMat = pbr(0x5c3d1e, 0.60, 0.02);
  const T = 0.04, apronH = 0.065, apronT = 0.03;

  if (d.isRoundTable) {
    // ── Round / pedestal table ──────────────────────────────────────────────
    const radius = Math.max(W, D) / 2;
    const topMesh = tag(new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, T, 32), topMat), 'trim');
    topMesh.position.set(0, H - T / 2, 0);
    g.add(topMesh);
    // Pedestal column
    at(g, tag(cyl(0.06, 0.09, H - T - 0.04, legMat, 12), 'leg'), 0, (H - T - 0.04) / 2, 0);
    // 4-point star base radiating from pedestal
    for (let i = 0; i < 4; i++) {
      const a = (i / 4) * Math.PI * 2;
      const foot = tag(cyl(0.024, 0.024, radius * 0.58, legMat, 8), 'leg');
      foot.rotation.z = Math.PI / 2;
      foot.position.set(Math.cos(a) * radius * 0.29, 0.024, Math.sin(a) * radius * 0.29);
      g.add(foot);
    }
  } else {
    // ── Rectangular table ──────────────────────────────────────────────────
    at(g, tag(box(W, T, D, topMat), 'trim'), 0, H - T / 2, 0);
    // Apron (4 sides)
    at(g, tag(box(W * 0.9, apronH, apronT, legMat), 'frame'), 0, H - T - apronH / 2, D / 2 - apronT / 2);
    at(g, tag(box(W * 0.9, apronH, apronT, legMat), 'frame'), 0, H - T - apronH / 2, -(D / 2 - apronT / 2));
    at(g, tag(box(apronT, apronH, D * 0.9, legMat), 'frame'), W / 2 - apronT / 2, H - T - apronH / 2, 0);
    at(g, tag(box(apronT, apronH, D * 0.9, legMat), 'frame'), -W / 2 + apronT / 2, H - T - apronH / 2, 0);
    // 4 tapered square legs
    const legH = H - T - apronH;
    for (const [xs, zs] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
      at(g, tag(cyl(0.028, 0.038, legH, legMat, 4), 'leg'), xs * (W / 2 - 0.05), legH / 2, zs * (D / 2 - 0.05));
    }
  }
  return g;
}

// â”€â”€â”€ COFFEE TABLE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildCoffeeTable(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const topMat = pbr(0xd4aa70, 0.55, 0.02);
  const legMat = pbr(0x2a1a0a, 0.50, 0.05);
  const T = 0.028, legH = H - T;

  at(g, tag(box(W, T, D, topMat), 'trim'), 0, H - T / 2, 0);

  // Thin hairpin-style legs (distinctive for coffee tables)
  for (const [xs, zs] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
    at(g, tag(cyl(0.016, 0.016, legH, legMat, 8), 'leg'), xs * (W / 2 - 0.06), legH / 2, zs * (D / 2 - 0.06));
  }

  // Lower shelf
  if (H > 0.35) {
    at(g, tag(box(W * 0.82, 0.018, D * 0.82, topMat), 'trim'), 0, H * 0.35, 0);
  }
  return g;
}

// â”€â”€â”€ DESK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildDesk(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const topMat = pbr(0xd4c4a0, 0.60);
  const woodMat = pbr(0xb09060, 0.70);
  const handleMat = pbr(0x909090, 0.30, 0.80);
  const T = 0.03, legH = H - T;

  at(g, tag(box(W, T, D, topMat), 'trim'), 0, H - T / 2, 0);

  // 3 open legs on left + pedestal drawer unit on right
  for (const [xs, zs] of [[-1, -1], [-1, 1], [1, -1]] as const) {
    at(g, tag(cyl(0.024, 0.028, legH, woodMat, 4), 'leg'), xs * (W / 2 - 0.04), legH / 2, zs * (D / 2 - 0.04));
  }

  // Pedestal (right side drawer unit)
  const pedW = W * 0.26, pedH = legH - 0.06, pedD = D * 0.84;
  at(g, tag(box(pedW, pedH, pedD, woodMat), 'frame'), W / 2 - pedW / 2 - 0.01, pedH / 2, 0);

  // 3 drawer fronts on pedestal
  for (let i = 0; i < 3; i++) {
    const dy = pedH * (0.14 + i * 0.3);
    at(g, tag(box(pedW * 0.88, pedH * 0.25, 0.018, topMat), 'trim'), W / 2 - pedW / 2 - 0.01, dy, pedD / 2 + 0.009);
    at(g, tag(box(0.04, 0.01, 0.01, handleMat), 'decorative'), W / 2 - pedW / 2 - 0.01, dy, pedD / 2 + 0.025);
  }
  return g;
}

// â”€â”€â”€ BED â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildBed(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const fabricMat = pbr(0xC09060, 0.93);
  const mattMat = pbr(0xf5f5f0, 0.92);
  const sheetMat = pbr(0xfafaf5, 0.90);
  const pillowMat = pbr(0xfefefe, 0.88);
  const backingMat = pbr(0x8a6040, 0.75);

  const PLATFORM_H = Math.max(0.28, H * 0.48);
  const MATT_H = Math.max(0.18, H * 0.32);
  const HEAD_H = Math.max(0.75, H * 1.25);
  const HEAD_T = 0.14;
  const FOOT_H = PLATFORM_H + 0.08;
  const FOOT_T = HEAD_T * 0.70;

  // ── Platform base ──────────────────────────────────────────────────────────
  at(g, tag(box(W, PLATFORM_H, D, fabricMat), 'upholstery'), 0, PLATFORM_H / 2, 0);

  // ── Side Rails ─────────────────────────────────────────────────────────────
  const railT = 0.08;
  at(g, tag(box(railT, PLATFORM_H * 1.05, D, fabricMat), 'upholstery'), -(W / 2 - railT / 2), PLATFORM_H / 2, 0);
  at(g, tag(box(railT, PLATFORM_H * 1.05, D, fabricMat), 'upholstery'), (W / 2 - railT / 2), PLATFORM_H / 2, 0);

  // ── Mattress ───────────────────────────────────────────────────────────────
  at(g, tag(box(W * 0.92, MATT_H, D * 0.96, mattMat), 'mattress'),
    0, PLATFORM_H + MATT_H / 2, 0);

  // ── Duvet / sheet ──────────────────────────────────────────────────────────
  at(g, tag(box(W * 0.94, MATT_H * 0.45, D * 0.65, sheetMat), 'cushion'),
    0, PLATFORM_H + MATT_H + MATT_H * 0.22, D * 0.10);

  // ── Headboard ──────────────────────────────────────────────────────────────
  const N_HEAD = Math.max(4, Math.round(W / 0.18));
  const hSegW = W / N_HEAD;
  for (let i = 0; i < N_HEAD; i++) {
    const sx = -W / 2 + hSegW * (i + 0.5);
    at(g, tag(box(hSegW * 0.90, HEAD_H, HEAD_T, fabricMat), 'upholstery'),
      sx, HEAD_H / 2, -(D / 2 + HEAD_T / 2));
  }
  at(g, tag(box(W, HEAD_H * 0.98, HEAD_T * 0.20, backingMat), 'frame'),
    0, HEAD_H / 2, -(D / 2 + HEAD_T * 0.95));

  // ── Footboard ──────────────────────────────────────────────────────────────
  const N_FOOT = Math.max(3, Math.round(W / 0.22));
  const fSegW = W / N_FOOT;
  for (let i = 0; i < N_FOOT; i++) {
    const fx = -W / 2 + fSegW * (i + 0.5);
    at(g, tag(box(fSegW * 0.88, FOOT_H, FOOT_T, fabricMat), 'upholstery'),
      fx, FOOT_H / 2, D / 2 + FOOT_T / 2);
  }

  // ── Pillows (Dynamic Count based on Width) ─────────────────────────────────
  const nPillows = W < 1.1 ? 1 : (W > 1.9 ? 3 : 2);
  const pillW = Math.min(0.65, W * 0.35), pillH = 0.14, pillD = 0.30;
  const pillSpacing = W / (nPillows + 1);
  for (let i = 0; i < nPillows; i++) {
    const px = -W / 2 + pillSpacing * (i + 1);
    at(g, tag(box(pillW, pillH, pillD, pillowMat), 'mattress'),
      px, PLATFORM_H + MATT_H + pillH / 2, -(D / 2 - pillD / 2 - 0.12));
  }
  return g;
}

// ─── WARDROBE ──────────────────────────────────────────────────────────────────

/**
 * Extracts door count from styleHints text (underscores already normalised to
 * spaces by WebARViewer).  Falls back to a width-based heuristic.
 */
function parseDoorCount(text: string, widthM: number): number {
  const t = text.toLowerCase();
  if (/6[\s-]*door|six[\s-]*door/.test(t)) return 6;
  if (/5[\s-]*door|five[\s-]*door/.test(t)) return 5;
  if (/4[\s-]*door|four[\s-]*door/.test(t)) return 4;
  if (/3[\s-]*door|three[\s-]*door/.test(t)) return 3;
  if (/2[\s-]*door|two[\s-]*door/.test(t)) return 2;
  if (/sliding/.test(t)) return 2;  // sliding = 2 panels
  if (/walk[\s-]*in/.test(t)) return 0;  // no front doors
  // Width-based fallback
  if (widthM >= 2.5) return 5;
  if (widthM >= 2.0) return 4;
  if (widthM >= 1.55) return 3;
  return 2;
}

function buildWardrobe(dims: FurnitureDimensions, nDoors: number): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  // Dark warm-wood defaults — overridden by product canvas / k-means colour
  const bodyMat = pbr(0x7a4520, 0.65);
  const doorMat = pbr(0x8a5228, 0.62, 0.04);
  const handleMat = pbr(0xb8b8bc, 0.22, 0.88);  // brushed silver
  const t = 0.022;

  const footH = 0.060;
  const bH = H - footH;
  const cy = footH + bH / 2;

  // ── Carcass panels (all 'frame' → receive primary product colour) ──────────
  at(g, tag(box(W, bH, t, bodyMat), 'frame'), 0, cy, -(D / 2 - t / 2));  // back
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), -(W / 2 - t / 2), cy, 0);           // left side
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), (W / 2 - t / 2), cy, 0);           // right side
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, H - t / 2, 0);              // top
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, footH + t / 2, 0);                  // bottom

  // Thin vertical dividers between door bays
  if (nDoors > 1) {
    const doorWDiv = (W - t * (nDoors + 1)) / nDoors;
    for (let i = 1; i < nDoors; i++) {
      const divX = -W / 2 + t * (i + 0.5) + doorWDiv * i;
      at(g, tag(box(t, bH * 0.99, D * 0.18, bodyMat), 'frame'), divX, cy, D / 2 - D * 0.09);
    }
  }

  if (nDoors === 0) {
    // Walk-in: base plinth only, no front doors
    at(g, tag(box(W + 0.02, footH, D + 0.015, pbr(0x3a1a08, 0.75)), 'frame'), 0, footH / 2, 0);
    return g;
  }

  // ── Door panels + arch handles ────────────────────────────────────────────
  const doorW = (W - t * (nDoors + 1)) / nDoors;
  const doorH = bH * 0.990;
  const doorT = 0.020;

  for (let i = 0; i < nDoors; i++) {
    const dx = -W / 2 + t * (i + 1) + doorW * (i + 0.5);

    // Door face — 'trim' → receives primary colour (wood grain texture)
    at(g, tag(box(doorW, doorH, doorT, doorMat), 'trim'), dx, footH + doorH / 2 + t, D / 2 + doorT / 2);

    // Arch/C-shape handle: two vertical arms + one horizontal crossbar at top
    // Opening side: left-half doors open right, right-half doors open left
    const openSide = (i < nDoors / 2) ? 1 : -1;
    const hx = dx + openSide * (doorW * 0.28);
    const hy = footH + bH * 0.57;
    const archH = 0.110;
    const armGap = 0.011;  // gap between the two vertical arms
    const hz = D / 2 + doorT + 0.015;

    // Left vertical arm
    at(g, tag(cyl(0.005, 0.005, archH, handleMat, 8), 'decorative'), hx - armGap / 2, hy, hz);
    // Right vertical arm
    at(g, tag(cyl(0.005, 0.005, archH, handleMat, 8), 'decorative'), hx + armGap / 2, hy, hz);
    // Top horizontal crossbar (cylinder rotated 90° around Z)
    const crossBar = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, armGap + 0.010, 8), handleMat);
    crossBar.rotation.z = Math.PI / 2;
    crossBar.position.set(hx, hy + archH / 2, hz);
    crossBar.userData.part = 'decorative';
    g.add(crossBar);

    // Lock — small disc below handle
    at(g, tag(cyl(0.011, 0.011, 0.013, handleMat, 8), 'decorative'), hx, footH + bH * 0.43, D / 2 + doorT + 0.007);
  }

  // ── Base plinth (flat-base style — no visible legs) ───────────────────────
  at(g, tag(box(W + 0.02, footH, D + 0.015, pbr(0x3a1a08, 0.75)), 'frame'), 0, footH / 2, 0);
  return g;
}

// â”€â”€â”€ BOOKSHELF â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildBookshelf(dims: FurnitureDimensions, d: ProductDetails): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const woodMat = pbr(0xc8a060, 0.68);
  const t = 0.022;
  // Shelf count: explicit from text (e.g. "5 tier") beats height-based auto
  const N = d.shelfCount > 0 ? d.shelfCount : Math.max(3, Math.round(H / 0.30));
  const gap = (H - t * 2) / N;

  // Side panels + back + top + bottom
  at(g, tag(box(t, H, D, woodMat), 'frame'), -(W / 2 - t / 2), H / 2, 0);
  at(g, tag(box(t, H, D, woodMat), 'frame'), (W / 2 - t / 2), H / 2, 0);
  at(g, tag(box(W, H, 0.01, woodMat), 'frame'), 0, H / 2, -(D / 2 - 0.005));
  at(g, tag(box(W - t * 2, t, D, woodMat), 'frame'), 0, H - t / 2, 0);
  at(g, tag(box(W - t * 2, t, D, woodMat), 'frame'), 0, t / 2, 0);

  const bookColors = [0xe74c3c, 0x3498db, 0x27ae60, 0xf39c12, 0x8e44ad, 0x16a085, 0xe67e22, 0x2980b9];

  for (let i = 1; i < N; i++) {
    const sy = t + gap * i;
    at(g, tag(box(W - t * 2, t, D, woodMat), 'frame'), 0, sy, 0);

    // Rows of books — tagged 'decoration' to skip color override (preserve their colorful spines)
    let bx = -(W / 2 - t - 0.02);
    for (let b = 0; b < 30; b++) {
      const bW = 0.022 + Math.random() * 0.018;
      const bH = gap * 0.58 + Math.random() * gap * 0.22;
      const book = tag(box(bW, bH, D * 0.72, pbr(bookColors[b % bookColors.length], 0.85)), 'decoration_skip');
      book.position.set(bx + bW / 2, sy - t / 2 - (gap - bH) / 2 - bH / 2, 0);
      g.add(book);
      bx += bW + 0.004;
      if (bx > W / 2 - t) break;
    }
  }
  return g;
}

// ─── CABINET ───────────────────────────────────────────────────────────────────

function buildCabinet(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const bodyMat = pbr(0xc8aa80, 0.68);
  const doorMat = pbr(0xd4b888, 0.55, 0.03);
  const handleMat = pbr(0xb0b0b0, 0.30, 0.80);
  const t = 0.020;

  const footH = 0.07;
  const bH = H - footH;
  const cy = footH + bH / 2;

  // Body
  at(g, tag(box(W, bH, t, bodyMat), 'frame'), 0, cy, -(D / 2 - t / 2));
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), -(W / 2 - t / 2), cy, 0);
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), (W / 2 - t / 2), cy, 0);
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, H - t / 2, 0);
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, footH + t / 2, 0);
  at(g, tag(box(W - t * 2, t, D - t * 2, bodyMat), 'frame'), 0, cy, 0);

  // 2 doors
  const doorW = (W - t * 3) / 2, doorT = 0.018;
  for (const [s, hs] of [[-1, -1], [1, 1]] as [number, number][]) {
    const dx = s * W / 4;
    at(g, tag(box(doorW, bH * 0.97, doorT, doorMat), 'trim'), dx, cy, D / 2 + doorT / 2);
    at(g, tag(box(0.010, 0.085, 0.010, handleMat), 'decorative'), dx - hs * doorW * 0.32, cy, D / 2 + doorT + 0.012);
  }

  // Small feet
  legs4(g, W, D, footH, 0.018, pbr(0x4a3520, 0.7), 0.04);
  return g;
}

// ─── DRESSER ───────────────────────────────────────────────────────────────────

function buildDresser(dims: FurnitureDimensions, d: ProductDetails): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const bodyMat = pbr(0xd4aa70, 0.65);
  const drawerMat = pbr(0xdcb878, 0.52, 0.02);
  const handleMat = pbr(0xc0c0c0, 0.25, 0.85);
  const t = 0.020;

  const footH = 0.06;
  const bH = H - footH;
  const cy = footH + bH / 2;
  // Drawer rows: explicit from text (e.g. "6 drawer" → 3 rows) beats default 4
  const N_ROWS = d.drawerRows > 0 ? d.drawerRows : 4;
  const drawH = (bH - t * (N_ROWS + 1)) / N_ROWS;

  // Body
  at(g, tag(box(W, bH, t, bodyMat), 'frame'), 0, cy, -(D / 2 - t / 2));
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), -(W / 2 - t / 2), cy, 0);
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), (W / 2 - t / 2), cy, 0);
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, H - t / 2, 0);
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, footH + t / 2, 0);
  // Overhanging top surface
  at(g, tag(box(W + 0.02, t * 1.6, D + 0.02, pbr(0xdcb878, 0.48, 0.03)), 'trim'), 0, H + t * 0.8, 0);

  // Drawer fronts (2 columns × 4 rows)
  const dFW = (W - t * 3) / 2;
  for (let row = 0; row < N_ROWS; row++) {
    const dy = footH + t + row * (drawH + t) + drawH / 2;
    for (const col of [-1, 1] as const) {
      const dx = col * W / 4;
      at(g, tag(box(dFW * 0.91, drawH * 0.84, 0.018, drawerMat), 'trim'), dx, dy, D / 2 + 0.009);
      at(g, tag(box(0.04, 0.011, 0.011, handleMat), 'decorative'), dx, dy, D / 2 + 0.024);
    }
  }

  legs4(g, W, D, footH, 0.016, pbr(0x3a2510, 0.7), 0.04);
  return g;
}

// ─── OTTOMAN ───────────────────────────────────────────────────────────────────

function buildOttoman(dims: FurnitureDimensions, d: ProductDetails): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const fabricMat = pbr(0x8a7a6a, 0.90);
  const topMat = pbr(0xa09080, 0.92);
  const legMat = pbr(0x2a1a0a, 0.60);

  const LEG_H = 0.08, BODY_H = H * 0.70, TOP_H = H - LEG_H - BODY_H;

  if (d.isRoundOttoman) {
    // ── Round pouf / circular ottoman ────────────────────────────────────────
    const radius = Math.min(W, D) / 2;
    at(g, tag(new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, BODY_H, 24), fabricMat), 'upholstery'), 0, LEG_H + BODY_H / 2, 0);
    at(g, tag(new THREE.Mesh(new THREE.CylinderGeometry(radius + 0.015, radius + 0.015, TOP_H + 0.015, 24), topMat), 'cushion'), 0, LEG_H + BODY_H + (TOP_H + 0.015) / 2, 0);
    at(g, tag(box(0.07, 0.014, 0.07, pbr(0x706050, 0.95)), 'trim'), 0, LEG_H + BODY_H + TOP_H + 0.02, 0);
    legs4(g, W, D, LEG_H, 0.018, legMat, 0.055);
  } else {
    // ── Rectangular ottoman ───────────────────────────────────────────────────
    at(g, tag(box(W, BODY_H, D, fabricMat), 'upholstery'), 0, LEG_H + BODY_H / 2, 0);
    at(g, tag(box(W + 0.03, TOP_H + 0.03, D + 0.03, topMat), 'cushion'), 0, LEG_H + BODY_H + (TOP_H + 0.03) / 2, 0);
    at(g, tag(box(0.07, 0.014, 0.07, pbr(0x706050, 0.95)), 'trim'), 0, LEG_H + BODY_H + TOP_H + 0.04, 0);
    legs4(g, W, D, LEG_H, 0.018, legMat, 0.055);
  }
  return g;
}

// ─── FLOOR LAMP ────────────────────────────────────────────────────────────────

function buildLamp(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const H = dims.h / 100;

  const metalMat = pbr(0x909090, 0.30, 0.85);
  const baseMat = pbr(0x888888, 0.40, 0.70);
  const shadeMat = pbr(0xfff3d0, 0.80);

  at(g, tag(new THREE.Mesh(new THREE.CylinderGeometry(0.23, 0.27, 0.05, 16), baseMat), 'frame'), 0, 0.025, 0);

  const poleH = H * 0.76;
  at(g, tag(cyl(0.014, 0.014, poleH, metalMat, 12), 'frame'), 0, 0.05 + poleH / 2, 0);

  // Shade (open-bottom truncated cone) — tagged decoration_skip to preserve warm amber color
  const shade = tag(new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.27, 0.34, 16, 1, true), shadeMat), 'decoration_skip');
  shade.position.set(0, H * 0.76 + 0.05 + 0.17, 0);
  g.add(shade);
  // Shade top cap
  at(g, tag(new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.012, 16), metalMat), 'frame'), 0, H * 0.76 + 0.05 + 0.34, 0);

  // Glowing bulb — always preserve emissive, skip color override
  const bulb = tag(new THREE.Mesh(
    new THREE.SphereGeometry(0.038, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xffffcc, emissive: 0xffee88, emissiveIntensity: 1.6 })
  ), 'decoration_skip');
  bulb.position.set(0, H * 0.76 + 0.05 + 0.06, 0);
  g.add(bulb);
  return g;
}

// ─── SIDEBOARD ─────────────────────────────────────────────────────────────────

function buildSideboard(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;

  const bodyMat = pbr(0xb89870, 0.62);
  const doorMat = pbr(0xc8a878, 0.52, 0.04);
  const handleMat = pbr(0xd4aa40, 0.20, 0.90);   // gold handles
  const t = 0.022;

  const legH = 0.14;
  const bH = H - legH;
  const cy = legH + bH / 2;

  at(g, tag(box(W, bH, t, bodyMat), 'frame'), 0, cy, -(D / 2 - t / 2));
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), -(W / 2 - t / 2), cy, 0);
  at(g, tag(box(t, bH, D, bodyMat), 'frame'), (W / 2 - t / 2), cy, 0);
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, H - t / 2, 0);
  at(g, tag(box(W, t, D, bodyMat), 'frame'), 0, legH + t / 2, 0);
  at(g, tag(box(W - t * 2, t, D - t * 2, bodyMat), 'frame'), 0, cy, 0);

  // 4 door panels (2 pairs)
  const nD = W > 1.2 ? 4 : 2;
  const doorW = (W - t * (nD + 1)) / nD, doorT = 0.018;
  for (let i = 0; i < nD; i++) {
    const dx = -W / 2 + t * (i + 1) + doorW * (i + 0.5);
    at(g, tag(box(doorW, bH * 0.97, doorT, doorMat), 'trim'), dx, cy, D / 2 + doorT / 2);
    // Horizontal bar handle
    at(g, tag(box(doorW * 0.38, 0.010, 0.010, handleMat), 'decorative'), dx, cy, D / 2 + doorT + 0.012);
  }

  // Tapered legs (4)
  for (const [xs, zs] of [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const) {
    at(g, tag(cyl(0.019, 0.028, legH, pbr(0x5c3d1e, 0.60), 4), 'leg'), xs * (W / 2 - 0.06), legH / 2, zs * (D / 2 - 0.06));
  }
  return g;
}

// â”€â”€â”€ GENERIC â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildGeneric(dims: FurnitureDimensions): THREE.Group {
  const g = new THREE.Group();
  const W = dims.w / 100, D = dims.l / 100, H = dims.h / 100;
  // Single body block — tagged 'frame' so the hard-furniture branch applies
  // the product primary colour + image-derived roughness to the whole surface.
  at(g, tag(box(W, H, D, pbr(0xd4b896, 0.80)), 'frame'), 0, H / 2, 0);
  return g;
}

// â”€â”€â”€ Dispatcher â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function buildFurnitureGroup(type: FurnitureType, dims: FurnitureDimensions, styleHints = ''): THREE.Group {
  const d = parseProductDetails(styleHints);
  switch (type) {
    case 'sofa': return buildSofa(dims, d);
    case 'armchair': return buildArmchair(dims);
    case 'chair': return buildChair(dims);
    case 'dining_chair': return buildDiningChair(dims);
    case 'office_chair': return buildOfficeChair(dims);
    case 'table': return buildDiningTable(dims, d);
    case 'dining_table': return buildDiningTable(dims, d);
    case 'coffee_table': return buildCoffeeTable(dims);
    case 'desk': return buildDesk(dims);
    case 'bed': return buildBed(dims);
    case 'wardrobe': return buildWardrobe(dims, parseDoorCount(styleHints, dims.w / 100));
    case 'bookshelf': return buildBookshelf(dims, d);
    case 'cabinet': return buildCabinet(dims);
    case 'dresser': return buildDresser(dims, d);
    case 'ottoman': return buildOttoman(dims, d);
    case 'lamp': return buildLamp(dims);
    case 'sideboard': return buildSideboard(dims);
    default: return buildGeneric(dims);
  }
}

// --- Smart Dimension Resolver ---

export function resolveSmartDimensions(
  type: FurnitureType,
  title?: string | null,
  description?: string | null,
): FurnitureDimensions {
  const text = `${title ?? ''} ${description ?? ''}`.toLowerCase();

  // ── Robust Dimension Parser (extracts 72x78, 6x6.5 ft, etc.) ────────────────
  // Looks for common patterns: [val] x [val] [unit]
  const dimRegex = /(\d+(?:\.\d+)?)\s*(?:x|by|\*)\s*(\d+(?:\.\d+)?)\s*(ft|feet|in|inch|cm|m)?/i;
  const match = text.match(dimRegex);
  if (match) {
    let w = parseFloat(match[1]);
    let l = parseFloat(match[2]);
    const unit = (match[3] || '').toLowerCase();

    // Normalise to CM
    if (unit === 'ft' || unit === 'feet') { w *= 30.48; l *= 30.48; }
    else if (unit === 'in' || unit === 'inch') { w *= 2.54; l *= 2.54; }
    else if (unit === 'm') { w *= 100; l *= 100; }

    // Sanity Check: If they specified 72x78 without units, it's almost certainly inches
    if (!unit && w > 12 && w < 100 && l > 12 && l < 100) { w *= 2.54; l *= 2.54; }
    // If they specified 6x6.5 without units, it's feet
    if (!unit && w < 12 && l < 12) { w *= 30.48; l *= 30.48; }

    if (w > 10 && l > 10) {
      return { w: Math.round(w), l: Math.round(l), h: FURNITURE_DEFAULTS[type].h };
    }
  }

  if (type === 'bed') {
    if (/king[\s-]*size|king[\s-]*bed|\bking\b/.test(text)) return { l: 203, w: 193, h: 55 };
    if (/queen[\s-]*size|queen[\s-]*bed|\bqueen\b/.test(text)) return { l: 200, w: 153, h: 55 };
    if (/double[\s-]*bed|full[\s-]*size|\bdouble\b/.test(text)) return { l: 190, w: 135, h: 55 };
    if (/single[\s-]*bed|twin[\s-]*bed|\bsingle\b|\btwin\b/.test(text)) return { l: 190, w: 90, h: 55 };
  }

  if (type === 'sofa' || type === 'armchair') {
    if (/7[\s-]*seater|seven[\s-]*seater/.test(text)) return { l: 98, w: 380, h: 90 };
    if (/6[\s-]*seater|six[\s-]*seater/.test(text)) return { l: 96, w: 340, h: 88 };
    if (/5[\s-]*seater|five[\s-]*seater/.test(text)) return { l: 95, w: 310, h: 87 };
    if (/4[\s-]*seater|four[\s-]*seater/.test(text)) return { l: 92, w: 260, h: 87 };
    if (/3[\s-]*seater|three[\s-]*seater/.test(text)) return { l: 90, w: 220, h: 85 };
    if (/2[\s-]*seater|two[\s-]*seater|loveseat/.test(text)) return { l: 90, w: 160, h: 85 };
    if (/1[\s-]*seater|one[\s-]*seater|single[\s-]*seater/.test(text)) return { l: 85, w: 95, h: 90 };
  }

  if (type === 'dining_table' || type === 'table') {
    if (/10[\s-]*seater|ten[\s-]*person/.test(text)) return { l: 100, w: 300, h: 76 };
    if (/8[\s-]*seater|eight[\s-]*person|8[\s-]*person/.test(text)) return { l: 100, w: 240, h: 76 };
    if (/6[\s-]*seater|six[\s-]*person|6[\s-]*person/.test(text)) return { l: 90, w: 180, h: 76 };
    if (/4[\s-]*seater|four[\s-]*person|4[\s-]*person/.test(text)) return { l: 85, w: 130, h: 76 };
    if (/2[\s-]*seater|two[\s-]*person|2[\s-]*person/.test(text)) return { l: 75, w: 80, h: 76 };
    if (/round|circular/.test(text)) return { l: 110, w: 110, h: 76 };
  }

  if (type === 'wardrobe') {
    if (/6[\s-]*door|six[\s-]*door/.test(text)) return { l: 60, w: 360, h: 210 };
    if (/5[\s-]*door|five[\s-]*door/.test(text)) return { l: 59, w: 300, h: 210 };
    if (/4[\s-]*door|four[\s-]*door/.test(text)) return { l: 58, w: 240, h: 210 };
    if (/3[\s-]*door|three[\s-]*door/.test(text)) return { l: 58, w: 180, h: 210 };
    if (/2[\s-]*door|two[\s-]*door/.test(text)) return { l: 55, w: 120, h: 210 };
  }

  return FURNITURE_DEFAULTS[type];
}

// ─── Product Image Texture ────────────────────────────────────────────────────
/**
 * Loads a product image URL as a Three.js Texture that can be applied to
 * fabric / upholstery surfaces.  Returns null on CORS or network failure so
 * the caller can fall back gracefully.
 */
function loadProductTexture(imageUrl: string): Promise<THREE.Texture | null> {
  return new Promise((resolve) => {
    const loader = new THREE.TextureLoader();
    loader.crossOrigin = 'anonymous';
    loader.load(
      imageUrl,
      (tex) => {
        tex.wrapS = THREE.RepeatWrapping;
        tex.wrapT = THREE.RepeatWrapping;
        // Tile 2×2 so the image becomes a tiled fabric/material swatch rather
        // than a stretched photograph.
        tex.repeat.set(2, 2);
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.needsUpdate = true;
        resolve(tex);
      },
      undefined,
      () => resolve(null),      // silently ignore CORS / 404 errors
    );
  });
}

// ─── CORS-safe image loader ────────────────────────────────────────────────────
/**
 * Loads an image URL into an HTMLCanvasElement using the fetch() → Blob → blobURL
 * pipeline.  This completely bypasses the browser-canvas CORS taint restriction
 * that occurs when a product image is first displayed (without crossOrigin) and
 * then re-loaded with img.crossOrigin='anonymous' — the browser serves the cached
 * version which lacks CORS headers, taints the canvas, and silently fails.
 *
 * fetch() has its own separate cache that always requests (and receives) CORS
 * headers when the server is configured correctly (FastAPI CORSMiddleware covers
 * all routes including mounted StaticFiles).  The resulting blobURL is same-origin
 * so the canvas is never tainted.
 *
 * Falls back to the direct crossOrigin img approach if fetch() itself fails.
 */
async function loadImageSafe(url: string, size: number): Promise<HTMLCanvasElement | null> {
  // Primary: fetch → blob → blobURL → canvas (CORS-taint-free)
  try {
    const resp = await fetch(url, { mode: 'cors', credentials: 'include' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const blob = await resp.blob();
    const blobUrl = URL.createObjectURL(blob);
    return await new Promise<HTMLCanvasElement | null>((resolve) => {
      const img = new Image();
      img.onload = () => {
        URL.revokeObjectURL(blobUrl);
        const c = document.createElement('canvas');
        c.width = size; c.height = size;
        const ctx = c.getContext('2d', { willReadFrequently: true });
        if (!ctx) { resolve(null); return; }
        ctx.drawImage(img, 0, 0, size, size);
        resolve(c);
      };
      img.onerror = () => { URL.revokeObjectURL(blobUrl); resolve(null); };
      img.src = blobUrl;
    });
  } catch {
    // Fallback: direct crossOrigin img (works when CORS headers are present but fetch failed)
    return new Promise<HTMLCanvasElement | null>((resolve) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        try {
          const c = document.createElement('canvas');
          c.width = size; c.height = size;
          const ctx = c.getContext('2d', { willReadFrequently: true });
          if (!ctx) { resolve(null); return; }
          ctx.drawImage(img, 0, 0, size, size);
          resolve(c);
        } catch { resolve(null); }
      };
      img.onerror = () => resolve(null);
      img.src = url;
    });
  }
}

// ─── Color Profile ─────────────────────────────────────────────────────────────
/**
 * Full colour analysis result extracted from a product image.
 * Used to drive both the primary fabric colour AND secondary metallic/wood trim.
 */
export interface ColorProfile {
  /** Dominant fabric / upholstery colour (hex, e.g. 0xb8a070 for caramel brown) */
  primaryColor: number;
  /** Secondary trim / frame / leg colour (e.g. 0xc8a020 for gold) */
  accentColor: number;
  /** True when a gold or silver metallic cluster was detected */
  hasMetal: boolean;
  /** True specifically when the metallic cluster is gold-hued (not silver) */
  isGold: boolean;
  /**
   * Surface smoothness inferred from intra-cluster pixel variance.
   * 0 = ultra-matte/velvet, 1 = mirror-gloss leather/lacquer.
   * Used to override keyword-based roughness guessing.
   */
  glossiness: number;
  /** True when the dominant palette is warm (amber, tan, brown, terracotta) */
  isWarm: boolean;
  /** True when the furniture is predominantly dark (charcoal, espresso, navy) */
  isDark: boolean;
  /**
   * Third distinct product colour detected (e.g. contrast piping, stitching,
   * decorative buttons). Applied to 'decorative' tagged meshes.
   */
  tertiaryColor?: number;
}

const _FALLBACK_PROFILE: ColorProfile = {
  primaryColor: 0xb8a898,
  accentColor: 0x5c3d1e,
  hasMetal: false,
  isGold: false,
  glossiness: 0.10,
  isWarm: true,
  isDark: false,
};

/**
 * V3 — Analyses a product image using:
 *  - k=8 k-means clustering with 12 iterations on a 128-px canvas
 *  - Corner-pixel background removal (walls/floors excluded from primary)
 *  - Intra-cluster variance → glossiness score (leather=high, velvet=low)
 *  - Warmth & darkness detection from dominant cluster hue/luma
 *  - Tertiary colour for piping, stitching, contrast legs
 */
export function extractColorProfile(imageUrl: string): Promise<ColorProfile> {
  return loadImageSafe(imageUrl, 128).then((canvas): ColorProfile => {
    if (!canvas) return { ..._FALLBACK_PROFILE };
    try {
      const S = 128;
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (!ctx) return { ..._FALLBACK_PROFILE };

      // ── Step 1: Sample all 4 corners to detect background colour ──────────
      const CORNER = Math.floor(S * 0.09);
      const full = ctx.getImageData(0, 0, S, S).data;
      let bgR = 0, bgG = 0, bgB = 0, bgN = 0;
      for (let y = 0; y < CORNER; y++) {
        for (let x = 0; x < CORNER; x++) {
          for (const [py, px] of [
            [y, x], [y, S - 1 - x],
            [S - 1 - y, x], [S - 1 - y, S - 1 - x],
          ] as [number, number][]) {
            const i = (py * S + px) * 4;
            bgR += full[i]; bgG += full[i + 1]; bgB += full[i + 2]; bgN++;
          }
        }
      }
      if (bgN > 0) { bgR /= bgN; bgG /= bgN; bgB /= bgN; }

      // ── Step 2: Collect product pixels (crop 12% margins, skip extremes) ──
      const M = Math.floor(S * 0.12);
      const CW = S - M * 2, CH = S - M * 2;
      const { data } = ctx.getImageData(M, M, CW, CH);
      const pixels: [number, number, number][] = [];
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const luma = 0.299 * r + 0.587 * g + 0.114 * b;
        if (luma < 22 || luma > 232) continue;
        pixels.push([r, g, b]);
      }
      if (pixels.length < 30) { return { ..._FALLBACK_PROFILE }; }

      // ── Step 3: K-means k=8, 12 iterations ───────────────────────────────
      const k = 8;
      let centroids = Array.from({ length: k }, (_, i) =>
        [...pixels[Math.floor((i + 0.5) * pixels.length / k)]] as [number, number, number],
      );
      for (let iter = 0; iter < 12; iter++) {
        const sums: [number, number, number, number][] = Array.from({ length: k }, () => [0, 0, 0, 0]);
        for (const [r, g, b] of pixels) {
          let best = 0, bestD = Infinity;
          for (let c = 0; c < k; c++) {
            const dr = r - centroids[c][0], dg = g - centroids[c][1], db = b - centroids[c][2];
            const d = dr * dr + dg * dg + db * db;
            if (d < bestD) { bestD = d; best = c; }
          }
          sums[best][0] += r; sums[best][1] += g; sums[best][2] += b; sums[best][3]++;
        }
        centroids = sums.map(([sr, sg, sb, n], ci) =>
          n > 0 ? [Math.round(sr / n), Math.round(sg / n), Math.round(sb / n)] : centroids[ci],
        );
      }

      // ── Step 4: Count membership + measure intra-cluster variance ─────────
      const counts = new Array(k).fill(0);
      const varSums = new Array(k).fill(0);
      for (const [r, g, b] of pixels) {
        let best = 0, bestD = Infinity;
        for (let c = 0; c < k; c++) {
          const dr = r - centroids[c][0], dg = g - centroids[c][1], db = b - centroids[c][2];
          const d = dr * dr + dg * dg + db * db;
          if (d < bestD) { bestD = d; best = c; }
        }
        counts[best]++;
        varSums[best] += bestD;
      }
      // Weighted-average intra-cluster variance (weighted by cluster size)
      let totalVar = 0, totalW = 0;
      for (let c = 0; c < k; c++) {
        if (counts[c] > 0) {
          totalVar += (varSums[c] / counts[c]) * counts[c];
          totalW += counts[c];
        }
      }
      const avgVariance = totalW > 0 ? totalVar / totalW : 800;
      // avgDist ≈ sqrt(avgVariance): ~10-15 = very smooth, ~45-60 = heavily textured
      const avgDist = Math.sqrt(avgVariance);
      const glossiness = Math.max(0, Math.min(1, 1 - (avgDist - 8) / 54));

      // ── Step 5: HSL helpers ───────────────────────────────────────────────
      function rgbToHsl([r, g, b]: [number, number, number]): [number, number, number] {
        const rn = r / 255, gn = g / 255, bn = b / 255;
        const max = Math.max(rn, gn, bn), min = Math.min(rn, gn, bn);
        const l = (max + min) / 2;
        if (max === min) return [0, 0, l];
        const d = max - min;
        const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        const h = max === rn ? ((gn - bn) / d + (gn < bn ? 6 : 0)) / 6
          : max === gn ? ((bn - rn) / d + 2) / 6
            : ((rn - gn) / d + 4) / 6;
        return [h * 360, s, l];
      }
      function colorDist2(a: [number, number, number], b: [number, number, number]): number {
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;
      }
      function isGoldCluster(c: [number, number, number]): boolean {
        const [h, s, l] = rgbToHsl(c);
        return h >= 22 && h <= 58 && s > 0.28 && l > 0.28 && l < 0.84;
      }
      function isSilverCluster(c: [number, number, number]): boolean {
        const [, s, l] = rgbToHsl(c);
        return s < 0.12 && l > 0.45 && l < 0.88;
      }
      function isMetallic(c: [number, number, number]): boolean {
        return isGoldCluster(c) || isSilverCluster(c);
      }

      // ── Step 6: Background cluster detection ──────────────────────────────
      const bg: [number, number, number] = [bgR, bgG, bgB];
      function isBackgroundCluster(c: [number, number, number], n: number): boolean {
        const distToBg = Math.sqrt(colorDist2(c, bg));
        const luma = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2];
        const [, sat] = rgbToHsl(c);
        // Background: very close to corner colour, OR a large neutral/white area
        return distToBg < 38 || (n / pixels.length > 0.25 && luma > 178 && sat < 0.14);
      }

      // ── Step 7: Sort clusters and exclude background ──────────────────────
      const allClusters = centroids
        .map((c, i) => ({ c, n: counts[i], v: varSums[i] / Math.max(1, counts[i]) }))
        .sort((a, b) => b.n - a.n);

      const productClusters = allClusters.filter(cl => !isBackgroundCluster(cl.c, cl.n));
      const clusters = productClusters.length >= 2 ? productClusters : allClusters;

      const toHex = ([r, g, b]: [number, number, number]) => (r << 16) | (g << 8) | b;

      // ── Step 8: Metallic detection + primary / accent assignment ──────────
      let primaryC = clusters[0].c;
      let accentC = clusters[1]?.c ?? clusters[0].c;
      let hasMetal = false, isGold = false;

      for (const { c } of clusters) {
        if (isGoldCluster(c)) { hasMetal = true; isGold = true; accentC = c; break; }
        if (isSilverCluster(c)) { hasMetal = true; accentC = c; break; }
      }
      if (hasMetal) {
        for (const { c } of clusters) {
          if (!isMetallic(c)) { primaryC = c; break; }
        }
      } else {
        for (const { c } of clusters.slice(1)) {
          if (colorDist2(c, primaryC) > 1600) { accentC = c; break; }
        }
      }

      // ── Step 9: Tertiary colour (contrast piping / stitching / buttons) ───
      let tertiaryColor: number | undefined;
      for (const { c } of clusters.slice(2)) {
        if (isMetallic(c)) continue;
        if (colorDist2(c, primaryC) > 2500 && colorDist2(c, accentC) > 2500) {
          tertiaryColor = toHex(c); break;
        }
      }

      // ── Step 10: Warmth and darkness ─────────────────────────────────────
      const pLuma = 0.299 * primaryC[0] + 0.587 * primaryC[1] + 0.114 * primaryC[2];
      const isDark = pLuma < 80;
      const [pH, pS] = rgbToHsl(primaryC);
      const isWarm = (pH >= 18 && pH <= 85 && pS > 0.07) || (pH <= 18 && pS > 0.10);

      return {
        primaryColor: toHex(primaryC), accentColor: toHex(accentC), hasMetal, isGold,
        glossiness, isWarm, isDark, tertiaryColor
      };
    } catch { return { ..._FALLBACK_PROFILE }; }
  });
}

/** Backward-compatible wrapper (returns just the primary colour number). */
export function extractDominantColor(imageUrl: string): Promise<number> {
  return extractColorProfile(imageUrl).then(p => p.primaryColor);
}

/**
 * Analyses ALL listing images in parallel and merges them into one profile.
 *
 * Why this is more accurate than a single image:
 *  - Multiple angles expose different surfaces (close-up reveals trim colour)
 *  - Gold/metallic details visible in detail shots but not overview are captured
 *  - Averaged primary reduces lighting-cast colour bias from any one photo
 *  - Glossiness averaged across angles smooths lighting artefacts
 *
 * Up to 4 images are processed (additional images have diminishing returns).
 */
export async function extractColorProfileMulti(imageUrls: string[]): Promise<ColorProfile> {
  if (!imageUrls.length) return { ..._FALLBACK_PROFILE };
  if (imageUrls.length === 1) return extractColorProfile(imageUrls[0]);

  const urls = imageUrls.slice(0, 4);
  const profiles = await Promise.all(
    urls.map(u => extractColorProfile(u).catch((): ColorProfile => ({ ..._FALLBACK_PROFILE }))),
  );

  // Metallic wins: if any image shows gold/silver, use that accent
  const metalProfile = profiles.find(p => p.hasMetal);
  const hasMetal = !!metalProfile;
  const isGold = !!metalProfile?.isGold;
  const accentColor = metalProfile?.accentColor ?? profiles[0].accentColor;

  // Primary: first image = 50% weight, remaining images split the other 50%
  const weights = urls.map((_, i) => (i === 0 ? 0.50 : 0.50 / (urls.length - 1)));
  let rS = 0, gS = 0, bS = 0;
  profiles.forEach((p, i) => {
    rS += ((p.primaryColor >> 16) & 0xff) * weights[i];
    gS += ((p.primaryColor >> 8) & 0xff) * weights[i];
    bS += (p.primaryColor & 0xff) * weights[i];
  });
  const primaryColor = (Math.round(rS) << 16) | (Math.round(gS) << 8) | Math.round(bS);

  // Scalar fields: averages / majority vote
  const glossiness = profiles.reduce((s, p) => s + p.glossiness, 0) / profiles.length;
  const warmCount = profiles.filter(p => p.isWarm).length;
  const darkCount = profiles.filter(p => p.isDark).length;
  const isWarm = warmCount >= Math.ceil(profiles.length / 2);
  const isDark = darkCount >= Math.ceil(profiles.length / 2);
  const tertiaryColor = profiles.find(p => p.tertiaryColor)?.tertiaryColor;

  return { primaryColor, accentColor, hasMetal, isGold, glossiness, isWarm, isDark, tertiaryColor };
}

/**
 * Loads the product image as a 512×512 canvas using the CORS-safe fetch-blob method.
 *
 * The returned canvas is passed to generateFurnitureGLB as `productCanvas` where it
 * becomes a THREE.CanvasTexture tiled across every upholstery/cushion surface.  This
 * gives the 3D model the actual fabric colour AND texture character (velvet pile,
 * woven grain, leather sheen) directly from the product photograph — far more
 * accurate than k-means flat-colour matching alone.
 *
 * Returns null when the image cannot be loaded (network failure, unreachable host).
 */
export function extractProductCanvas(imageUrl: string): Promise<HTMLCanvasElement | null> {
  return loadImageSafe(imageUrl, 512);
}

/**
 * Detects the material roughness and type from listing keywords.
 * Drives the fabric roughness value applied to 'upholstery' meshes.
 */
function detectMaterialStyle(text: string): { roughness: number; isLeather: boolean; metalness?: number; isHardMaterial?: boolean } {
  const t = text.toLowerCase();
  // ─ Soft upholstery materials ─────────────────────────────────────────────────────────
  if (/velvet|velour/.test(t)) return { roughness: 0.98, isLeather: false };
  if (/\bleather\b|leatherette|faux.{0,6}leather|pu.{0,4}leather/.test(t)) return { roughness: 0.42, isLeather: true };
  if (/suede/.test(t)) return { roughness: 0.97, isLeather: false };
  if (/linen|woven|tweed|cotton/.test(t)) return { roughness: 0.95, isLeather: false };
  // ─ Hard structural materials ──────────────────────────────────────────────────────
  if (/stainless|steel|\biron\b|\bmetal\b|chrome|aluminum|aluminium/.test(t))
    return { roughness: 0.28, isLeather: false, metalness: 0.88, isHardMaterial: true };
  if (/\bglass\b|tempered[\ s-]*glass/.test(t))
    return { roughness: 0.08, isLeather: false, metalness: 0, isHardMaterial: true };
  if (/marble|granite/.test(t))
    return { roughness: 0.18, isLeather: false, metalness: 0, isHardMaterial: true };
  if (/\bwood\b|wooden|walnut|teak|\boak\b|mahogany|sheesham|mdf|chipboard|plywood|hardwood|sheesham/.test(t))
    return { roughness: 0.62, isLeather: false, metalness: 0, isHardMaterial: true };
  if (/rattan|wicker|cane/.test(t))
    return { roughness: 0.90, isLeather: false, metalness: 0, isHardMaterial: true };
  if (/plastic|polypropylene/.test(t))
    return { roughness: 0.55, isLeather: false, metalness: 0, isHardMaterial: true };
  return { roughness: 0.92, isLeather: false };
}

export async function generateFurnitureGLB(
  type: FurnitureType,
  dims: FurnitureDimensions,
  prevUrl?: string,
  options?: {
    /** Dominant fabric colour (hex) from extractColorProfile / extractColorProfileMulti */
    primaryColor?: number;
    /** Trim / frame / leg colour — gold hex when hasMetal */
    accentColor?: number;
    /** True when a metallic cluster was detected */
    hasMetal?: boolean;
    /** True when the metallic cluster is specifically gold */
    isGold?: boolean;
    /**
     * Image-derived surface smoothness (0=ultra-matte velvet, 1=mirror-gloss leather).
     * Overrides keyword roughness guessing unless an explicit material keyword is found.
     */
    glossiness?: number;
    /** Warm (amber/brown/tan) palette — drives warm-wood default when no accent detected */
    isWarm?: boolean;
    /** Dark furniture (charcoal/espresso/navy) — applies stronger lerp to keep darkness */
    isDark?: boolean;
    /** Third distinct product colour for piping / stitching / decorative detail meshes */
    tertiaryColor?: number;
    /** Listing title + description — explicit material keywords (velvet/leather/suede) */
    styleHints?: string;
    /** Product image URL (reserved) */
    imageUrl?: string;
    /**
     * 512×512 canvas loaded from the product image via CORS-safe fetch
     * (see extractProductCanvas).  When provided, a tiled THREE.CanvasTexture
     * is applied to every upholstery/cushion mesh so the 3D model displays
     * the actual fabric colour and texture pattern from the product photo.
     */
    productCanvas?: HTMLCanvasElement;
  },
): Promise<string> {
  if (prevUrl) URL.revokeObjectURL(prevUrl);

  const scene = new THREE.Scene();
  const group = buildFurnitureGroup(type, dims, options?.styleHints ?? '');

  // ── Floor-snap: bake the Y=0 origin directly into the geometry vertices ──
  // AR QuickLook (iOS) often ignores top-level node translations when converting
  // from GLB. If we just shift `group.position.y`, the object still floats.
  // Instead, we compute the bounding box and physically shift all vertices
  // so the lowest point of the geometry is mathematically at Y=0.
  {
    const bbox = new THREE.Box3().setFromObject(group);
    if (isFinite(bbox.min.y) && bbox.min.y !== 0) {
      const offset = -bbox.min.y;
      group.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (mesh.geometry) {
            mesh.geometry.translate(0, offset, 0);
          }
        }
      });
      // Recompute bounding boxes after geometry mutation
      const newBbox = new THREE.Box3().setFromObject(group);
      group.userData.bbox = newBbox;
    }
  }


  // 0xb8a898 is the _FALLBACK_PROFILE grey — used when CORS blocks image extraction.
  // Treat it as "no color" so builders can use their own material-accurate defaults
  // (e.g. dark brown 0x7a4520 for wood wardrobes) rather than always looking grey.
  const _FALLBACK_HEX = 0xb8a898;
  const primaryIsDefaultFallback = options?.primaryColor === _FALLBACK_HEX;

  // Named-colour hint derived from listing text — used as fallback when the
  // k-means extraction returns neutral/grey (background contamination) or the
  // fallback constant.  Covers wood, upholstery colours, material keywords.
  const _namedColorHex = parseNamedColor(options?.styleHints ?? '');

  // Build the primary THREE.Color:
  //  1. If image primary is the exact fallback grey → skip image, use named keyword colour
  //  2. If image primary is very unsaturated (near-grey, likely background) → same
  //  3. Otherwise use the image-extracted primary
  let primary: THREE.Color | null = null;
  if (!primaryIsDefaultFallback && options?.primaryColor !== undefined) {
    const rawPrimary = new THREE.Color(options.primaryColor);
    const hslCheck = { h: 0, s: 0, l: 0 };
    rawPrimary.getHSL(hslCheck);
    if (hslCheck.s < 0.06) {
      // Near-grey primary (sat < 6%) — likely the neutral background was dominant.
      // Use named keyword colour if available; otherwise null (builder keeps its defaults).
      primary = _namedColorHex !== null ? new THREE.Color(_namedColorHex) : null;
    } else {
      primary = rawPrimary;
    }
  } else if (primaryIsDefaultFallback || options?.primaryColor === undefined) {
    // Fallback grey or no image — prefer keyword colour, else null → builder defaults
    primary = _namedColorHex !== null ? new THREE.Color(_namedColorHex) : null;
  }

  const accent = options?.accentColor !== undefined ? new THREE.Color(options.accentColor) : null;
  const tertiary = options?.tertiaryColor !== undefined ? new THREE.Color(options.tertiaryColor) : null;
  const hasMetal = options?.hasMetal ?? false;
  const isGold = options?.isGold ?? false;
  const isWarm = options?.isWarm ?? true;
  const isDark = options?.isDark ?? false;
  const imgGloss = options?.glossiness ?? -1;   // -1 = not provided

  // Rich gold and cool silver constants for metallic trim
  const goldColor = new THREE.Color(0xc8a020);
  const silverColor = new THREE.Color(0xa8b0bc);

  // ── Material resolution: image glossiness + keyword hints ─────────────────────
  const kwStyle = detectMaterialStyle(options?.styleHints ?? '');
  const hintText = (options?.styleHints ?? '').toLowerCase();
  const hasExplicitMaterial = /velvet|velour|leather|leatherette|faux.{0,6}leather|pu.{0,4}leather|suede|linen|woven|tweed|cotton|stainless|steel|\biron\b|\bmetal\b|chrome|\bglass\b|marble|granite|\bwood\b|wooden|walnut|teak|\boak\b|mahogany|sheesham|mdf|chipboard|rattan|wicker|plastic/.test(hintText);

  let fabricRoughness: number;
  let isLeather: boolean;

  if (hasExplicitMaterial) {
    // Explicit keyword → definitive, ignore image
    fabricRoughness = kwStyle.roughness;
    isLeather = kwStyle.isLeather;
  } else if (imgGloss >= 0) {
    if (imgGloss > 0.70) {
      // Tight pixel clusters → smooth leather / PU / lacquered surface
      fabricRoughness = 0.35 + (1 - imgGloss) * 0.28;
      isLeather = true;
    } else if (imgGloss < 0.08) {
      // Loose pixel clusters → velvet / microfiber
      fabricRoughness = 0.97;
      isLeather = false;
    } else {
      // Mid-range → standard woven fabric
      fabricRoughness = 0.85 + 0.13 * (1 - imgGloss);
      isLeather = false;
    }
  } else {
    fabricRoughness = kwStyle.roughness;
    isLeather = kwStyle.isLeather;
  }
  // Hard-material metalness — applied to structural parts of non-upholstered furniture
  // (e.g. stainless steel dining set, metal frame bed, glass top table)
  const hardMetalness = (kwStyle.isHardMaterial && (kwStyle.metalness ?? 0) > 0)
    ? (kwStyle.metalness ?? 0) : 0;

  // ── Fabric texture from product image (CORS-safe blob approach) ───────────────
  // Tiling the product photo 3×3 across upholstery surfaces gives authentic fabric
  // colour AND texture character (velvet pile, woven grain) that flat colour cannot.
  let fabricTex: THREE.CanvasTexture | null = null;
  if (options?.productCanvas) {
    fabricTex = new THREE.CanvasTexture(options.productCanvas);
    fabricTex.wrapS = THREE.RepeatWrapping;
    fabricTex.wrapT = THREE.RepeatWrapping;
    fabricTex.repeat.set(1.5, 1.5); // Less repetition = more natural grain
    fabricTex.anisotropy = 8; // Sharp textures from side angles
    fabricTex.colorSpace = THREE.SRGBColorSpace;
    fabricTex.needsUpdate = true;
  }

  // ── Per-mesh material application ─────────────────────────────────────────────
  // Detect whether this builder has ANY upholstered surfaces (sofa, chair, bed, ottoman).
  // If yes  → frame / trim / leg are structural wood/metal parts → use accent shade.
  // If no   → frame / trim / leg ARE the dominant visual surface (table top, wardrobe body)
  //           → use primary colour + image-derived roughness.
  let hasUpholsteryParts = false;
  group.traverse((obj: THREE.Object3D) => {
    if ((obj as THREE.Mesh).isMesh) {
      const p = (obj.userData.part as string | undefined) ?? '';
      if (p === 'upholstery' || p === 'cushion') hasUpholsteryParts = true;
    }
  });

  if (primary || accent || hasMetal || imgGloss >= 0 || fabricTex) {
    group.traverse((obj: THREE.Object3D) => {
      if (!(obj as THREE.Mesh).isMesh) return;
      const mesh = obj as THREE.Mesh;
      const part = (mesh.userData.part as string | undefined) ?? '';
      // Skip meshes intentionally excluded from color override (book spines, lamp shades, bulbs)
      if (part === 'decoration_skip') return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];

      (mats as THREE.MeshStandardMaterial[]).forEach((mat) => {
        if (!mat?.isMeshStandardMaterial) return;

        const luma = mat.color.r * 0.299 + mat.color.g * 0.587 + mat.color.b * 0.114;
        const isNearWhite = luma > 0.88;
        const isAlreadyMetal = mat.metalness > 0.5;

        // ── upholstery / cushion → fabric texture OR full solid colour + roughness ──
        if (part === 'upholstery' || part === 'cushion') {
          if (fabricTex) {
            mat.map = fabricTex;
            mat.color.set(0xffffff);   // white tint = texture drives colour fully
          } else if (primary) {
            mat.color.copy(primary);   // full copy — no bleed from default base colour
          }
          mat.roughness = fabricRoughness;
          mat.metalness = isLeather ? 0.03 : 0.0;

          // ── trim / decorative → gold, silver, tertiary piping, primary or accent ─
        } else if (part === 'trim' || part === 'decorative') {
          if (hasMetal && isGold) { mat.color.copy(goldColor); mat.roughness = 0.17; mat.metalness = 0.90; }
          else if (hasMetal) { mat.color.copy(silverColor); mat.roughness = 0.22; mat.metalness = 0.85; }
          else if (part === 'decorative' && tertiary) { mat.color.lerp(tertiary, 0.88); }
          else if (!hasUpholsteryParts && primary) {
            // Hard furniture: table top, wardrobe door, drawer front → dominant product colour
            mat.color.copy(primary);
            mat.roughness = kwStyle.isHardMaterial ? kwStyle.roughness : (imgGloss >= 0 ? fabricRoughness : 0.68);
            mat.metalness = hardMetalness;
          } else if (accent) { mat.color.lerp(accent, 0.75); }
          else if (primary) { mat.color.copy(primary); }

          // ── frame → metallic, primary (hard) or accent (structural in upholstered) ─
        } else if (part === 'frame') {
          if (hasMetal) {
            mat.color.copy(isGold ? goldColor : silverColor);
            mat.roughness = 0.22; mat.metalness = 0.82;
          } else if (!hasUpholsteryParts && primary) {
            // Hard furniture: frame IS the dominant visual surface (wardrobe body, table apron)
            mat.color.copy(primary);
            mat.roughness = kwStyle.isHardMaterial ? kwStyle.roughness : (imgGloss >= 0 ? fabricRoughness : 0.68);
            mat.metalness = hardMetalness;
          } else if (accent) {
            // Upholstered furniture: frame is structural wood/metal (chair posts, sofa base)
            mat.color.lerp(accent, isDark ? 0.80 : 0.65);
            mat.roughness = 0.68;
          } else if (primary) {
            mat.color.copy(primary);
            mat.roughness = 0.68;
          } else {
            mat.color.set(isWarm ? 0xc8882a : 0x888875);
            mat.roughness = 0.65;
          }

          // ── leg → gold, silver, primary (hard furniture) or accent (upholstered) ──
        } else if (part === 'leg') {
          if (hasMetal && isGold) { mat.color.copy(goldColor); mat.roughness = 0.22; mat.metalness = 0.80; }
          else if (hasMetal) { mat.color.copy(silverColor); mat.roughness = 0.26; mat.metalness = 0.78; }
          else if (!hasUpholsteryParts && primary) {
            // Hard furniture: legs are the same material as the body
            mat.color.copy(primary);
            mat.roughness = kwStyle.isHardMaterial ? Math.min(0.72, kwStyle.roughness) : (imgGloss >= 0 ? Math.min(0.72, fabricRoughness) : 0.65);
            mat.metalness = hardMetalness;
          }
          else if (accent) { mat.color.lerp(accent, isDark ? 0.72 : 0.58); }
          else { mat.color.set(isWarm ? 0x7a4820 : 0x606060); mat.roughness = 0.60; }

          // ── mattress / pillow → near-white, barely tinted ────────────────────
        } else if (part === 'mattress') {
          if (primary && !isNearWhite) mat.color.lerp(primary, 0.10);

          // ── untagged fallback: infer from existing material properties ────────
        } else {
          if (isAlreadyMetal) {
            if (hasMetal && isGold) { mat.color.copy(goldColor); mat.roughness = 0.17; mat.metalness = 0.92; }
            else if (hasMetal) { mat.color.copy(silverColor); mat.roughness = 0.22; mat.metalness = 0.86; }
          } else if (isNearWhite) {
            if (primary) mat.color.lerp(primary, 0.06);
          } else if (mat.roughness >= 0.85) {
            if (primary) mat.color.lerp(primary, isDark ? 0.82 : 0.72);
            mat.roughness = fabricRoughness;
            if (isLeather) mat.metalness = 0.03;
          } else if (mat.roughness >= 0.50) {
            if (accent) mat.color.lerp(accent, 0.48);
            else if (primary) mat.color.lerp(primary, 0.30);
          }
        }

        mat.needsUpdate = true;
      });
    });
  }

  // ── Final Grounding & Centering ─────────────────────────────────────────────
  // Simplified hierarchy for better USDZ conversion compatibility on iOS.
  const bbox = new THREE.Box3();
  bbox.setFromObject(group); 
  
  const center = new THREE.Vector3();
  bbox.getCenter(center);
  
  // Shift the group so its absolute lowest point is at Y=0 and it's centered on X/Z
  // This is the CRITICAL anchor point for AR placement.
  group.position.set(-center.x, -bbox.min.y, -center.z);
  scene.add(group);

  // ── Contact-shadow decal ──────────────────────────────────────────────────
  {
    const W = dims.w / 100;
    const D = dims.l / 100;
    const shadowMat = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.45,
      depthWrite: false,
    });
    const shadowPlane = new THREE.Mesh(
      new THREE.PlaneGeometry(W * 1.15, D * 1.15),
      shadowMat,
    );
    shadowPlane.rotation.x = -Math.PI / 2;
    shadowPlane.position.y = 0.002; // Slightly higher to ensure visibility on all surfaces
    scene.add(shadowPlane);
  }

  // NOTE: We NO LONGER add internal lights to the scene. 
  // AR viewers (QuickLook/SceneViewer) provide their own lighting. 
  // Adding lights here confuses the bounding box and scale on many mobile viewers.

  return new Promise((resolve, reject) => {
    const exporter = new GLTFExporter();
    exporter.parse(
      scene,
      (result) => {
        const blob = new Blob([result as ArrayBuffer], { type: 'model/gltf-binary' });
        resolve(URL.createObjectURL(blob));
      },
      (error: unknown) => reject(error),
      { binary: true },
    );
  });
}
