# Scripts de JungleLabStudio

Guía rápida de los scripts disponibles en el proyecto.

---

## 🧹 Scripts de Limpieza

### `clean_cache.sh` ⭐

**Propósito**: Limpiar toda la cache del proyecto sin ejecutarlo.

**Uso**:
```bash
./clean_cache.sh
```

**Qué limpia**:
- ✅ Directorios `__pycache__/` (Python bytecode cache)
- ✅ Archivos `*.pyc` (Python compiled files)
- ✅ Directorios `.pytest_cache/` (pytest cache)
- ✅ Directorios `.mypy_cache/` (mypy type checker cache)
- ✅ Directorios `*.egg-info/` (Python package info)
- ✅ Archivos `*.log` (application logs)
- ✅ Archivo `imgui.ini` (ImGui UI state)
- ✅ Contenido de `logs/` y `src/logs/`

**Cuándo usar**:
- Antes de hacer `git push` (asegura que no subes cache)
- Cuando el proyecto se comporta de forma extraña (cache corrupta)
- Para liberar espacio en disco
- Después de cambiar entre ramas de Git

**Salida**:
```
🧹 Cleaning JungleLabStudio cache...

📊 Files to clean:
   __pycache__ directories: 45
   .pyc files: 234
   .log files: 12

🗑️  Removing __pycache__ directories...
🗑️  Removing .pyc files...
🗑️  Removing .pytest_cache...
...
✅ Cache cleaned successfully!

📦 Ready for git push
```

---

### `clean_and_run.sh`

**Propósito**: Limpiar cache y ejecutar la aplicación.

**Uso**:
```bash
./clean_and_run.sh
```

**Qué hace**:
1. Limpia `__pycache__/` y `*.pyc`
2. Ejecuta `run.sh`

**Equivalente a**:
```bash
./clean_cache.sh
./run.sh
```

---

## 🚀 Scripts de Ejecución

### `run.sh`

**Propósito**: Ejecutar la aplicación en modo normal.

**Uso**:
```bash
./run.sh
```

**Características**:
- Activa el entorno virtual (`venv/`)
- Ejecuta la aplicación desde `src/main.py`
- Modo de producción estándar

---

### `run_debug.sh` ⭐

**Propósito**: Ejecutar la aplicación en modo debug con cache limpia.

**Uso**:
```bash
./run_debug.sh
```

**Qué hace**:
1. **Limpia cache automáticamente** antes de ejecutar
   - Elimina `__pycache__/`
   - Elimina `*.pyc`
   - Elimina `imgui.ini`
2. Activa el entorno virtual
3. Ejecuta con `PYTHONUNBUFFERED=1` para logging en tiempo real
4. Usa `python -u` para unbuffered output

**Cuándo usar**:
- Durante desarrollo (asegura código actualizado)
- Para debugging (sin cache que interfiera)
- Cuando haces cambios en el código y quieres ver efectos inmediatos
- Para logging en tiempo real

**Ventajas**:
- ✅ Siempre ejecuta código actualizado (no cache)
- ✅ Logs en tiempo real (unbuffered)
- ✅ UI state limpio cada vez (no imgui.ini)

---

### `run_editor.sh`

**Propósito**: Ejecutar el editor visual.

**Uso**:
```bash
./run_editor.sh
```

**Características**:
- Abre el editor visual de nodos
- Permite crear y editar presets YAML
- Interfaz gráfica completa

---

## 📋 Workflow Recomendado

### Durante Desarrollo

```bash
# Opción 1: Ejecutar con limpieza automática
./run_debug.sh

# Opción 2: Limpiar manualmente y ejecutar
./clean_cache.sh
./run.sh
```

### Antes de Git Push

```bash
# Limpiar cache
./clean_cache.sh

# Verificar qué se subirá
git status

# Commit y push
git add .
git commit -m "mensaje"
git push
```

### Debugging de Problemas

```bash
# Si la app se comporta extraño
./clean_cache.sh
./run_debug.sh

# Ver logs en tiempo real (unbuffered)
```

---

## 🔍 Verificación de Cache

Para ver qué archivos de cache existen actualmente:

```bash
# Contar __pycache__ directories
find . -type d -name "__pycache__" | wc -l

# Contar .pyc files
find . -type f -name "*.pyc" | wc -l

# Ver tamaño de cache
du -sh $(find . -type d -name "__pycache__")
```

---

## 🛠️ Troubleshooting

### "Permission denied" al ejecutar scripts

```bash
# Hacer ejecutables
chmod +x *.sh
```

### Scripts no funcionan

```bash
# Verificar líneas de fin (LF vs CRLF)
dos2unix *.sh  # si disponible

# O manualmente
sed -i 's/\r$//' *.sh
```

### Cache sigue apareciendo

```bash
# Verificar .gitignore
cat .gitignore

# Forzar limpieza profunda
./clean_cache.sh
git clean -fdx  # CUIDADO: elimina archivos no rastreados
```

---

## 📁 Archivos Ignorados (.gitignore)

El proyecto está configurado para ignorar automáticamente:

- `__pycache__/`, `*.pyc` (Python cache)
- `venv/`, `.venv/` (entornos virtuales)
- `*.log` (logs)
- `imgui.ini` (UI state)
- `.pytest_cache/`, `.mypy_cache/` (testing cache)
- Y más...

Ver `.gitignore` para lista completa.

---

## 🎯 Resumen Rápido

| Script | Propósito | Limpia Cache | Ejecuta App |
|--------|-----------|--------------|-------------|
| `clean_cache.sh` | Solo limpiar | ✅ | ❌ |
| `clean_and_run.sh` | Limpiar + ejecutar | ✅ | ✅ |
| `run.sh` | Solo ejecutar | ❌ | ✅ |
| `run_debug.sh` | Ejecutar debug | ✅ | ✅ |
| `run_editor.sh` | Abrir editor | ❌ | ✅ |

**Recomendación**: Usar `run_debug.sh` durante desarrollo, y `clean_cache.sh` antes de git push.

---

**Última actualización**: 2025-11-29
**Versión**: 2.1.0
