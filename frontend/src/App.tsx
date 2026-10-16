import { useState, useEffect } from 'react';
import { type Customer, customersApi, ticketsApi } from './api';
import { Navbar } from './components/Navbar';
import { CustomerChat } from './components/CustomerChat';
import { AgentDesk } from './components/AgentDesk';
import { AnalyticsView } from './components/AnalyticsView';

export function App() {
  const [currentView, setCurrentView] = useState<'customer' | 'agent' | 'analytics'>('customer');
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);

  const fetchInitialData = async () => {
    try {
      const custList = await customersApi.list();
      setCustomers(custList);
      if (custList.length > 0 && !selectedCustomer) {
        setSelectedCustomer(custList[0]); // Defaults to Ruthi
      }

      const pending = await ticketsApi.listPendingApprovals();
      setPendingApprovalsCount(pending.length);
    } catch (err) {
      console.error('Failed to load initial customers or approvals:', err);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleDataRefresh = async () => {
    try {
      const pending = await ticketsApi.listPendingApprovals();
      setPendingApprovalsCount(pending.length);
    } catch (err) {
      console.error('Failed to update pending count', err);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        currentView={currentView}
        setCurrentView={setCurrentView}
        customers={customers}
        selectedCustomer={selectedCustomer}
        setSelectedCustomer={setSelectedCustomer}
        pendingApprovalsCount={pendingApprovalsCount}
      />

      <main style={{ flex: 1, paddingBottom: '2rem' }}>
        {currentView === 'customer' && selectedCustomer && (
          <CustomerChat 
            customer={selectedCustomer} 
            onTicketCreated={handleDataRefresh}
          />
        )}

        {currentView === 'agent' && (
          <AgentDesk onRefreshData={handleDataRefresh} />
        )}

        {currentView === 'analytics' && (
          <AnalyticsView />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--ks-border-subtle)',
        padding: '1.25rem 1.75rem',
        fontSize: '0.78rem',
        color: 'var(--ks-text-3)',
        background: 'var(--ks-surface-1)',
      }}>
        <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <strong style={{ color: 'var(--ks-text-1)' }}>SupportFlow</strong> • Agentic Operations & Human Authorization Guardrails
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--ks-text-4)' }}>
            FastAPI • SQLite • React 19 • ReAct Orchestrator
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
