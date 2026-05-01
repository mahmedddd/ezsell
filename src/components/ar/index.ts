// Barrel export for the AR module
export { WebARViewer }            from './WebARViewer';
export type { WebARViewerProps }  from './WebARViewer';
export {
  generateFurnitureGLB,
  resolveFurnitureType,
  resolveSmartDimensions,
  extractDominantColor,
  FURNITURE_DEFAULTS,
  FURNITURE_TYPE_LABELS,
}                                 from './FurnitureGLBGenerator';
export type {
  FurnitureDimensions,
  FurnitureType,
}                                 from './FurnitureGLBGenerator';
