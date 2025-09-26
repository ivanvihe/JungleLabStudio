import React from 'react';
import {
  AiModelProviderId,
  InstalledModel,
  ModelInfo,
  ModelProviderDefinition,
} from '../../types/models';
import { formatBytes } from '../../utils/aiModelProviders';
import './ModelGallery.css';

interface ModelGalleryProps {
  providers: ModelProviderDefinition[];
  provider: AiModelProviderId;
  models: ModelInfo[];
  installedIndex: Record<string, InstalledModel>;
  activeModelKey?: string | null;
  query: string;
  isLoading?: boolean;
  error?: string | null;
  onProviderChange: (provider: AiModelProviderId) => void;
  onQueryChange: (value: string) => void;
  onRefresh: () => void;
  onInstall: (model: ModelInfo) => void;
  onActivate: (model: ModelInfo) => void;
}

const ModelGallery: React.FC<ModelGalleryProps> = ({
  providers,
  provider,
  models,
  installedIndex,
  activeModelKey,
  query,
  isLoading = false,
  error,
  onProviderChange,
  onQueryChange,
  onRefresh,
  onInstall,
  onActivate,
}) => {
  const providerDefinition = providers.find((item) => item.id === provider);

  const renderSkeleton = () => (
    <div className="model-gallery__grid">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="model-card model-card--skeleton">
          <div className="model-card__thumbnail" />
          <div className="model-card__meta">
            <div className="model-card__title" />
            <div className="model-card__info" />
            <div className="model-card__tags" />
          </div>
        </div>
      ))}
    </div>
  );

  const renderManualContent = () => (
    <div className="model-gallery__empty">
      <h4>Galería no disponible</h4>
      <p>
        Este proveedor es únicamente para modelos instalados manualmente. Usa la configuración avanzada
        para registrar modelos descargados desde otras fuentes.
      </p>
    </div>
  );

  const renderGalleryContent = () => {
    if (isLoading) {
      return renderSkeleton();
    }

    if (error) {
      return (
        <div className="model-gallery__error">
          <strong>No se pudo cargar la galería.</strong>
          <span>{error}</span>
          <button type="button" onClick={onRefresh} className="model-gallery__retry">
            Reintentar
          </button>
        </div>
      );
    }

    if (!models.length) {
      return (
        <div className="model-gallery__empty">
          <h4>No hay resultados</h4>
          <p>Prueba con otro término de búsqueda o revisa más tarde.</p>
        </div>
      );
    }

    return (
      <div className="model-gallery__grid">
        {models.map((model) => {
          const installed = installedIndex[`${model.provider}:${model.id}`];
          const isActive = activeModelKey === `${model.provider}:${model.id}`;
          const primaryFile = model.files?.[0];
          return (
            <article key={`${model.provider}-${model.id}`} className="model-card">
              <div className="model-card__thumbnail">
                {model.thumbnail ? (
                  <img src={model.thumbnail} alt={model.name} />
                ) : (
                  <span className="model-card__placeholder">{model.name.charAt(0).toUpperCase()}</span>
                )}
              </div>
              <div className="model-card__meta">
                <div className="model-card__header">
                  <span className={`model-card__provider model-card__provider--${model.provider}`}>
                    {providerDefinition?.name ?? model.provider}
                  </span>
                  {model.downloads ? (
                    <span className="model-card__stat">⬇ {model.downloads.toLocaleString()}</span>
                  ) : null}
                </div>
                <h4 title={model.name}>{model.name}</h4>
                {model.description ? (
                  <p className="model-card__description">{model.description}</p>
                ) : null}
                <dl className="model-card__details">
                  {model.version ? (
                    <div>
                      <dt>Versión</dt>
                      <dd>{model.version}</dd>
                    </div>
                  ) : null}
                  {model.author ? (
                    <div>
                      <dt>Autor</dt>
                      <dd>{model.author}</dd>
                    </div>
                  ) : null}
                  {model.updatedAt ? (
                    <div>
                      <dt>Actualizado</dt>
                      <dd>{new Date(model.updatedAt).toLocaleDateString()}</dd>
                    </div>
                  ) : null}
                  {primaryFile ? (
                    <div>
                      <dt>Formato</dt>
                      <dd>{primaryFile.format || primaryFile.name.split('.').pop()}</dd>
                    </div>
                  ) : null}
                  <div>
                    <dt>Tamaño</dt>
                    <dd>{formatBytes(model.sizeBytes)}</dd>
                  </div>
                </dl>
                {model.tags?.length ? (
                  <ul className="model-card__tags">
                    {model.tags.slice(0, 5).map((tag) => (
                      <li key={tag}>#{tag}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
              <div className="model-card__actions">
                {!installed ? (
                  <button
                    type="button"
                    className="model-card__button"
                    onClick={() => onInstall(model)}
                  >
                    Instalar modelo
                  </button>
                ) : (
                  <div className="model-card__cta">
                    <button
                      type="button"
                      className={`model-card__button ${isActive ? 'model-card__button--active' : ''}`}
                      onClick={() => onActivate(model)}
                    >
                      {isActive ? 'Activo en Jarvis' : 'Activar para Jarvis'}
                    </button>
                    <span className="model-card__installed">Instalado el {new Date(installed.installedAt).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    );
  };

  return (
    <section className="model-gallery">
      <header className="model-gallery__header">
        <div className="model-gallery__tabs">
          {providers.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`model-gallery__tab ${item.id === provider ? 'active' : ''}`}
              onClick={() => onProviderChange(item.id)}
            >
              {item.name}
            </button>
          ))}
        </div>
        {providerDefinition?.supportsGallery ? (
          <div className="model-gallery__actions">
            <input
              type="search"
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  onRefresh();
                }
              }}
              placeholder="Buscar modelos..."
            />
            <button type="button" onClick={onRefresh} className="model-gallery__refresh">
              Actualizar
            </button>
          </div>
        ) : null}
      </header>

      {providerDefinition ? (
        <div className="model-gallery__summary" style={{ borderColor: providerDefinition.accentColor }}>
          <div>
            <h3>{providerDefinition.name}</h3>
            <p>{providerDefinition.description}</p>
          </div>
          <a href={providerDefinition.docsUrl} target="_blank" rel="noreferrer">
            Ver documentación ↗
          </a>
        </div>
      ) : null}

      {providerDefinition?.supportsGallery ? renderGalleryContent() : renderManualContent()}
    </section>
  );
};

export default ModelGallery;
