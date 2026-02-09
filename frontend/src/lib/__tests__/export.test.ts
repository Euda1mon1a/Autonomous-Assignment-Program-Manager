import { exportToCSV, exportToJSON, downloadFile, Column } from '../export';

// Mock URL.createObjectURL and URL.revokeObjectURL
const mockCreateObjectURL = jest.fn(() => 'blob:mock-url');
const mockRevokeObjectURL = jest.fn();
global.URL.createObjectURL = mockCreateObjectURL;
global.URL.revokeObjectURL = mockRevokeObjectURL;

// Track link clicks
let clickedLinks: HTMLAnchorElement[] = [];
const originalCreateElement = document.createElement.bind(document);

beforeEach(() => {
  clickedLinks = [];
  jest.clearAllMocks();

  jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
    const el = originalCreateElement(tag);
    if (tag === 'a') {
      jest.spyOn(el, 'click').mockImplementation(() => {
        clickedLinks.push(el as HTMLAnchorElement);
      });
    }
    return el;
  });

  jest.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
  jest.spyOn(document.body, 'removeChild').mockImplementation((node) => node);
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('downloadFile', () => {
  it('creates blob and triggers download', () => {
    downloadFile('content', 'test.txt', 'text/plain');

    expect(mockCreateObjectURL).toHaveBeenCalledTimes(1);
    expect(clickedLinks).toHaveLength(1);
    expect(clickedLinks[0].download).toBe('test.txt');
    expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });

  it('sets correct href from blob URL', () => {
    downloadFile('data', 'file.csv', 'text/csv');
    expect(clickedLinks[0].href).toContain('blob:mock-url');
  });
});

describe('exportToCSV', () => {
  const columns: Column[] = [
    { key: 'name', header: 'Name' },
    { key: 'age', header: 'Age' },
  ];

  it('generates CSV with headers and data', () => {
    const data = [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
    ];

    exportToCSV(data, 'test', columns);

    expect(mockCreateObjectURL).toHaveBeenCalledTimes(1);
    expect(clickedLinks).toHaveLength(1);
    expect(clickedLinks[0].download).toBe('test.csv');
  });

  it('adds .csv extension if missing', () => {
    exportToCSV([{ name: 'Test', age: 1 }], 'report', columns);
    expect(clickedLinks[0].download).toBe('report.csv');
  });

  it('keeps .csv extension if present', () => {
    exportToCSV([{ name: 'Test', age: 1 }], 'report.csv', columns);
    expect(clickedLinks[0].download).toBe('report.csv');
  });

  it('does nothing for empty data', () => {
    exportToCSV([], 'empty', columns);
    expect(clickedLinks).toHaveLength(0);
  });

  it('does nothing for null-ish data', () => {
    exportToCSV(null as unknown as Record<string, unknown>[], 'empty', columns);
    expect(clickedLinks).toHaveLength(0);
  });

  it('handles nested keys with dot notation', () => {
    const nestedColumns: Column[] = [
      { key: 'user.name', header: 'User Name' },
    ];
    const data = [{ user: { name: 'Alice' } }];

    exportToCSV(data, 'nested', nestedColumns);
    expect(clickedLinks).toHaveLength(1);
  });

  it('handles null values in data', () => {
    const data = [{ name: null, age: undefined }];
    exportToCSV(data, 'nulls', columns);
    expect(clickedLinks).toHaveLength(1);
  });

  it('handles values with commas', () => {
    const data = [{ name: 'Last, First', age: 30 }];
    exportToCSV(data, 'commas', columns);
    expect(clickedLinks).toHaveLength(1);
  });

  it('handles values with quotes', () => {
    const data = [{ name: 'He said "hello"', age: 30 }];
    exportToCSV(data, 'quotes', columns);
    expect(clickedLinks).toHaveLength(1);
  });

  it('handles values with newlines', () => {
    const data = [{ name: 'Line1\nLine2', age: 30 }];
    exportToCSV(data, 'newlines', columns);
    expect(clickedLinks).toHaveLength(1);
  });
});

describe('exportToJSON', () => {
  it('generates JSON and triggers download', () => {
    const data = [{ name: 'Alice' }, { name: 'Bob' }];
    exportToJSON(data, 'test');

    expect(clickedLinks).toHaveLength(1);
    expect(clickedLinks[0].download).toBe('test.json');
  });

  it('adds .json extension if missing', () => {
    exportToJSON([{ id: 1 }], 'data');
    expect(clickedLinks[0].download).toBe('data.json');
  });

  it('keeps .json extension if present', () => {
    exportToJSON([{ id: 1 }], 'data.json');
    expect(clickedLinks[0].download).toBe('data.json');
  });

  it('does nothing for empty array', () => {
    exportToJSON([], 'empty');
    expect(clickedLinks).toHaveLength(0);
  });

  it('does nothing for null-ish data', () => {
    exportToJSON(null as unknown as unknown[], 'empty');
    expect(clickedLinks).toHaveLength(0);
  });
});
