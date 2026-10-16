import React from 'react';
import { type Customer } from '../api';
import { 
  Bot, 
  MessageSquare, 
  ShieldAlert, 
  BarChart3, 
  ChevronDown
} from 'lucide-react';

interface NavbarProps {
  currentView: 'customer' | 'agent' | 'analytics';
  setCurrentView: (view: 'customer' | 'agent' | 'analytics') => void;
  customers: Customer[];
  selectedCustomer: Customer | null;
  setSelectedCustomer: (customer: Customer) => void;
  pendingApprovalsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  setCurrentView,
  customers,
  selectedCustomer,
  setSelectedCustomer,
  pendingApprovalsCount,
}) => {
  return (
    <header style={{
      borderBottom: '1px solid var(--ks-border-subtle)',
      background: 'var(--ks-surface-1)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '0.65rem 1.75rem',
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--ks-surface-2)',
            border: '1px solid var(--ks-border-strong)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Bot size={18} color="var(--ks-text-1)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontSize: '1.05rem',
                fontWeight: 700,
                color: 'var(--ks-text-1)',
                letterSpacing: '-0.02em',
              }}>
                SupportFlow
              </span>
              <span style={{
                fontSize: '0.72rem',
                color: 'var(--ks-text-4)',
                fontFamily: 'var(--font-mono)',
              }}>
                v1.0
              </span>
            </div>
          </div>
        </div>

        {/* View Switcher: Impeccable Instrument Strip */}
        <nav className="ks-instrument-strip">
          <button
            onClick={() => setCurrentView('customer')}
            className={`ks-instrument-key ${currentView === 'customer' ? 'is-active' : ''}`}
          >
            <MessageSquare size={15} />
            <span>Customer Portal</span>
          </button>

          <button
            onClick={() => setCurrentView('agent')}
            className={`ks-instrument-key ${currentView === 'agent' ? 'is-active' : ''}`}
          >
            <ShieldAlert size={15} />
            <span>Operations & Agent Desk</span>
            {pendingApprovalsCount > 0 && (
              <span style={{
                background: 'var(--ks-rose)',
                color: '#fff',
                fontSize: '0.65rem',
                fontWeight: 700,
                padding: '1px 5px',
                borderRadius: 'var(--radius-xs)',
                marginLeft: '2px',
              }}>
                {pendingApprovalsCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setCurrentView('analytics')}
            className={`ks-instrument-key ${currentView === 'analytics' ? 'is-active' : ''}`}
          >
            <BarChart3 size={15} />
            <span>Analytics</span>
          </button>
        </nav>

        {/* Right Persona & Status Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {currentView === 'customer' && customers.length > 0 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--ks-surface-sunken)',
              border: '1px solid var(--ks-border-subtle)',
              padding: '4px 8px',
              borderRadius: 'var(--radius-sm)',
            }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--ks-text-3)' }}>Customer:</span>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <select
                  value={selectedCustomer?.id || ''}
                  onChange={(e) => {
                    const cust = customers.find(c => c.id === Number(e.target.value));
                    if (cust) setSelectedCustomer(cust);
                  }}
                  style={{
                    background: 'transparent',
                    color: 'var(--ks-text-1)',
                    border: 'none',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    outline: 'none',
                    cursor: 'pointer',
                    paddingRight: '16px',
                    appearance: 'none',
                  }}
                >
                  {customers.map((c) => (
                    <option key={c.id} value={c.id} style={{ background: '#11141d', color: '#f8fafc' }}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <ChevronDown size={12} color="var(--ks-text-3)" style={{ position: 'absolute', right: 0, pointerEvents: 'none' }} />
              </div>
            </div>
          )}

          {currentView === 'agent' && (
            <div style={{
              fontSize: '0.78rem',
              color: 'var(--ks-text-3)',
              background: 'var(--ks-surface-sunken)',
              border: '1px solid var(--ks-border-subtle)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
            }}>
              Agent: <strong style={{ color: 'var(--ks-text-1)' }}>Sarah Johnson</strong>
            </div>
          )}

          {/* Backend Status indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.72rem',
            color: 'var(--ks-text-3)',
            fontFamily: 'var(--font-mono)',
          }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: 'var(--ks-emerald)',
              display: 'inline-block',
            }} />
            <span>:8001</span>
          </div>
        </div>
      </div>
    </header>
  );
};
