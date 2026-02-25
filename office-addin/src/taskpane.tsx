import React, { useEffect, useState } from 'react';
import { readSysMeta, readRefData, BlockMetadata, getVisibleGridSnapshot, writeScheduleCell, getActiveSheetName } from './excel-utils';
import { validateScheduleLocal, ValidationWarning } from './acgme-validator';

// ---------------------------------------------------------------------------
// OPSEC: LLM endpoint allowlist. The grid snapshot may contain PII (resident
// names, schedule assignments). Only send data to trusted local endpoints.
// ---------------------------------------------------------------------------
const ALLOWED_LLM_HOSTS = ['localhost', '127.0.0.1', '[::1]'];
const MAX_EDITS = 200;
const NAME_COL_INDEX = 5; // Column F — typically contains resident names

function isEndpointAllowed(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ALLOWED_LLM_HOSTS.includes(parsed.hostname);
  } catch {
    return false;
  }
}

/** Replace name column with anonymized tokens before sending grid to LLM */
function redactGrid(grid: any[][]): any[][] {
  const tokenMap = new Map<string, string>();
  let counter = 1;
  return grid.map(row => {
    if (!row) return row;
    const copy = [...row];
    const name = copy[NAME_COL_INDEX];
    if (typeof name === 'string' && name.trim() !== '' && name.trim() !== 'Name' && name.trim() !== 'Resident') {
      if (!tokenMap.has(name)) {
        tokenMap.set(name, `Person_${counter++}`);
      }
      copy[NAME_COL_INDEX] = tokenMap.get(name);
    }
    return copy;
  });
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function Taskpane() {
  const [meta, setMeta] = useState<BlockMetadata | null>(null);
  const [refs, setRefs] = useState<{rotations: string[], activities: string[]} | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [endpoint, setEndpoint] = useState('http://localhost:11434/api/generate'); // Default Ollama
  const [warnings, setWarnings] = useState<ValidationWarning[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        const metadata = await readSysMeta();
        const refData = await readRefData();
        setMeta(metadata);
        setRefs(refData);
        if (metadata?.llm_rules_of_engagement) {
          setMessages([{ role: 'assistant', content: 'Ready. Rules of engagement loaded.' }]);
        }
      } catch (err: any) {
        setError(err.message || 'Error loading Excel metadata');
      }
    }
    loadData();
  }, []);

  const handleValidate = async () => {
    if (!refs) return;
    try {
      const grid = await getVisibleGridSnapshot();
      const localWarnings = validateScheduleLocal(grid, refs);
      setWarnings(localWarnings);
      if (localWarnings.length === 0) {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Local validation passed: No ACGME violations found.' }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `Local validation failed: Found ${localWarnings.length} potential violations.` }]);
      }
    } catch (e: any) {
       setError(e.message || "Failed to validate grid");
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setIsLoading(true);

    try {
      // OPSEC: Validate endpoint before sending any data
      if (!isEndpointAllowed(endpoint)) {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Endpoint blocked: Only localhost endpoints are allowed to prevent PII exfiltration. Update the LLM Endpoint field to a localhost address.' }]);
        setIsLoading(false);
        return;
      }

      const rawGrid = await getVisibleGridSnapshot();
      const grid = redactGrid(rawGrid);
      const prompt = `
System Rules: ${meta?.llm_rules_of_engagement || 'You are an AI assistant.'}
Valid Rotations: ${refs?.rotations.join(', ')}
Valid Activities: ${refs?.activities.join(', ')}
Current Grid Snapshot:
${JSON.stringify(grid)}

User Request: ${userMsg}

Output ONLY valid JSON in this format:
{"thoughts": "your reasoning", "edits": [{"row": 10, "col": 6, "value": "LV"}]}
Do not include markdown blocks or any other text outside the JSON.
`;

      // Simple fetch to local Ollama (Llama 3 or similar)
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'llama3', // Adjust as needed
          prompt: prompt,
          stream: false,
          format: 'json'
        })
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();

      const responseText = data.response;
      let parsed;
      try {
        parsed = JSON.parse(responseText);
      } catch (e) {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error parsing JSON from LLM: ${responseText}` }]);
        setIsLoading(false);
        return;
      }

      const edits = parsed.edits || [];
      if (edits.length > MAX_EDITS) {
        setMessages(prev => [...prev, { role: 'assistant', content: `Refused: LLM requested ${edits.length} edits (max ${MAX_EDITS}). This may indicate a malformed response.` }]);
        setIsLoading(false);
        return;
      }
      if (edits.length > 0) {
        const sheetName = await getActiveSheetName();
        for (const edit of edits) {
          // Validate edit shape
          if (typeof edit.row !== 'number' || typeof edit.col !== 'number' || typeof edit.value !== 'string') {
            setMessages(prev => [...prev, { role: 'assistant', content: `Skipped malformed edit: ${JSON.stringify(edit)}` }]);
            continue;
          }
          // validate codes
          if (!refs?.activities.includes(edit.value) && !refs?.rotations.includes(edit.value) && edit.value !== "") {
             setMessages(prev => [...prev, { role: 'assistant', content: `Refused invalid code: ${edit.value}` }]);
             continue;
          }
          await writeScheduleCell(sheetName, edit.row, edit.col, edit.value);
        }
        setMessages(prev => [...prev, { role: 'assistant', content: `Thoughts: ${parsed.thoughts}\nExecuted ${edits.length} edits.` }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `Thoughts: ${parsed.thoughts}\nNo edits needed.` }]);
      }

    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: '16px', fontFamily: 'sans-serif', display: 'flex', flexDirection: 'column', height: '100vh', boxSizing: 'border-box' }}>
      <h2>AAPM AI Assistant</h2>
      {error && <div style={{ color: 'red', marginBottom: '8px' }}>{error}</div>}

      <div style={{ marginBottom: '8px', fontSize: '12px', display: 'flex', gap: '8px' }}>
        <button onClick={handleValidate} style={{ padding: '4px 8px' }}>Validate Schedule</button>
      </div>

      {warnings.length > 0 && (
        <div style={{ marginBottom: '8px', padding: '8px', background: '#ffebeb', borderLeft: '4px solid red' }}>
          <h4 style={{ margin: '0 0 4px 0', color: 'red' }}>Warnings ({warnings.length})</h4>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px' }}>
            {warnings.map((w, i) => (
              <li key={i}>Row {w.row} ({w.personName}): {w.message}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginBottom: '8px', fontSize: '12px' }}>
        <label>LLM Endpoint: </label>
        <input
          value={endpoint}
          onChange={e => setEndpoint(e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      <div style={{ flexGrow: 1, overflowY: 'auto', border: '1px solid #ccc', padding: '8px', marginBottom: '8px', background: '#f9f9f9' }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: '8px', textAlign: m.role === 'user' ? 'right' : 'left' }}>
            <div style={{
              display: 'inline-block',
              padding: '8px',
              borderRadius: '4px',
              background: m.role === 'user' ? '#0078d4' : '#e1dfdd',
              color: m.role === 'user' ? '#fff' : '#000',
              maxWidth: '80%',
              wordWrap: 'break-word',
              whiteSpace: 'pre-wrap'
            }}>
              {m.content}
            </div>
          </div>
        ))}
        {isLoading && <div style={{ fontStyle: 'italic' }}>Thinking...</div>}
      </div>

      <div style={{ display: 'flex' }}>
        <input
          style={{ flexGrow: 1, padding: '8px' }}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="e.g. Swap Dr. Vance's Call on Tuesday..."
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isLoading}
          style={{ padding: '8px 16px', marginLeft: '4px', background: '#0078d4', color: '#fff', border: 'none', cursor: 'pointer' }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
