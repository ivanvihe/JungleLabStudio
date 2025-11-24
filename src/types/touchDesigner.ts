export interface TouchDesignerSettings {
  enabled: boolean;
  bloomStrength: number;
  bloomRadius: number;
  bloomThreshold: number;
  filmGrain: number;
  chromaticAberration: number;
  vignetteDarkness: number;
  exposure: number;
}

export const DEFAULT_TOUCHDESIGNER_SETTINGS: TouchDesignerSettings = {
  enabled: false,
  bloomStrength: 0.9,
  bloomRadius: 0.35,
  bloomThreshold: 0.18,
  filmGrain: 0.28,
  chromaticAberration: 0.0012,
  vignetteDarkness: 0.65,
  exposure: 1.15,
};
