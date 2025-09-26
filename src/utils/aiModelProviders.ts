import {
  AiModelProviderId,
  InstalledModel,
  ModelFileInfo,
  ModelInfo,
  ModelProviderConfig,
  ModelProviderDefinition,
} from '../types/models';

const STORAGE_KEY = 'aiModelProviderConfigs';

const DEFAULT_INSTALL_ROOT = '~/JungleLab/models';

export const MODEL_PROVIDER_DEFINITIONS: ModelProviderDefinition[] = [
  {
    id: 'huggingface',
    name: 'Hugging Face',
    description: 'Repositorio de modelos open-source con soporte para múltiples tareas.',
    accentColor: '#ff7b00',
    docsUrl: 'https://huggingface.co/docs/api-inference/index',
    defaultInstallPath: `${DEFAULT_INSTALL_ROOT}/huggingface`,
    supportsGallery: true,
    requiresApiKey: false,
  },
  {
    id: 'civitai',
    name: 'Civitai',
    description: 'Modelos y LORAs creados por la comunidad para Stable Diffusion.',
    accentColor: '#5b6cff',
    docsUrl: 'https://docs.civitai.com/api-reference',
    defaultInstallPath: `${DEFAULT_INSTALL_ROOT}/civitai`,
    supportsGallery: true,
    requiresApiKey: false,
  },
  {
    id: 'manual',
    name: 'Manual / Local',
    description: 'Modelos instalados manualmente o importados desde otras fuentes.',
    accentColor: '#26a69a',
    docsUrl: 'https://docs.jarvis.local/model-import',
    defaultInstallPath: `${DEFAULT_INSTALL_ROOT}/manual`,
    supportsGallery: false,
    requiresApiKey: false,
  },
];

const PROVIDER_MAP: Record<AiModelProviderId, ModelProviderDefinition> = MODEL_PROVIDER_DEFINITIONS.reduce(
  (map, provider) => ({ ...map, [provider.id]: provider }),
  {} as Record<AiModelProviderId, ModelProviderDefinition>
);

const ensureConfig = (
  configs: Partial<Record<AiModelProviderId, ModelProviderConfig>> | null,
  provider: AiModelProviderId
): ModelProviderConfig => {
  const fallback: ModelProviderConfig = {
    installPath: PROVIDER_MAP[provider].defaultInstallPath,
    models: [],
    activeModelId: null,
  };
  if (!configs) {
    return fallback;
  }
  const existing = configs[provider];
  if (!existing) {
    return fallback;
  }
  return {
    installPath: existing.installPath || PROVIDER_MAP[provider].defaultInstallPath,
    models: Array.isArray(existing.models) ? existing.models : [],
    activeModelId: existing.activeModelId ?? null,
  };
};

const sanitizePath = (value: string): string => {
  if (!value) return '';
  return value.replace(/\\\\/g, '/');
};

const sanitizeModelName = (value: string): string => {
  return value
    .replace(/[<>:"|?*]/g, '_')
    .replace(/[\\/]/g, '_')
    .trim();
};

const computeSizeBytes = (model: ModelInfo | InstalledModel): number => {
  if (model.sizeBytes && model.sizeBytes > 0) {
    return model.sizeBytes;
  }
  if (model.files?.length) {
    return model.files.reduce((total, file) => total + (file.sizeBytes || 0), 0);
  }
  return 0;
};

const buildInstalledModel = (
  model: ModelInfo,
  installPath: string
): InstalledModel => {
  const sizeBytes = computeSizeBytes(model);
  const sanitizedPath = sanitizePath(installPath || PROVIDER_MAP[model.provider].defaultInstallPath);
  const normalizedRoot = sanitizedPath.replace(/\\\\/g, '/').replace(/\/+$/, '');
  const safeName = sanitizeModelName(model.id || model.name);
  const fullPath = normalizedRoot ? `${normalizedRoot}/${safeName}` : safeName;
  return {
    ...model,
    installedAt: new Date().toISOString(),
    installedPath: fullPath,
    sizeOnDisk: sizeBytes || undefined,
    sizeBytes: sizeBytes || undefined,
  };
};

export const loadStoredModelProviderConfigs = (): Record<AiModelProviderId, ModelProviderConfig> => {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      throw new Error('localStorage unavailable');
    }
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return MODEL_PROVIDER_DEFINITIONS.reduce((acc, provider) => {
        acc[provider.id] = ensureConfig({}, provider.id);
        return acc;
      }, {} as Record<AiModelProviderId, ModelProviderConfig>);
    }
    const parsed = JSON.parse(raw);
    return MODEL_PROVIDER_DEFINITIONS.reduce((acc, provider) => {
      acc[provider.id] = ensureConfig(parsed, provider.id);
      return acc;
    }, {} as Record<AiModelProviderId, ModelProviderConfig>);
  } catch {
    return MODEL_PROVIDER_DEFINITIONS.reduce((acc, provider) => {
      acc[provider.id] = ensureConfig({}, provider.id);
      return acc;
    }, {} as Record<AiModelProviderId, ModelProviderConfig>);
  }
};

