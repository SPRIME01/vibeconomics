#!/bin/bash

# Storybook Setup Script - Idempotent Installation and Configuration
# Usage: ./setup-storybook.sh [frontend-directory]
# If no directory specified, assumes script is in scripts/ and frontend is ../frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Determine frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -eq 0 ]; then
    # If no argument provided, assume we're in scripts/ and frontend is ../frontend
    if [[ "$SCRIPT_DIR" == */scripts ]]; then
        FRONTEND_DIR="$(dirname "$SCRIPT_DIR")/frontend"
    else
        FRONTEND_DIR="$SCRIPT_DIR/frontend"
    fi
else
    FRONTEND_DIR="$1"
fi

# Convert to absolute path and navigate there
FRONTEND_DIR="$(cd "$FRONTEND_DIR" 2>/dev/null && pwd)" || {
    print_error "Frontend directory not found: $FRONTEND_DIR"
    print_error "Please ensure the frontend directory exists or specify the correct path"
    exit 1
}

cd "$FRONTEND_DIR"

print_status "Setting up Storybook in directory: $(pwd)"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    print_error "package.json not found in $FRONTEND_DIR"
    print_error "Please ensure this is the correct React frontend directory"
    exit 1
fi

# Check if it's a React project
if ! grep -q "react" package.json; then
    print_error "This doesn't appear to be a React project"
    exit 1
fi

print_success "React project detected"

# Check if Storybook is already installed
if [ -d ".storybook" ] && grep -q "@storybook" package.json; then
    print_warning "Storybook appears to already be installed"
    print_status "Checking and updating configuration..."
else
    print_status "Installing Storybook..."

    # Clean npm cache to avoid ETARGET errors
    print_status "Cleaning npm cache to avoid dependency conflicts..."
    npm cache clean --force

    # Update npm to latest version
    print_status "Updating npm to latest version..."
    npm install -g npm@latest

    # Initialize Storybook with specific version and retry logic
    print_status "Initializing Storybook (this may take a few minutes)..."

    # First attempt with latest
    if ! npx storybook@latest init --yes --package-manager npm --skip-install; then
        print_warning "Initial Storybook setup failed, trying with manual dependency installation..."

        # Manual installation approach
        print_status "Installing Storybook dependencies manually..."
        npm install --save-dev @storybook/react-vite @storybook/react @storybook/addon-essentials @storybook/addon-interactions @storybook/test

        # Try init again with skip-install
        if ! npx storybook@latest init --yes --package-manager npm --skip-install; then
            print_error "Storybook initialization failed. Please check the storybook.log file for details."
            print_error "You may need to manually install Storybook or check for package conflicts."
            exit 1
        fi
    fi

    # Install any missing dependencies
    print_status "Installing any missing Storybook dependencies..."
    npm install

    print_success "Storybook initialized"
fi

# Install additional useful addons
print_status "Installing additional Storybook addons..."

ADDONS=(
    "@storybook/addon-docs"
    "@storybook/addon-controls"
    "@storybook/addon-actions"
    "@storybook/addon-viewport"
    "@storybook/addon-backgrounds"
    "@storybook/addon-toolbars"
    "@storybook/addon-measure"
    "@storybook/addon-outline"
    "@storybook/addon-a11y"
)

for addon in "${ADDONS[@]}"; do
    if ! grep -q "$addon" package.json; then
        print_status "Installing $addon..."
        if ! npm install --save-dev "$addon"; then
            print_warning "Failed to install $addon, continuing with setup..."
        fi
    else
        print_status "$addon already installed"
    fi
done

# Create or update main Storybook configuration
print_status "Configuring Storybook main settings..."

cat > .storybook/main.js << 'EOF'
/** @type { import('@storybook/react-vite').StorybookConfig } */
const config = {
  stories: ['../src/**/*.stories.@(js|jsx|mjs|ts|tsx|mdx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-onboarding',
    '@storybook/addon-interactions',
    '@storybook/addon-docs',
    '@storybook/addon-controls',
    '@storybook/addon-actions',
    '@storybook/addon-viewport',
    '@storybook/addon-backgrounds',
    '@storybook/addon-toolbars',
    '@storybook/addon-measure',
    '@storybook/addon-outline',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  typescript: {
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) => (prop.parent ? !/node_modules/.test(prop.parent.fileName) : true),
    },
  },
  docs: {
    autodocs: 'tag',
  },
  // Configure for potential Docker usage
  core: {
    disableTelemetry: true,
  },
  // Allow external access (needed for Docker)
  viteFinal: async (config) => {
    if (config.server) {
      config.server.host = '0.0.0.0';
      config.server.port = 6006;
    }
    return config;
  },
};

export default config;
EOF

