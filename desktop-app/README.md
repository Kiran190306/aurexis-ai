# Jarvis AI - Desktop Application

Desktop application for the Jarvis AI platform built with Electron and React.

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

This will start both the Electron main process and the React renderer in development mode with hot reload.

### Building

```bash
npm run build
```

### Packaging

```bash
# Build for current platform
npm run dist

# Build for specific platforms
npm run dist:win    # Windows
npm run dist:mac    # macOS
npm run dist:linux  # Linux
```

## Project Structure

```
desktop-app/
├── src/
│   ├── main/           # Electron main process
│   ├── preload/        # Preload scripts
│   └── renderer/       # React application
│       └── src/
│           ├── components/
│           ├── pages/
│           └── ...
├── resources/          # Icons and assets
└── package.json
```

## Features

- Cross-platform desktop application (Windows, macOS, Linux)
- Persistent local storage using electron-store
- Auto-updates support
- Native system integration
- Full-featured React UI matching web platform

## Configuration

Environment variables and API configuration should be set in the application settings or via the backend API.

## License

MIT