export const persistModelProviderConfigs = (
  configs: Record<AiModelProviderId, ModelProviderConfig>
) => {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(configs));
  } catch (err) {
    console.warn('Unable to persist model provider configs', err);
  }
};

export const setProviderInstallPath = (
  configs: Record<AiModelProviderId, ModelProviderConfig>,
  provider: AiModelProviderId,
  path: string
): Record<AiModelProviderId, ModelProviderConfig> => {
  const next: Record<AiModelProviderId, ModelProviderConfig> = { ...configs };
  const config = ensureConfig(configs, provider);
  next[provider] = {
    ...config,
    installPath: sanitizePath(path) || PROVIDER_MAP[provider].defaultInstallPath,
  };
  return next;
};

export const addInstalledModel = (
  configs: Record<AiModelProviderId, ModelProviderConfig>,
  model: ModelInfo
): Record<AiModelProviderId, ModelProviderConfig> => {
  const provider = model.provider;
  const config = ensureConfig(configs, provider);
  const installed = buildInstalledModel(model, config.installPath);
  const existingIndex = config.models.findIndex((item) => item.id === installed.id);
  const nextModels = existingIndex >= 0
    ? config.models.map((item, index) => (index === existingIndex ? { ...installed, installedAt: item.installedAt } : item))
    : [...config.models, installed];
  const next: Record<AiModelProviderId, ModelProviderConfig> = {
    ...configs,
    [provider]: {
      ...config,
      models: nextModels,
    },
  };
  persistModelProviderConfigs(next);
  return next;
};

export const removeInstalledModel = (
  configs: Record<AiModelProviderId, ModelProviderConfig>,
  provider: AiModelProviderId,
  modelId: string
): Record<AiModelProviderId, ModelProviderConfig> => {
  const config = ensureConfig(configs, provider);
  const nextModels = config.models.filter((model) => model.id !== modelId);
  const nextActive = config.activeModelId === modelId ? null : config.activeModelId ?? null;
  const next: Record<AiModelProviderId, ModelProviderConfig> = {
    ...configs,
    [provider]: {
      ...config,
      models: nextModels,
      activeModelId: nextActive,
    },
  };
  persistModelProviderConfigs(next);
  return next;
};

export const setActiveModel = (
  configs: Record<AiModelProviderId, ModelProviderConfig>,
  provider: AiModelProviderId,
  modelId: string | null
): Record<AiModelProviderId, ModelProviderConfig> => {
  const config = ensureConfig(configs, provider);
  const existing = config.models.find((model) => model.id === modelId);
  const next: Record<AiModelProviderId, ModelProviderConfig> = {
    ...configs,
    [provider]: {
      ...config,
      activeModelId: existing ? modelId : null,
    },
  };
  persistModelProviderConfigs(next);
  return next;
};

export const getInstalledModelsIndex = (
  configs: Record<AiModelProviderId, ModelProviderConfig>
): Record<string, InstalledModel> => {
  const index: Record<string, InstalledModel> = {};
  (Object.keys(configs) as AiModelProviderId[]).forEach((provider) => {
    const config = ensureConfig(configs, provider);
    config.models.forEach((model) => {
      index[`${provider}:${model.id}`] = model;
    });
  });
  return index;
};

type FetchOptions = {
  provider: AiModelProviderId;
  query?: string;
  limit?: number;
  signal?: AbortSignal;
};

const parseJsonResponse = async <T>(response: Response): Promise<T> => {
  const contentType = response.headers.get('content-type') || '';
  const textBody = await response.text();
  if (!response.ok) {
    throw new Error(textBody || `Request failed with status ${response.status}`);
  }
  if (!contentType.includes('application/json')) {
    try {
      return JSON.parse(textBody) as T;
    } catch {
      throw new Error('El proveedor devolvió una respuesta no válida (JSON)');
    }
  }
  try {
    return JSON.parse(textBody) as T;
  } catch (error) {
    throw new Error('Error al parsear la respuesta JSON del proveedor');
  }
};

