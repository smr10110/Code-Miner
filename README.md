# Code-Miner

Sistema que analiza repositorios populares de GitHub para descubrir las palabras mas usadas en nombres de funciones y metodos de Python y Java. Los resultados se visualizan en tiempo real a traves de un dashboard web.

## Arquitectura

```
GitHub API  ──>  Miner  ──>  Redis  <──  Visualizer API  <──  Dashboard
  (lee repos)   (escribe)   (sorted sets)   (lee)           (muestra)
```

El sistema se compone de 3 contenedores Docker:

| Contenedor | Rol | Puerto |
|---|---|---|
| **Miner** | Busca repos en GitHub, parsea funciones, escribe palabras en Redis | - |
| **Redis** | Almacena rankings con Sorted Sets y persistencia AOF | 6379 |
| **Visualizer** | FastAPI + Streamlit: lee Redis y muestra dashboard en tiempo real | 8000, 8501 |

### Flujo de datos

1. El **Miner** busca repos populares con actividad reciente (ultimo mes) en GitHub
2. Filtra solo repos Python o Java y recorre sus archivos (.py, .java)
3. Extrae nombres de funciones (AST para Python, regex para Java)
4. Separa cada nombre en palabras (snake_case, camelCase)
5. Escribe las palabras en **Redis** con `ZINCRBY` (overall y por lenguaje)
6. El **Visualizer** lee de Redis con `ZREVRANGE` y muestra el ranking en un dashboard Streamlit

### Estructura de datos en Redis

```
word_ranking          -> Sorted Set (ranking global)
word_ranking:python   -> Sorted Set (solo palabras de archivos .py)
word_ranking:java     -> Sorted Set (solo palabras de archivos .java)
processed_repos       -> Set (repos ya procesados)
total_words_sent      -> String (contador total de palabras)
miner_status          -> Hash (estado actual del miner)
```

## Requisitos

- **Docker** y **Docker Compose**
- **Token de GitHub** (opcional pero recomendado)
  - Sin token: 60 requests/hora (muy lento)
  - Con token: 5000 requests/hora

## Como levantarlo

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Code-Miner

# 2. Configurar token de GitHub (recomendado)
cp .env.example .env
# Editar .env y poner tu token: GITHUB_TOKEN=ghp_xxxx

# 3. Levantar todo con un solo comando
docker-compose up --build

# 4. Abrir el dashboard en el navegador
# http://localhost:8501
```