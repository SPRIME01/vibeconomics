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