# Create or update preview configuration
print_status "Configuring Storybook preview settings..."

cat > .storybook/preview.js << 'EOF'
import '../src/index.css'; // Import your main CSS file

/** @type { import('@storybook/react').Preview } */
const preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    docs: {
      toc: true, // Enable table of contents
    },
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#ffffff' },
        { name: 'dark', value: '#333333' },
        { name: 'gray', value: '#f8f9fa' },
      ],
    },
    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile',
          styles: { width: '375px', height: '667px' },
        },
        tablet: {
          name: 'Tablet',
          styles: { width: '768px', height: '1024px' },
        },
        desktop: {
          name: 'Desktop',
          styles: { width: '1200px', height: '800px' },
        },
      },
    },
  },
  tags: ['autodocs'],
};

export default preview;
EOF

# Create stories directory structure
print_status "Creating stories directory structure..."

mkdir -p src/stories/components
mkdir -p src/stories/pages

# Create a sample Button component and story if it doesn't exist
if [ ! -f "src/components/Button.jsx" ] && [ ! -f "src/components/Button.tsx" ]; then
    print_status "Creating sample Button component..."

    mkdir -p src/components

    cat > src/components/Button.jsx << 'EOF'
import React from 'react';
import PropTypes from 'prop-types';
import './Button.css';

/**
 * Primary UI component for user interaction
 */
export const Button = ({ primary, backgroundColor, size, label, ...props }) => {
  const mode = primary ? 'storybook-button--primary' : 'storybook-button--secondary';

  return (
    <button
      type="button"
      className={['storybook-button', `storybook-button--${size}`, mode].join(' ')}
      style={{ backgroundColor }}
      {...props}
    >
      {label}
    </button>
  );
};

Button.propTypes = {
  /**
   * Is this the principal call to action on the page?
   */
  primary: PropTypes.bool,
  /**
   * What background color to use
   */
  backgroundColor: PropTypes.string,
  /**
   * How large should the button be?
   */
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  /**
   * Button contents
   */
  label: PropTypes.string.isRequired,
  /**
   * Optional click handler
   */
  onClick: PropTypes.func,
};

Button.defaultProps = {
  backgroundColor: null,
  primary: false,
  size: 'medium',
  onClick: undefined,
};
EOF

    cat > src/components/Button.css << 'EOF'
.storybook-button {
  font-family: 'Nunito Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-weight: 700;
  border: 0;
  border-radius: 3em;
  cursor: pointer;
  display: inline-block;
  line-height: 1;
}

.storybook-button--primary {
  color: white;
  background-color: #1ea7fd;
}

.storybook-button--secondary {
  color: #333;
  background-color: transparent;
  box-shadow: rgba(0, 0, 0, 0.15) 0px 0px 0px 1px inset;
}

.storybook-button--small {
  font-size: 12px;
  padding: 10px 16px;
}

.storybook-button--medium {
  font-size: 14px;
  padding: 11px 20px;
}

.storybook-button--large {
  font-size: 16px;
  padding: 12px 24px;
}
EOF

    cat > src/components/Button.stories.js << 'EOF'
import { fn } from '@storybook/test';
import { Button } from './Button';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories#default-export
export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    // Optional parameter to center the component in the Canvas
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile button component that supports different sizes, colors, and states.',
      },
    },
  },
  // This component will have an automatically generated Autodocs entry: https://storybook.js.org/docs/writing-docs/autodocs
  tags: ['autodocs'],
  // More on argTypes: https://storybook.js.org/docs/api/argtypes
  argTypes: {
    backgroundColor: { control: 'color' },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
    },
  },
  // Use `fn` to spy on the onClick arg, which will appear in the actions panel once invoked: https://storybook.js.org/docs/essentials/actions#action-args
  args: { onClick: fn() },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary = {
  args: {
    primary: true,
    label: 'Button',
  },
};

export const Secondary = {
  args: {
    label: 'Button',
  },
};

export const Large = {
  args: {
    size: 'large',
    label: 'Button',
  },
};

export const Small = {
  args: {
    size: 'small',
    label: 'Button',
  },
};

export const CustomColor = {
  args: {
    primary: true,
    backgroundColor: '#ff6b6b',
    label: 'Custom Color',
  },
};
EOF

    print_success "Sample Button component created"
fi

# Create a comprehensive test story
print_status "Creating test story to verify Storybook setup..."

cat > src/stories/StorybookTest.stories.js << 'EOF'
export default {
  title: 'Tests/Storybook Setup Test',
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'This story verifies that Storybook is properly configured with all addons working.',
      },
    },
  },
  tags: ['autodocs'],
};

