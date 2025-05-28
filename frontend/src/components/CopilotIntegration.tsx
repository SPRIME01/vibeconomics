import React from 'react';
import CopilotSidebar, { CopilotSidebarProps } from './CopilotSidebar';
import CopilotActions, { CopilotActionsProps } from './CopilotActions';

/**
 * Props for the CopilotIntegration component.
 */
export interface CopilotIntegrationProps {
  /**
   * Props to pass down to the CopilotSidebar component.
   */
  sidebarProps?: CopilotSidebarProps;
  /**
   * Props to pass down to the CopilotActions component.
   */
  actionsProps?: CopilotActionsProps;
  /**
   * An example prop to influence the page context,
   * which might be read by `useCopilotReadable` in the Sidebar.
   * @default "Integrated Copilot Page"
   */
  initialPageTitle?: string;
}

/**
 * @file CopilotIntegration.tsx
 * @description This component integrates CopilotSidebar and CopilotActions
 * to provide a cohesive CopilotKit experience. It demonstrates how actions defined
 * in CopilotActions can be invoked from the CopilotSidebar, and how context
 * from the application (simulated by `initialPageTitle`) can be made available
 * to the Copilot.
 *
 * The CopilotKitProvider is assumed to be wrapping this component at a higher level
 * in the application or via a decorator in Storybook stories.
 */
const CopilotIntegration: React.FC<CopilotIntegrationProps> = ({
  sidebarProps,
  actionsProps,
  initialPageTitle = "Integrated Copilot Page"
}) => {
  /**
   * Effect to update the document title based on the `initialPageTitle` prop.
   * This simulates how an application might set context that `useCopilotReadable`
   * (potentially within CopilotSidebar) could pick up.
   */
  React.useEffect(() => {
    document.title = initialPageTitle;
    // If CopilotSidebar's useCopilotReadable needs to be explicitly updated,
    // a mechanism to trigger that update would be needed here,
    // e.g., by passing initialPageTitle as a prop to CopilotSidebar if it's designed to re-evaluate context.
    // For this example, we assume CopilotSidebar's context might pick up document.title or use its own props.
  }, [initialPageTitle]);

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif', color: '#333' }}>
      <div style={{ flexGrow: 1, padding: '20px', overflowY: 'auto' }}>
        <h2>Application Content Area</h2>
        <p>This area represents the main content of your application.</p>
        <p>Interact with the Copilot Sidebar on the right. Try commands like:</p>
        <ul>
          <li>"Summarize this text: The quick brown fox jumps over the lazy dog."</li>
          <li>"Create a new task titled 'Review Integration' with description 'Check sidebar and actions working together'."</li>
          <li>"Notify me with the message 'Integration looks good!' type info."</li>
          <li>"What is the current page title?" (This will test context provided by `useCopilotReadable` in the Sidebar, which should reflect `initialPageTitle` if correctly set up there or if it reads `document.title`).</li>
        </ul>
        {/* 
          CopilotActions defines the actions available to the Copilot system.
          It doesn't render significant UI itself but makes actions available
          when it's part of the rendered tree within a CopilotKitProvider.
          The debug UI within CopilotActions will show the last action's output.
        */}
        <CopilotActions {...actionsProps} />
      </div>
      <div style={{ width: '350px', borderLeft: '1px solid #ccc', flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
        {/* 
          CopilotSidebar provides the chat interface.
          Its `useCopilotReadable` hook should be configured to pick up relevant context,
          potentially influenced by props like `initialPageTitle` or by reading `document.title`.
          The sidebarProps are passed down to configure its behavior (e.g., defaultOpen).
        */}
        <CopilotSidebar {...sidebarProps} />
      </div>
    </div>
  );
};

export default CopilotIntegration;
