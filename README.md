# FrameForge V2 — text-to-video website prototype

This keeps the V1 browser-based prompt builder and storyboard features, and adds a server-side text-to-video request route.

## Important cost note
Hugging Face currently documents $0.10/month in free Inference Providers credits for free accounts (subject to change). A video-generation call may cost more than that, and model/provider availability can change. This app does not bypass provider billing. Do not add a payment method unless you choose to spend money.

## Run locally

Requirements: Python 3.10+ recommended.

1. Extract this ZIP.
2. Open a terminal in the `frameforge_v2` folder.
3. Create and activate a virtual environment:

   macOS/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Create a Hugging Face access token at https://huggingface.co/settings/tokens. Use only the permissions required for Inference Providers. Do not paste it into the web page.
6. Set it in your terminal environment.

   macOS/Linux:
   ```bash
   export HF_TOKEN="hf_your_token_here"
   ```

   Windows PowerShell:
   ```powershell
   $env:HF_TOKEN="hf_your_token_here"
   ```

7. Start the website/API:
   ```bash
   uvicorn server:app --reload --host 127.0.0.1 --port 8000
   ```
8. Open http://127.0.0.1:8000 on your computer. To test on iPhone while both devices are on the same Wi-Fi, start with `--host 0.0.0.0` and open the computer's LAN IP address on the phone. A public HTTPS deployment is better for regular use.

## Verify the API
- `GET /api/health` reports whether `HF_TOKEN` is configured.
- The website's Check backend button tests the route.
- Generate video sends the prompt to the backend; the backend calls Hugging Face Inference Providers and returns the video bytes.
- If a model/provider is unavailable or the account has insufficient credits, the site displays an error rather than a fake result.

## Deploy as a website (Render)
1. Create a GitHub account and a new private repository.
2. Upload `index.html`, `server.py`, `requirements.txt`, and `render.yaml`.
3. In Render, create a new Blueprint or Web Service from the repository.
4. Add `HF_TOKEN` in the service's environment settings as a secret. Never commit the token.
5. Deploy. Use the HTTPS URL on iPhone and computer.
6. Free web services may sleep when idle, and free hosting limits can change. Provider video inference is separate from web hosting.

## Troubleshooting
- 503: `HF_TOKEN` is not configured on the server.
- 401: token invalid or lacks access.
- 402 / credit error: no usable provider credits or billing access; do not assume generation is free.
- 404: selected model/provider route is not available; check the current Hugging Face text-to-video docs and adjust `HF_MODEL` / `HF_PROVIDER`.
- Timeout: video models can take a while; try a shorter prompt and check the provider's current status/limits.

## Scope of this version
The V1 storyboard, prompt builder, timing controls, scene reorder, CSV export, and JSON import/export remain in the browser. V2 adds a generate request, status check, preview, and download for the returned clip. Video assets are downloaded separately; the JSON project export stores scene metadata/prompts, not the large video binary.

## Security
- Never put `HF_TOKEN` in frontend JavaScript or in a public repository.
- Add authentication, per-user rate limits, prompt size limits, and usage accounting before opening this to the public.
- This starter makes a synchronous generation call. For production, switch to a provider queue/webhook job model and store output in object storage.
