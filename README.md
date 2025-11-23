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

### Using Pre-built Image from GHCR

Pull and run the latest image from GitHub Container Registry:

```bash
docker run --rm \
  -v /path/to/your/docs:/docs \
  -v /path/to/your/embeddings:/embeddings \
  ghcr.io/sofadb/build-embeddings:latest
```

### With GPU Support

If you have a NVIDIA GPU:

```bash
docker run --rm --gpus all \
  -v /path/to/your/docs:/docs \
  -v /path/to/your/embeddings:/embeddings \
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
  -v /path/to/your/docs:/docs \
  -v /path/to/your/embeddings:/embeddings \
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