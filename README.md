# GitHub Webhook Deployment Server

A FastAPI-based server that listens for GitHub webhooks and triggers deployment scripts for configured applications, running in a Docker container.

## Setup

1. Clone the repository
2. Configure `app_config.json` with your application names and deployment script paths
3. Set the following environment variables:
   - `GITHUB_WEBHOOK_SECRET_{APP_NAME}`: The secret token for webhook verification for each app (e.g., `GITHUB_WEBHOOK_SECRET_APP1`, `GITHUB_WEBHOOK_SECRET_APP2`)
   - `HOST_BINDING`: The host IP to bind the server to (use 0.0.0.0 for local development, 127.0.0.1 for production behind a reverse proxy)
   - `PORT`: The port on which the server will run (default is 8001)
4. Build and run the Docker container:

   ```bash
   docker-compose up -d
   ```

## Usage

Configure GitHub webhooks to send POST requests to:
`https://your-server-address/github/webhook/{app_name}`

The server will run the corresponding deployment script when pushes are made to the main branch.

## Setting up GitHub Webhooks

To set up a webhook in your GitHub repository:

1. Go to your repository on GitHub
2. Click on "Settings" > "Webhooks" > "Add webhook"
3. Set the Payload URL to `https://your-server-address/github/webhook/{app_name}`
4. Set the Content type to `application/json`
5. Set the Secret to the same value as your `GITHUB_WEBHOOK_SECRET_{APP_NAME}` environment variable for the corresponding app
6. Choose "Just the push event"
7. Ensure the webhook is set to "Active"
8. Click "Add webhook"

For more detailed instructions, refer to the [GitHub Webhooks documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks/creating-webhooks).

## Development

For local development:

1. Install dependencies: `uv sync`
2. Set up pre-commit hooks: `uv run pre-commit install`
3. Run the server locally: `uv run uvicorn server:app --host 0.0.0.0 --port $PORT
