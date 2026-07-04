// Backend URL the app talks to.
//
// PUBLIC (APK / off-WiFi demo): a cloudflared tunnel to the laptop's Gemma backend.
//   Start it with:  cloudflared tunnel --url http://localhost:8000
//   Each quick-tunnel run mints a NEW url — paste it here and rebuild the APK.
// LOCAL (Expo Go, same WiFi): use the Mac's LAN IP instead, e.g.
//   export const BACKEND_URL = "http://192.168.31.120:8000";
export const BACKEND_URL = "https://quarterly-harrison-heavy-jewel.trycloudflare.com";