// Test story to verify all addons are working
export const SetupVerification = {
  render: () => {
    return (
      <div style={{ padding: '20px', maxWidth: '600px' }}>
        <h2>🎉 Storybook Setup Verification</h2>
        <div style={{ marginBottom: '20px' }}>
          <h3>✅ Addons Test Checklist:</h3>
          <ul style={{ textAlign: 'left', lineHeight: '1.6' }}>
            <li><strong>Controls:</strong> Check the Controls panel below</li>
            <li><strong>Actions:</strong> Click the button to see actions logged</li>
            <li><strong>Docs:</strong> This documentation is auto-generated</li>
            <li><strong>Viewport:</strong> Try different viewport sizes from the toolbar</li>
            <li><strong>Backgrounds:</strong> Change background colors from the toolbar</li>
            <li><strong>Measure:</strong> Use the measure tool from the toolbar</li>
            <li><strong>Outline:</strong> Toggle element outlines from the toolbar</li>
            <li><strong>A11y:</strong> Check accessibility panel for violations</li>
          </ul>
        </div>

        <button
          onClick={() => console.log('Button clicked!')}
          style={{
            padding: '12px 24px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Test Actions Addon
        </button>

        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          <p><strong>Next Steps:</strong></p>
          <ol style={{ textAlign: 'left', marginLeft: '20px' }}>
            <li>Create stories for your existing components</li>
            <li>Use the Controls addon to make your stories interactive</li>
            <li>Add JSDoc comments to your components for better documentation</li>
            <li>Use the A11y addon to ensure your components are accessible</li>
          </ol>
        </div>
      </div>
    );
  },
  argTypes: {
    title: {
      control: 'text',
      description: 'Test the controls addon by changing this title'
    },
    showDetails: {
      control: 'boolean',
      description: 'Toggle additional details'
    },
    theme: {
      control: { type: 'select' },
      options: ['light', 'dark', 'colorful'],
      description: 'Select a theme'
    }
  },
  args: {
    title: 'Storybook is Working!',
    showDetails: true,
    theme: 'light'
  }
};
EOF

# Update package.json scripts if needed
print_status "Updating package.json scripts..."

# Check if storybook scripts exist, if not add them
if ! grep -q "\"storybook\":" package.json; then
    # Add storybook script with host configuration for Docker
    npm pkg set scripts.storybook="storybook dev -p 6006 --host 0.0.0.0"
fi

if ! grep -q "\"build-storybook\":" package.json; then
    # Add build-storybook script
    npm pkg set scripts.build-storybook="storybook build"
fi

# Add Docker-specific storybook script
if ! grep -q "\"storybook:docker\":" package.json; then
    npm pkg set scripts.storybook:docker="storybook dev -p 6006 --host 0.0.0.0 --no-open"
fi

# Create .gitignore entries for Storybook if .gitignore exists
if [ -f ".gitignore" ]; then
    print_status "Updating .gitignore for Storybook..."

    if ! grep -q "storybook-static" .gitignore; then
        echo "" >> .gitignore
        echo "# Storybook" >> .gitignore
        echo "storybook-static/" >> .gitignore
    fi
fi

# Create Docker Compose override for Storybook
print_status "Creating Docker Compose override for Storybook..."

# Check if we're in a project with docker-compose files
PROJECT_ROOT="$(dirname "$FRONTEND_DIR")"
if [ -f "$PROJECT_ROOT/docker-compose.yml" ] || [ -f "$PROJECT_ROOT/docker-compose.yaml" ]; then
    cat > "$PROJECT_ROOT/docker-compose.storybook.yml" << 'EOF'
# Docker Compose override for Storybook development
# Usage: docker compose -f docker-compose.yml -f docker-compose.storybook.yml up

version: '3.8'

services:
  storybook:
    build:
      context: ./frontend
      dockerfile: Dockerfile.storybook
    ports:
      - "6006:6006"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - STORYBOOK_TELEMETRY_DISABLED=1
    command: npm run storybook:docker
    restart: unless-stopped
    depends_on:
      - frontend
    networks:
      - default

  # Production Storybook (static build)
  storybook-static:
    image: nginx:alpine
    volumes:
      - ./frontend/storybook-static:/usr/share/nginx/html:ro
    ports:
      - "6007:80"
    labels:
      - traefik.enable=true
      - traefik.http.routers.storybook-static.rule=Host(`storybook.${DOMAIN:-localhost}`)
      - traefik.http.routers.storybook-static.tls=true
      - traefik.http.routers.storybook-static.tls.certresolver=le
      - traefik.http.services.storybook-static.loadbalancer.server.port=80
    networks:
      - default
    profiles:
      - production
EOF

    # Create a Dockerfile for Storybook if it doesn't exist
    if [ ! -f "$FRONTEND_DIR/Dockerfile.storybook" ]; then
        cat > "$FRONTEND_DIR/Dockerfile.storybook" << 'EOF'
# Dockerfile for Storybook development
FROM node:18-alpine

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Expose Storybook port
EXPOSE 6006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:6006 || exit 1

# Disable telemetry
ENV STORYBOOK_TELEMETRY_DISABLED=1

# Start Storybook
CMD ["npm", "run", "storybook:docker"]
EOF
    fi

    print_success "Docker Compose configuration created"
    print_status "To run Storybook with Docker: docker compose -f docker-compose.yml -f docker-compose.storybook.yml up storybook"
    print_status "To run static Storybook: docker compose --profile production -f docker-compose.yml -f docker-compose.storybook.yml up storybook-static"
fi

# Create a simple README for Storybook usage
print_status "Creating Storybook documentation..."

cat > STORYBOOK.md << 'EOF'
# Storybook Documentation

## Overview
Storybook is set up for developing and documenting UI components in isolation.

## Getting Started

### Local Development
```bash
npm run storybook
```
This starts Storybook on http://localhost:6006

### Docker Development
```bash
# From project root
docker compose -f docker-compose.yml -f docker-compose.storybook.yml up storybook
```
This starts Storybook in a Docker container on http://localhost:6006

### Build Storybook for Production
```bash
npm run build-storybook
```

## Available Scripts
- `npm run storybook` - Start Storybook locally
- `npm run storybook:docker` - Start Storybook configured for Docker (no auto-open)
- `npm run build-storybook` - Build static Storybook

## Deployment Options

### Development
- Local: `npm run storybook`
- Docker: `docker compose -f docker-compose.yml -f docker-compose.storybook.yml up storybook`

### Production
- Build static: `npm run build-storybook`
- Serve static: `docker compose --profile production -f docker-compose.yml -f docker-compose.storybook.yml up storybook-static`

## Writing Stories

### Basic Story Structure
```javascript
export default {
  title: 'Components/MyComponent',
  component: MyComponent,
  tags: ['autodocs'],
};

export const Default = {
  args: {
    prop1: 'value1',
    prop2: 'value2',
  },
};
```

### Best Practices
1. **Use descriptive titles**: `Components/Button` instead of just `Button`
2. **Add documentation**: Use JSDoc comments on your components
3. **Create multiple variants**: Show different states of your component
4. **Use controls**: Make your stories interactive with argTypes
5. **Test accessibility**: Use the A11y addon to catch accessibility issues

## Installed Addons
- **Controls**: Interactive controls for component props
- **Actions**: Log component interactions
- **Docs**: Auto-generated documentation
- **Viewport**: Test different screen sizes
- **Backgrounds**: Test different background colors
- **Measure**: Measure spacing and dimensions
- **Outline**: Show element boundaries
- **A11y**: Accessibility testing

## Component Documentation
Add JSDoc comments to your components for better auto-generated docs:

```javascript
/**
 * Primary UI component for user interaction
 */
export const Button = ({
  /**
   * Is this the principal call to action on the page?
   */
  primary = false,
  /**
   * Button contents
   */
  label,
  ...props
}) => {
  // Component implementation
};
```

## Docker Integration
When running in Docker, Storybook is configured to:
- Listen on `0.0.0.0:6006` for external access
- Disable telemetry for better performance
- Skip auto-opening browser (handled by Docker host)

## File Structure
```
frontend/
  src/
    components/
      Button/
        Button.jsx
        Button.stories.js
        Button.css
    stories/
      components/
      pages/
  .storybook/
    main.js
    preview.js
```
EOF

print_success "Storybook setup completed successfully!"

echo ""
print_status "🚀 Next Steps:"
echo "1. Start Storybook locally: npm run storybook"
echo "2. Or start with Docker: docker compose -f docker-compose.yml -f docker-compose.storybook.yml up storybook"
echo "3. Open http://localhost:6006 in your browser"
echo "4. Check the 'Tests/Storybook Setup Test' story to verify everything is working"
echo "5. Create stories for your existing components"
echo "6. Read STORYBOOK.md for best practices and usage guidelines"
echo ""
echo "📁 Files created/updated:"
echo "   - .storybook/main.js (Storybook configuration)"
echo "   - .storybook/preview.js (Preview configuration)"
echo "   - docker-compose.storybook.yml (Docker integration)"
echo "   - frontend/Dockerfile.storybook (Storybook Docker image)"
echo "   - frontend/STORYBOOK.md (Documentation)"
echo ""
echo "⚠️  If you encountered issues during setup:"
echo "   - Check frontend/storybook.log for detailed error information"
echo "   - Run 'npm cache clean --force' and try again"
echo "   - Ensure all dependencies are up to date with 'npm update'"
echo ""

print_success "Happy storytelling! 📚✨"
