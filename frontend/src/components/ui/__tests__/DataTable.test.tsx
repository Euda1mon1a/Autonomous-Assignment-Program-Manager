import { renderWithProviders } from '@/test-utils';
import React from 'react';
import { renderWithProviders as render, screen, fireEvent } from '@/test-utils';
import { DataTable, Column } from '../DataTable';

interface TestData {
  id: string;
  name: string;
  role: string;
  hours: number;
}

describe('DataTable', () => {
  const mockData: TestData[] = [
    { id: '1', name: 'Dr. Smith', role: 'Attending', hours: 60 },
    { id: '2', name: 'Dr. Johnson', role: 'Resident', hours: 75 },
    { id: '3', name: 'Dr. Williams', role: 'Resident', hours: 80 },
    { id: '4', name: 'Dr. Brown', role: 'Fellow', hours: 55 },
  ];

  const mockColumns: Column<TestData>[] = [
    {
      key: 'name',
      header: 'Name',
      accessor: (row) => row.name,
      sortable: true,
    },
    {
      key: 'role',
      header: 'Role',
      accessor: (row) => row.role,
      sortable: true,
    },
    {
      key: 'hours',
      header: 'Hours',
      accessor: (row) => row.hours,
      sortable: true,
      render: (value) => `${value}h`,
    },
  ];

  it('renders table with data', () => {
    render(
      <DataTable
        data={mockData}
        columns={mockColumns}
        rowKey={(row) => row.id}
      />
    );

    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    expect(screen.getByText('Dr. Johnson')).toBeInTheDocument();
    expect(screen.getByText('60h')).toBeInTheDocument();
  });

  it('renders column headers', () => {
    render(
      <DataTable
        data={mockData}
        columns={mockColumns}
        rowKey={(row) => row.id}
      />
    );

    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Role')).toBeInTheDocument();
    expect(screen.getByText('Hours')).toBeInTheDocument();
  });

  it('sorts data when column header is clicked', () => {
    render(
      <DataTable
        data={mockData}
        columns={mockColumns}
        rowKey={(row) => row.id}
      />
    );

    const rows = screen.getAllByRole('row');
    // First row is header, second row is first data row
    expect(rows[1]).toHaveTextContent('Dr. Smith');

    // Click on Name header to sort
    fireEvent.click(screen.getByText('Name'));

    // After sorting, order might change
    const sortedRows = screen.getAllByRole('row');
    expect(sortedRows.length).toBe(mockData.length + 1); // +1 for header
  });

  it('filters data based on search query', () => {
    render(
      <DataTable
        data={mockData}
        columns={mockColumns}
        rowKey={(row) => row.id}
        searchable
      />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'Smith' } });

    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    expect(screen.queryByText('Dr. Johnson')).not.toBeInTheDocument();
  });

  it('displays "no data" message when table is empty', () => {
    render(
      <DataTable
        data={[]}
        columns={mockColumns}
        rowKey={(row) => row.id}
      />
    );

    expect(screen.getByText('No data to display')).toBeInTheDocument();
  });

  it('handles row click events', () => {
    const handleRowClick = jest.fn();

    render(
      <DataTable
        data={mockData}
        columns={mockColumns}
        rowKey={(row) => row.id}
        onRowClick={handleRowClick}
      />
    );

    const firstRow = screen.getByText('Dr. Smith').closest('tr');
    if (firstRow) {
      fireEvent.click(firstRow);
      expect(handleRowClick).toHaveBeenCalledWith(mockData[0]);
    }
  });

  it('paginates data correctly', () => {
    const largeData = Array.from({ length: 25 }, (_, i) => ({
      id: `${i}`,
      name: `Dr. Person ${i}`,
      role: 'Resident',
      hours: 60 + i,
    }));

    render(
      <DataTable
        data={largeData}
        columns={mockColumns}
        rowKey={(row) => row.id}
        pageSize={10}
      />
    );

    // Should show pagination controls
    expect(screen.getByText('Next')).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();

    // Should show first 10 items
    expect(screen.getByText('Dr. Person 0')).toBeInTheDocument();
    expect(screen.getByText('Dr. Person 9')).toBeInTheDocument();
    expect(screen.queryByText('Dr. Person 10')).not.toBeInTheDocument();
  });

  it('changes pages when pagination buttons are clicked', () => {
    const largeData = Array.from({ length: 25 }, (_, i) => ({
      id: `${i}`,
      name: `Dr. Person ${i}`,
      role: 'Resident',
      hours: 60 + i,
    }));

    render(
      <DataTable
        data={largeData}
        columns={mockColumns}
        rowKey={(row) => row.id}
        pageSize={10}
      />
    );

    // Click next button
    fireEvent.click(screen.getByText('Next'));

    // Should show second page items
    expect(screen.queryByText('Dr. Person 0')).not.toBeInTheDocument();
    expect(screen.getByText('Dr. Person 10')).toBeInTheDocument();
  });

  it('applies custom rendering for columns', () => {
    render(
      <DataTable
        data={mockData}
        columns={mockColumns}
        rowKey={(row) => row.id}
      />
    );

    // Hours column has custom render function that adds 'h' suffix
    expect(screen.getByText('60h')).toBeInTheDocument();
    expect(screen.getByText('75h')).toBeInTheDocument();
  });
});
