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
