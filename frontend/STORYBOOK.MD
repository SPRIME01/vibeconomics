# Storybook Documentation

This document provides guidelines and information for using Storybook in this project.

## Table of Contents

- [Running Storybook](#running-storybook)
- [Writing Stories](#writing-stories)
- [Folder Structure](#folder-structure)
- [Available Addons](#available-addons)
- [CopilotKit Integration Testing](#copilotkit-integration-testing)

## Running Storybook

To run Storybook locally, use the following command:

```bash
npm run storybook
# or
yarn storybook
```

This will start the Storybook development server, usually on `http://localhost:6006`.

## Writing Stories

Stories are written in `.stories.tsx` (or `.stories.ts`, `.stories.js`, `.stories.mdx`) files. They follow the Component Story Format (CSF).

Example:

```typescript
// src/components/MyComponent.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { MyComponent } from './MyComponent';

const meta: Meta<typeof MyComponent> = {
  title: 'Components/MyComponent',
  component: MyComponent,
  parameters: {
    layout: 'centered', // Example parameter
  },
  tags: ['autodocs'], // Enable Autodocs
  argTypes: {
    backgroundColor: { control: 'color' }, // Example argType
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: 'Button',
  },
};
```

## Folder Structure

- **`.storybook/`**: Contains Storybook configuration files (`main.ts`, `preview.ts`, custom decorators, etc.).
- **`src/stories/`**: Can be used for global stories or documentation pages (e.g., introduction, color palettes).
- Component-specific stories are typically co-located with their components (e.g., `src/components/MyComponent/MyComponent.stories.tsx`).

## Available Addons

This project's Storybook setup includes the following key addons:

- **`@storybook/addon-docs`**: For generating documentation from stories (Autodocs).
- **`@storybook/addon-controls`**: For interactively editing component arguments.
- **`@storybook/addon-actions`**: For logging events and callbacks.
- **`@storybook/addon-a11y`**: For accessibility testing.
- **`@storybook/addon-interactions`**: For writing interaction tests within stories.
- **`@storybook/addon-links`**: For creating links between stories.
- **`@chromatic-com/storybook`**: For visual regression testing with Chromatic.
- **`msw-storybook-addon`**: For mocking API requests (see [CopilotKit Integration Testing](#copilotkit-integration-testing)).

*(Note: Some addons like controls and actions might be bundled within `@storybook/addon-essentials` if it's used directly. The current setup lists them explicitly or includes them via `@storybook/addon-onboarding` and other packages listed in `.storybook/main.ts`.)*

## CopilotKit Integration Testing

To facilitate the development and testing of UI components that integrate with CopilotKit, this Storybook setup includes tools for mocking backend interactions.

### MSW (Mock Service Worker) Setup

We use `msw-storybook-addon` to mock API calls made by CopilotKit. This allows us to simulate various backend responses (success, error, specific data scenarios) directly within Storybook without needing a live backend.

- **Configuration:**
  - The addon is registered in `.storybook/main.ts`.
  - It's initialized in `.storybook/preview.ts` (via `initialize()` and `mswLoader`), making MSW active for all stories.
- **Usage:**
  - API mocks are typically defined within individual stories using the `msw` parameter or in a shared mock definition file.
  - For CopilotKit, this means we can mock the `/copilot/mock` (or a similar) endpoint that the `CopilotKitProvider` communicates with.

  Example of how mocks might be defined in a story (refer to MSW and `msw-storybook-addon` documentation for details):
  ```typescript
  // MyCopilotComponent.stories.tsx
  import { rest } from 'msw'; // Or your specific MSW import

  export const MyStory = {
    parameters: {
      msw: {
        handlers: [
          rest.post('/copilot/mock', (req, res, ctx) => {
            // Example: inspect req.body to provide different responses
            // const { scenario } = await req.json();
            // if (scenario === 'error') {
            //   return res(ctx.status(500), ctx.json({ message: "Mocked server error" }));
            // }
            return res(ctx.json({ reply: "This is a mocked AI response!" }));
          }),
        ],
      },
    },
  };
  ```

### `copilot-decorator.tsx`

A custom decorator, `CopilotProviderDecorator`, is available at `.storybook/copilot-decorator.tsx`.

- **Purpose:** This decorator wraps a story with a `CopilotKitProvider` (currently a placeholder, to be replaced with the actual component from `@copilotkit/react-core` or similar). This is essential for any component that uses CopilotKit hooks or context.
- **API Endpoint Configuration:**
  - By default, the `CopilotKitProvider` within this decorator is configured to use a `chatApiEndpoint` pointing to `/copilot/mock`. This endpoint should be handled by MSW mocks in your stories.
  - The API endpoint can be overridden globally by setting the `STORYBOOK_COPILOT_MOCK_API_URL` environment variable when running Storybook (e.g., in your `.env` file or shell).
    ```bash
    STORYBOOK_COPILOT_MOCK_API_URL=/api/custom_mock yarn storybook
    ```
- **How to Use:** Import and add it to the `decorators` array in your story file or component meta.

  ```typescript
  // src/components/MyCopilotFeature.stories.tsx
  import type { Meta, StoryObj } from '@storybook/react';
  import { MyCopilotFeature } from './MyCopilotFeature'; // Your component
  import { CopilotProviderDecorator } from '../../.storybook/copilot-decorator'; // Adjust path if needed

  const meta: Meta<typeof MyCopilotFeature> = {
    title: 'Features/MyCopilotFeature',
    component: MyCopilotFeature,
    decorators: [CopilotProviderDecorator], // Apply the decorator
    parameters: {
      // Example: MSW handlers for this story
      msw: {
        handlers: [
          rest.post('/copilot/mock', (req, res, ctx) => {
            return res(ctx.json({ reply: "Story-specific mock response!" }));
          }),
        ],
      },
    }
  };

  export default meta;
  type Story = StoryObj<typeof meta>;

  export const Default: Story = {
    args: {
      // ... your component's args
    },
  };
  ```

### Important Notes:

- **Install Dependencies:** Ensure `msw` and `msw-storybook-addon` are installed as dev dependencies:
  ```bash
  npm install -D msw msw-storybook-addon
  # or
  yarn add -D msw msw-storybook-addon
  ```
  (`msw` is a peer dependency for `msw-storybook-addon`).
- The `CopilotKitProvider` used in the decorator (`.storybook/copilot-decorator.tsx`) is currently a placeholder (`CopilotKitProviderPlaceholder`). It needs to be replaced with the actual provider component from the `@copilotkit/react-core` (or an equivalent) package once that package is integrated into the main frontend application. Remember to update the import path and any props passed to the provider to match the actual component's API.
---

*This document should be updated as Storybook configuration or practices evolve.*
