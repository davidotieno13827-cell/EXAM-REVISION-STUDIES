# Kisii TV — Staging / Deployment

This repo contains the Kisii TV Django site. To deploy a staging site quickly, you can use Render (https://render.com) with the included `Dockerfile`.

Quick start (Render):

1. Connect this GitHub repository to Render.
2. Create a new Web Service and select "Docker" for the environment.
3. Use the default `Dockerfile` in the repo and set the branch to `main`.
4. Set any required environment variables (e.g., `SECRET_KEY`, `ALLOWED_HOSTS`, database credentials).

Or for a quick demo use `ngrok`:

```
ngrok http 8000
```

Then open the generated public URL.
