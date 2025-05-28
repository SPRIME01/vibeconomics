import React, { useState } from 'react';
// Assuming these are the correct import paths and names from CopilotKit
import { CopilotSidebar as CKCopilotSidebar } from "@copilotkit/react-ui"; 
import { useCopilotReadable } from "@copilotkit/react-core";

/**
 * Represents the context of the current page, to be made readable by the Copilot.
 */
interface PageContext {
  pageTitle: string;
  userId: string | null;
}

/**
 * Props for the CopilotSidebar component.
 */
export interface CopilotSidebarProps {
  /**
   * Determines if the sidebar should be open by default.
   * @default true
   */
  defaultOpen?: boolean;
}

/**
 * CopilotSidebar component integrates the CopilotKit Sidebar UI.
 * It also demonstrates how to make application state (e.g., page context)
 * available to the Copilot using the `useCopilotReadable` hook.
 */
const CopilotSidebar: React.FC<CopilotSidebarProps> = ({ defaultOpen = true }) => {
  const [pageContext, setPageContext] = useState<PageContext>({
    pageTitle: "Default Page Title", // Initial page title
    userId: "user-123", // Example user ID
  });

  // Expose pageContext to CopilotKit, making it readable by the AI.
  // This allows the AI to have context about the current page or user.
  useCopilotReadable({
    description: "The current page context including title and user ID.",
    value: pageContext,
  });

  /**
   * Simulates changing the page context.
   * In a real application, this might be triggered by navigation or other state changes.
   * @param newPageTitle The new title for the page.
   */
  const changePageContext = (newPageTitle: string) => {
    setPageContext(prev => ({ ...prev, pageTitle: newPageTitle }));
  };

  return (
    <div>
      {/* This button is for local testing/demonstration of context updates. */}
      {/* It's not intended as a primary feature of the sidebar itself. */}
      <button 
        onClick={() => changePageContext(`Page Updated At ${new Date().toLocaleTimeString()}`)}
        style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 10000 }} // Basic styling for visibility
      >
        Update Page Context (Test)
      </button>

      <CKCopilotSidebar
        defaultOpen={defaultOpen}
        labels={{
          title: "AI Copilot",
          initial: "Hello! How can I help you today?",
        }}
        // The backend endpoint (e.g., /copilot/execute or /copilot/mock for Storybook)
        // is configured in the CopilotKitProvider, which should wrap this component
        // either in the main application or via a decorator in Storybook.
      >
        {/* CKCopilotSidebar might allow children for further customization,
            or it might be a self-contained UI. Refer to CopilotKit documentation. */}
      </CKCopilotSidebar>
    </div>
  );
};

export default CopilotSidebar;
