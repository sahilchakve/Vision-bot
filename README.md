# Vision Bot (Android APK)

Instagram DM bot app with a Start/Stop button. Build the APK on GitHub Actions and install it on your phone.

## Build the APK
1. Push this repo to GitHub (branch `main`).
2. Go to the **Actions** tab, open **Build Android APK**, and wait for it to finish (30 to 60 minutes the first time).
3. Download the `vision-bot-apk` artifact and install the APK on your phone. Allow "Install unknown apps" for your browser or file manager.

## Use the app
1. Open the app and fill in: Gemini API key, bot Instagram username and password, your name and handle.
2. Tap **START BOT**. The log shows login status and replies.
3. Keep the app open. Android may stop background apps, so turn off battery optimization for this app.

## Safety
- Use a **secondary** Instagram account for the bot, never your main account.
- Never commit real keys or passwords. The app stores your settings only on your phone.
- Automating Instagram breaks its Terms of Service. Expect possible restrictions.