interface HuggingFaceResponseItem {
  modelId: string;
  id?: string;
  name?: string;
  author?: string;
  likes?: number;
  downloads?: number;
  tags?: string[];
  pipeline_tag?: string;
  library_name?: string;
  lastModified?: string;
  createdAt?: string;
  siblings?: { rfilename: string; size?: number }[];
  cardData?: {
    summary?: string;
    license?: string;
    thumbnail?: string;
  };
}

interface CivitaiResponseItem {
  id: number;
  name: string;
  description?: string;
  tags?: string[];
  stats?: {
    downloadCount?: number;
  };
  modelVersions?: Array<{
    id: number;
    name: string;
    baseModel?: string;
    updatedAt?: string;
    trainedWords?: string[];
    files?: Array<{
      id: number;
      name: string;
      sizeKB?: number;
      type?: string;
      primary?: boolean;
      downloadUrl: string;
      hashes?: {
        SHA256?: string;
      };
    }>;
    images?: Array<{
      url: string;
    }>;
  }>;
  creator?: {
    username?: string;
  };
}

const fetchFromHuggingFace = async (
  options: FetchOptions
): Promise<ModelInfo[]> => {
  const url = new URL('https://huggingface.co/api/models');
  if (options.query) {
    url.searchParams.set('search', options.query);
  }
  if (options.limit) {
    url.searchParams.set('limit', String(options.limit));
  }
  url.searchParams.set('sort', 'downloads');
  const response = await fetch(url.toString(), {
    signal: options.signal,
    headers: {
      Accept: 'application/json',
    },
  });
  const data = await parseJsonResponse<HuggingFaceResponseItem[]>(response);
  return data.map<ModelInfo>((item) => {
    const files: ModelFileInfo[] = (item.siblings || []).map((file) => ({
      id: file.rfilename,
      name: file.rfilename,
      sizeBytes: file.size,
      downloadUrl: `https://huggingface.co/${item.modelId}/resolve/main/${file.rfilename}`,
      format: file.rfilename.split('.').pop(),
    }));
    const sizeBytes = files.reduce((total, file) => total + (file.sizeBytes || 0), 0) || undefined;
    return {
      id: item.modelId,
      name: item.name || item.modelId.split('/').pop() || item.modelId,
      description: item.cardData?.summary,
      provider: 'huggingface',
      tags: item.tags || (item.pipeline_tag ? [item.pipeline_tag] : []),
      downloads: item.downloads,
      updatedAt: item.lastModified || item.createdAt,
      author: item.author,
      license: item.cardData?.license,
      sizeBytes,
      thumbnail: item.cardData?.thumbnail,
      version: item.library_name,
      files,
    };
  });
};

const fetchFromCivitai = async (
  options: FetchOptions
): Promise<ModelInfo[]> => {
  const url = new URL('https://civitai.com/api/v1/models');
  if (options.query) {
    url.searchParams.set('query', options.query);
  }
  url.searchParams.set('limit', String(options.limit ?? 24));
  const response = await fetch(url.toString(), {
    signal: options.signal,
    headers: {
      Accept: 'application/json',
    },
  });
  const data = await parseJsonResponse<{ items: CivitaiResponseItem[] }>(response);
  return (data.items || []).map<ModelInfo>((item) => {
    const primaryVersion = item.modelVersions?.[0];
    const files: ModelFileInfo[] = (primaryVersion?.files || []).map((file) => ({
      id: String(file.id),
      name: file.name,
      sizeBytes: typeof file.sizeKB === 'number' ? file.sizeKB * 1024 : undefined,
      downloadUrl: file.downloadUrl,
      primary: file.primary,
      format: file.type,
      sha256: file.hashes?.SHA256,
    }));
    const thumbnail = primaryVersion?.images?.[0]?.url;
    const sizeBytes = files.reduce((total, file) => total + (file.sizeBytes || 0), 0) || undefined;
    return {
      id: String(item.id),
      name: item.name,
      description: item.description,
      provider: 'civitai',
      tags: item.tags || [],
      downloads: item.stats?.downloadCount,
      updatedAt: primaryVersion?.updatedAt,
      author: item.creator?.username,
      sizeBytes,
      version: primaryVersion?.name,
      thumbnail,
      files,
    };
  });
};

export const fetchModelGallery = async (
  options: FetchOptions
): Promise<ModelInfo[]> => {
  if (options.provider === 'manual') {
    return [];
  }
  if (options.provider === 'huggingface') {
    return fetchFromHuggingFace(options);
  }
  if (options.provider === 'civitai') {
    return fetchFromCivitai(options);
  }
  return [];
};

export const formatBytes = (bytes?: number): string => {
  if (!bytes || bytes <= 0) return '—';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const idx = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, idx);
  return `${value.toFixed(value >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`;
};

