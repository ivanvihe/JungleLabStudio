import React from 'react';
import {
  AiModelProviderId,
  InstalledModel,
  ModelProviderConfig,
  ModelProviderDefinition,
} from '../../types/models';
import { formatBytes } from '../../utils/aiModelProviders';
import './ModelProviderSettings.css';

interface ModelProviderSettingsProps {
  providers: ModelProviderDefinition[];
  configs: Record<AiModelProviderId, ModelProviderConfig>;
  activeModelKey?: string | null;
  onInstallPathChange: (provider: AiModelProviderId, path: string) => void;
  onActivateModel: (provider: AiModelProviderId, modelId: string) => void;
  onRemoveModel: (provider: AiModelProviderId, modelId: string) => void;
}

const formatDate = (value: string) => {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

const ModelProviderSettings: React.FC<ModelProviderSettingsProps> = ({
  providers,
  configs,
  activeModelKey,
  onInstallPathChange,
  onActivateModel,
  onRemoveModel,
}) => {
  const renderInstalledModel = (
    provider: AiModelProviderId,
    model: InstalledModel,
    isActive: boolean
  ) => (
    <li key={`${provider}-${model.id}`} className="provider-card__model">
      <div className="provider-card__model-info">
        <div className="provider-card__model-header">
          <h4>{model.name}</h4>
          {isActive ? <span className="provider-card__badge">Activo en Jarvis</span> : null}
        </div>
        <dl>
          <div>
            <dt>Proveedor</dt>
            <dd>{provider}</dd>
          </div>
          <div>
            <dt>Tamaño</dt>
            <dd>{formatBytes(model.sizeOnDisk || model.sizeBytes)}</dd>
          </div>
          <div>
            <dt>Instalado</dt>
            <dd>{formatDate(model.installedAt)}</dd>
          </div>
          <div>
            <dt>Ubicación</dt>
            <dd className="provider-card__path" title={model.installedPath}>{model.installedPath}</dd>
          </div>
        </dl>
        {model.tags?.length ? (
          <ul className="provider-card__tags">
            {model.tags.slice(0, 6).map((tag) => (
              <li key={tag}>#{tag}</li>
            ))}
          </ul>
        ) : null}
      </div>
      <div className="provider-card__model-actions">
        {!isActive ? (
          <button type="button" onClick={() => onActivateModel(provider, model.id)}>
            Activar para Jarvis
          </button>
        ) : (
          <button type="button" className="secondary" onClick={() => onActivateModel(provider, model.id)}>
            Reasignar
          </button>
        )}
        <button
          type="button"
          className="danger"
          onClick={() => onRemoveModel(provider, model.id)}
        >
          Eliminar
        </button>
      </div>
    </li>
  );

  return (
    <section className="settings-section model-provider-settings">
      <h3>🧠 Proveedores de modelos IA</h3>
      <p className="setting-description">
        Define dónde se descargan los modelos, consulta qué tienes instalado y activa el modelo en producción
        para Jarvis.
      </p>

      <div className="provider-grid">
        {providers.map((provider) => {
          const config = configs[provider.id];
          const installedModels = config?.models || [];
          const activeKey = config?.activeModelId ? `${provider.id}:${config.activeModelId}` : null;
          return (
            <article key={provider.id} className="provider-card">
              <header className="provider-card__header" style={{ borderColor: provider.accentColor }}>
                <div>
                  <h4>{provider.name}</h4>
                  <p>{provider.description}</p>
                </div>
                <a href={provider.docsUrl} target="_blank" rel="noreferrer">
                  Docs ↗
                </a>
              </header>

              <div className="provider-card__body">
                <label className="provider-card__path-input">
                  <span>Ruta de instalación</span>
                  <input
                    type="text"
                    value={config?.installPath || ''}
                    onChange={(event) => onInstallPathChange(provider.id, event.target.value)}
                    placeholder={provider.defaultInstallPath}
                  />
                </label>

                <div className="provider-card__stats">
                  <div>
                    <strong>{installedModels.length}</strong>
                    <span>Modelos instalados</span>
                  </div>
                  <div>
                    <strong>{formatBytes(installedModels.reduce((total, item) => total + (item.sizeOnDisk || item.sizeBytes || 0), 0))}</strong>
                    <span>Espacio ocupado</span>
                  </div>
                </div>

                {provider.supportsGallery ? (
                  <div className="provider-card__hint">
                    Descarga directamente desde la galería para mantener los metadatos sincronizados.
                  </div>
                ) : (
                  <div className="provider-card__hint">
                    Registra aquí modelos instalados manualmente o importados desde otras fuentes.
                  </div>
                )}

                {installedModels.length ? (
                  <ul className="provider-card__models">
                    {installedModels.map((model) =>
                      renderInstalledModel(provider.id, model, activeModelKey === `${provider.id}:${model.id}`)
                    )}
                  </ul>
                ) : (
                  <div className="provider-card__empty">Todavía no hay modelos registrados para este proveedor.</div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export default ModelProviderSettings;
