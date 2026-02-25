import React from 'react';
import { createRoot } from 'react-dom/client';
import Taskpane from './taskpane';

Office.onReady(() => {
  const root = createRoot(document.getElementById('root')!);
  root.render(
    <React.StrictMode>
      <Taskpane />
    </React.StrictMode>
  );
});
