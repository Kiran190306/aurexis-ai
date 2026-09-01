# Jarvis AI - Android Application

Android mobile application for the Jarvis AI platform built with Kotlin and Jetpack Compose.

## Development

### Prerequisites
- Android Studio Hedgehog (2023.1.1) or later
- JDK 17
- Android SDK API 33+

### Installation

1. Clone the repository
2. Open the project in Android Studio
3. Sync Gradle files
4. Run the application on an emulator or physical device

### Building

```bash
# Debug build
./gradlew assembleDebug

# Release build
./gradlew assembleRelease

# Install debug APK
./gradlew installDebug
```

## Project Structure

```
android-app/
├── app/
│   └── src/
│       └── main/
│           ├── java/com/jarvis/ai/
│           │   ├── data/          # Data layer (API, repositories, stores)
│           │   ├── ui/            # UI layer (screens, components, theme)
│           │   ├── MainActivity.kt
│           │   └── JarvisApplication.kt
│           ├── res/               # Resources
│           └── AndroidManifest.xml
└── build.gradle.kts
```

## Features

- Native Android UI with Jetpack Compose
- Material Design 3 theming
- Secure token storage
- Offline-first architecture
- Push notifications support
- Biometric authentication
- Camera and microphone integration

## Configuration

API endpoint and other configurations should be set in `local.properties`:

```properties
API_URL=https://api.jarvis.ai
API_KEY=your_api_key
```

## Architecture

The app follows MVVM architecture with:
- **Data Layer**: API clients, repositories, and local storage
- **Domain Layer**: Use cases and business logic
- **UI Layer**: Compose screens and view models

## Permissions

The app requires the following permissions:
- INTERNET
- ACCESS_NETWORK_STATE
- INTERNET
- ACCESS_NETWORK_STATE
- POST_NOTIFICATIONS

## License

MIT
