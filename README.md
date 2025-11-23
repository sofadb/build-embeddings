# Build Embeddings

Docker image for generating embeddings from markdown files using the `intfloat/multilingual-e5-large` model.

## Overview

This tool processes markdown files in a `/docs` directory and generates corresponding embedding files in an `/embeddings` directory. The embeddings are saved as JSON files with the same relative path structure.

### Features

- **Incremental Processing**: Only processes files that have changed (using SHA256 checksum)
- **Automatic Cleanup**: Deletes embedding files when source markdown files are removed
- **Multilingual Support**: Uses the `intfloat/multilingual-e5-large` model
- **GPU Support**: Automatically uses GPU if available

### Output Format

For each markdown file, a corresponding JSON file is created in `/embeddings` with the same relative path structure:

```json
{
  "embeddings": {
    "intfloat/multilingual-e5-large": [1024-dimensional vector]
  },
  "shasum": "sha256_hash_of_markdown_file",
  "headline": "first line of the markdown file"
}
```

## Quick Start

### Using as a Reusable GitHub Actions Workflow

The most common use case is to automatically generate embeddings for your notes repository using GitHub Actions. This workflow will:
- Clone your notes repository
- Clone your embeddings repository
- Generate embeddings for all markdown files
- Commit the embeddings to the separate embeddings repository

#### Setup

1. In your notes repository (e.g., `user/brain`), create `.github/workflows/build-embeddings.yml`:

```yaml
name: Build Embeddings

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  workflow_dispatch:     # Manual trigger

jobs:
  build:
    permissions:
      contents: write
    uses: sofadb/build-embeddings/.github/workflows/build-embeddings-reusable.yml@main
    with:
      embeddings_repo: 'user/brain-embeddings'  # Your embeddings repository
      notes_path: '/'                            # Where your markdown files are (optional)
      embeddings_path: '/'                       # Where to put embeddings (optional)
      image_tag: 'latest'                        # Docker image version (optional)
    secrets:
      embeddings_token: ${{ secrets.EMBEDDINGS_TOKEN }}
```

2. Create a personal access token with repo access and add it as `EMBEDDINGS_TOKEN` in your repository secrets.

3. Commit and push this workflow file. Embeddings will be generated:
   - Daily at midnight UTC (via schedule)
   - Manually via the Actions tab (click "Run workflow")

#### Configuration Options

Required:
- `embeddings_repo`: Repository to push embeddings to, format `owner/repo`

Optional:
- `notes_path`: Path to markdown files in notes repo, defaults to `/`
- `embeddings_path`: Output path in embeddings repo, defaults to `/`
- `image_tag`: Docker image version, defaults to `latest`
- `commit_email`: Git commit email, defaults to `action@github.com`
- `commit_user`: Git commit user name, defaults to `GitHub Action - Embeddings Builder`

Secrets:
- `embeddings_token`: GitHub token with write access to embeddings repository

### Using Pre-built Image from GHCR

Pull and run the latest image from GitHub Container Registry:

```bash
docker run --rm \
  -v ./examples/docs:/docs \
  -v ./examples/embeddings:/embeddings \
  ghcr.io/sofadb/build-embeddings:latest
```

### With GPU Support

If you have a NVIDIA GPU:

```bash
docker run --rm --gpus all \
  -v ./examples/docs:/docs \
  -v ./examples/embeddings:/embeddings \
  ghcr.io/sofadb/build-embeddings:latest
```

### Build the Docker Image Locally

If you prefer to build locally:

```bash
docker build -t build-embeddings .
```

Then run with:

```bash
docker run --rm \
  -v ./examples/docs:/docs \
  -v ./examples/embeddings:/embeddings \
  build-embeddings
```

## How It Works

1. **Scanning**: Finds all `.md` files in `/docs`
2. **Checksum Comparison**: Compares SHA256 hash of each file with stored hash in existing embedding files
3. **Processing**: For changed files:
   - Reads the entire markdown content
   - Extracts the first line as the headline
   - Generates embedding using `multilingual-e5-large` model
   - Saves as JSON with embedding, shasum, and headline
4. **Cleanup**: Deletes embedding files for markdown files that no longer exist

## Development

### Local Testing

You can run the script directly without Docker:

```bash
pip install -r requirements.txt
python build_embeddings.py
```

Make sure to have `/docs` and `/embeddings` directories available, or modify the paths in the script.

## Requirements

- Docker
- Sufficient disk space for the model (~2GB)
- Optional: NVIDIA GPU with Docker GPU support for faster processing

## License

MIT