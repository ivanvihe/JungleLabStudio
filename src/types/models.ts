export type AiModelProviderId = 'huggingface' | 'civitai' | 'manual';

export interface ModelFileInfo {
  id: string;
  name: string;
  sizeBytes?: number;
  downloadUrl: string;
  primary?: boolean;
  format?: string;
  sha256?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  description?: string;
  provider: AiModelProviderId;
  tags: string[];
  downloads?: number;
  updatedAt?: string;
  version?: string;
  author?: string;
  license?: string;
  sizeBytes?: number;
  thumbnail?: string;
  files: ModelFileInfo[];
}

export interface InstalledModel extends ModelInfo {
  installedAt: string;
  installedPath: string;
  sizeOnDisk?: number;
}

export interface ModelProviderDefinition {
  id: AiModelProviderId;
  name: string;
  description: string;
  accentColor: string;
  docsUrl: string;
  defaultInstallPath: string;
  supportsGallery: boolean;
  requiresApiKey: boolean;
}

export interface ModelProviderConfig {
  installPath: string;
  models: InstalledModel[];
  activeModelId?: string | null;
}
