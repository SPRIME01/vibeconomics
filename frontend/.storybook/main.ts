import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  "stories": [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  "addons": [
    "@storybook/addon-onboarding",
    "@chromatic-com/storybook",
    "@storybook/addon-docs", // Maintained as per current setup
    "@storybook/addon-a11y",
    "@storybook/addon-vitest",
    "@storybook/addon-links", // Added
    "@storybook/addon-interactions", // Added
    "msw-storybook-addon" // Added for MSW integration
  ],
  "framework": {
    "name": "@storybook/react-vite",
    "options": {}
  }
};
export default config;