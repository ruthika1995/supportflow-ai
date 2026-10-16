import React, { useState, useEffect } from 'react';
import { 
  type Ticket, 
  type ApprovalRequest, 
  type Order, 
  type Product, 
  type KnowledgeDoc, 
  ticketsApi, 
  ordersApi, 
  productsApi, 
  knowledgeApi 
} from '../api';
import { 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  Search, 
  RotateCcw, 
  Package, 
  BookOpen, 
  Send, 
  Inbox
} from 'lucide-react';

interface AgentDeskProps {
  onRefreshData?: () => void;
}

export const AgentDesk: React.FC<AgentDeskProps> = ({ onRefreshData }) => {
  const [activeTab, setActiveTab] = useState<'tickets' | 'approvals' | 'orders' | 'knowledge'>('tickets');
  
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [knowledgeDocs, setKnowledgeDocs] = useState<KnowledgeDoc[]>([]);

  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [ticketFilterStatus, setTicketFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [agentReplyText, setAgentReplyText] = useState('');
  const [reviewNotes, setReviewNotes] = useState('');

  const [newDocTitle, setNewDocTitle] = useState('');
  const [newDocFilename, setNewDocFilename] = useState('');
  const [newDocCategory, setNewDocCategory] = useState('policy');
  const [newDocContent, setNewDocContent] = useState('');

  const [loading, setLoading] = useState(false);

  const refreshAll = async () => {
    setLoading(true);
    try {
      const [tList, aList, oList, pList, kList] = await Promise.all([
        ticketsApi.list(),
        ticketsApi.listPendingApprovals(),
        ordersApi.list(),
        productsApi.list(),
        knowledgeApi.list(),
      ]);
      setTickets(tList);
      setApprovals(aList);
      setOrders(oList);
      setProducts(pList);
      setKnowledgeDocs(kList);

      if (selectedTicket) {
        const updated = tList.find(t => t.id === selectedTicket.id);
        if (updated) setSelectedTicket(updated);
      }
      if (onRefreshData) onRefreshData();
    } catch (err) {
      console.error('Error fetching ops desk data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
  }, []);

  const filteredTickets = tickets.filter(t => {
    const matchesStatus = ticketFilterStatus === 'all' || t.status === ticketFilterStatus;
    const matchesSearch = !searchQuery || 
      t.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.id.toString().includes(searchQuery);
    return matchesStatus && matchesSearch;
  });

  const handleReviewApproval = async (id: number, status: 'approved' | 'rejected') => {
    try {
      await ticketsApi.reviewApproval(id, status, reviewNotes || `Reviewed by Sarah Johnson`);
      setReviewNotes('');
      await refreshAll();
    } catch (err) {
      alert('Error updating approval request: ' + err);
    }
  };

  const handleSendAgentReply = async () => {
    if (!selectedTicket || !agentReplyText.trim()) return;
    try {
      await ticketsApi.addMessage(selectedTicket.id, 'human_agent', agentReplyText.trim(), 'Sarah Johnson');
      setAgentReplyText('');
      await refreshAll();
    } catch (err) {
      alert('Failed to send agent reply: ' + err);
    }
  };

  const handleUpdateTicketStatus = async (status: string) => {
    if (!selectedTicket) return;
    try {
      await ticketsApi.update(selectedTicket.id, { status });
      await refreshAll();
    } catch (err) {
      alert('Failed to update ticket: ' + err);
    }
  };

  const handleEscalateTicket = async () => {
    if (!selectedTicket) return;
    try {
      await ticketsApi.escalate(selectedTicket.id);
      await refreshAll();
    } catch (err) {
      alert('Failed to escalate ticket: ' + err);
    }
  };

  const handleAddKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDocFilename || !newDocContent) return;
    try {
      await knowledgeApi.addText(newDocFilename, newDocContent, newDocTitle, newDocCategory);
      setNewDocFilename('');
      setNewDocTitle('');
      setNewDocContent('');
      await refreshAll();
    } catch (err) {
      alert('Failed to add knowledge document: ' + err);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return <span className="ks-badge ks-badge-rose">Urgent</span>;
      case 'high':
        return <span className="ks-badge ks-badge-amber">High</span>;
      default:
        return <span className="ks-badge ks-badge-slate">{priority}</span>;
    }
  };

  const getTicketStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return <span className="ks-badge ks-badge-cyan">Open</span>;
      case 'escalated':
        return <span className="ks-badge ks-badge-rose"><AlertTriangle size={10} /> Escalated</span>;
      case 'pending_approval':
        return <span className="ks-badge ks-badge-amber"><Clock size={10} /> Review Needed</span>;
      case 'resolved':
        return <span className="ks-badge ks-badge-emerald"><CheckCircle2 size={10} /> Resolved</span>;
      default:
        return <span className="ks-badge ks-badge-slate">{status}</span>;
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '1.5rem auto', padding: '0 1.75rem' }}>
      {/* Top Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.25rem',
      }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', margin: 0, fontWeight: 700 }}>
            Operations & Support Desk
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--ks-text-3)', marginTop: '2px', margin: 0 }}>
            Supervise AI agent actions, authorize high-risk transactions, and inspect inventory.
          </p>
        </div>

        <button 
          onClick={refreshAll} 
          disabled={loading}
          className="ks-btn ks-btn-secondary"
          style={{ fontSize: '0.78rem', padding: '5px 12px' }}
        >
          <RotateCcw size={13} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Segmented Instrument Navigation */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div className="ks-instrument-strip">
          <button
            onClick={() => setActiveTab('tickets')}
            className={`ks-instrument-key ${activeTab === 'tickets' ? 'is-active' : ''}`}
          >
            <Inbox size={14} />
            <span>Tickets ({tickets.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('approvals')}
            className={`ks-instrument-key ${activeTab === 'approvals' ? 'is-active' : ''}`}
          >
            <ShieldAlert size={14} />
            <span>Human Approvals ({approvals.length})</span>
            {approvals.length > 0 && (
              <span style={{
                background: 'var(--ks-rose)',
                color: '#fff',
                fontSize: '0.65rem',
                fontWeight: 700,
                padding: '0 5px',
                borderRadius: 'var(--radius-xs)',
              }}>
                {approvals.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('orders')}
            className={`ks-instrument-key ${activeTab === 'orders' ? 'is-active' : ''}`}
          >
            <Package size={14} />
            <span>Orders & Products</span>
          </button>

          <button
            onClick={() => setActiveTab('knowledge')}
            className={`ks-instrument-key ${activeTab === 'knowledge' ? 'is-active' : ''}`}
          >
            <BookOpen size={14} />
            <span>Knowledge Base (RAG)</span>
          </button>
        </div>
      </div>

      {/* TAB 1: TICKETS QUEUE */}
      {activeTab === 'tickets' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: selectedTicket ? '400px 1fr' : '1fr',
          gap: '1.25rem',
        }}>
          {/* List */}
          <div className="impeccable-card" style={{ padding: '1rem', height: '720px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '10px' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--ks-surface-sunken)',
                border: '1px solid var(--ks-border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 10px',
              }}>
                <Search size={14} color="var(--ks-text-4)" />
                <input
                  type="text"
                  placeholder="Filter tickets by subject or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--ks-text-1)',
                    fontSize: '0.8rem',
                    outline: 'none',
                    width: '100%',
                    fontFamily: 'var(--font-sans)',
                  }}
                />
              </div>

              {/* Status Filter Keys */}
              <div style={{ display: 'flex', gap: '4px', overflowX: 'auto' }}>
                {['all', 'open', 'pending_approval', 'escalated', 'resolved'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setTicketFilterStatus(st)}
                    style={{
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid',
                      borderColor: ticketFilterStatus === st ? 'var(--ks-border-strong)' : 'transparent',
                      background: ticketFilterStatus === st ? 'var(--ks-surface-3)' : 'transparent',
                      color: ticketFilterStatus === st ? 'var(--ks-text-1)' : 'var(--ks-text-3)',
                      fontSize: '0.72rem',
                      fontWeight: 500,
                      cursor: 'pointer',
                      textTransform: 'capitalize',
                    }}
                  >
                    {st.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            {/* List Items */}
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {filteredTickets.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--ks-text-4)', fontSize: '0.8rem' }}>
                  No tickets found.
                </div>
              ) : (
                filteredTickets.map(ticket => {
                  const isSelected = selectedTicket?.id === ticket.id;
                  return (
                    <div
                      key={ticket.id}
                      onClick={() => setSelectedTicket(ticket)}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-sm)',
                        background: isSelected ? 'var(--ks-surface-3)' : 'var(--ks-surface-sunken)',
                        border: '1px solid',
                        borderColor: isSelected ? 'var(--ks-border-strong)' : 'var(--ks-border-subtle)',
                        cursor: 'pointer',
                        transition: 'all var(--transition-fast)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.825rem', color: 'var(--ks-text-1)', fontFamily: 'var(--font-mono)' }}>
                          #{ticket.id}
                        </span>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {getPriorityBadge(ticket.priority)}
                          {getTicketStatusBadge(ticket.status)}
                        </div>
                      </div>

                      <div style={{
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        color: 'var(--ks-text-2)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        marginBottom: '4px',
                      }}>
                        {ticket.subject}
                      </div>

                      <div style={{ fontSize: '0.72rem', color: 'var(--ks-text-4)' }}>
                        Cust #{ticket.customer_id} • {ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : 'Recent'}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Ticket Inspector */}
          {selectedTicket && (
            <div className="impeccable-card" style={{
              padding: '1.25rem',
              height: '720px',
              display: 'flex',
              flexDirection: 'column',
            }}>
              {/* Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                borderBottom: '1px solid var(--ks-border-subtle)',
                paddingBottom: '0.85rem',
                marginBottom: '1rem',
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ fontSize: '1rem', margin: 0 }}>Ticket #{selectedTicket.id}: {selectedTicket.subject}</h3>
                    {getTicketStatusBadge(selectedTicket.status)}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--ks-text-4)', marginTop: '2px' }}>
                    Customer #{selectedTicket.customer_id} • Priority: {selectedTicket.priority}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '6px' }}>
                  {selectedTicket.status !== 'resolved' && (
                    <button
                      onClick={() => handleUpdateTicketStatus('resolved')}
                      className="ks-btn ks-btn-success"
                      style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                    >
                      <CheckCircle2 size={12} />
                      <span>Resolve</span>
                    </button>
                  )}

                  {selectedTicket.status !== 'escalated' && (
                    <button
                      onClick={handleEscalateTicket}
                      className="ks-btn ks-btn-danger"
                      style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                    >
                      <AlertTriangle size={12} />
                      <span>Escalate</span>
                    </button>
                  )}

                  <button
                    onClick={() => setSelectedTicket(null)}
                    className="ks-btn ks-btn-secondary"
                    style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                  >
                    Close
                  </button>
                </div>
              </div>

              {/* Message Transcript */}
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedTicket.conversations && selectedTicket.conversations.length > 0 ? (
                  selectedTicket.conversations.flatMap(c => c.messages || []).map((msg, idx) => {
                    const isAi = msg.sender_type === 'ai_agent';
                    const isHuman = msg.sender_type === 'human_agent';

                    return (
                      <div
                        key={idx}
                        style={{
                          padding: '10px 12px',
                          borderRadius: 'var(--radius-sm)',
                          background: isHuman 
                            ? 'rgba(16, 185, 129, 0.08)' 
                            : isAi 
                              ? 'var(--ks-surface-2)' 
                              : 'var(--ks-surface-sunken)',
                          border: '1px solid var(--ks-border-subtle)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 600, color: isHuman ? '#34d399' : isAi ? 'var(--ks-cyan)' : 'var(--ks-text-2)' }}>
                            {isHuman ? msg.sender_name || 'Staff' : isAi ? 'AI Agent' : 'Customer'}
                          </span>
                          <span style={{ fontSize: '0.7rem', color: 'var(--ks-text-4)', fontFamily: 'var(--font-mono)' }}>
                            {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.825rem', color: 'var(--ks-text-1)', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                          {msg.content}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--ks-text-4)' }}>
                    No messages.
                  </div>
                )}
              </div>

              {/* Agent Reply Bar */}
              <div style={{
                marginTop: '0.85rem',
                paddingTop: '0.85rem',
                borderTop: '1px solid var(--ks-border-subtle)',
                display: 'flex',
                gap: '8px',
              }}>
                <input
                  type="text"
                  placeholder="Send staff response to customer..."
                  value={agentReplyText}
                  onChange={(e) => setAgentReplyText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendAgentReply()}
                  style={{
                    flex: 1,
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-strong)',
                    color: 'var(--ks-text-1)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.825rem',
                    outline: 'none',
                    fontFamily: 'var(--font-sans)',
                  }}
                />
                <button
                  onClick={handleSendAgentReply}
                  disabled={!agentReplyText.trim()}
                  className="ks-btn ks-btn-primary"
                  style={{ padding: '6px 12px' }}
                >
                  <Send size={13} />
                  <span>Reply</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: APPROVAL QUEUE */}
      {activeTab === 'approvals' && (
        <div className="impeccable-card" style={{ padding: '1.25rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', margin: 0, fontWeight: 700 }}>
              Human Authorization Gate
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--ks-text-3)', marginTop: '2px', margin: 0 }}>
              Autonomous guardrails paused the following actions. Authorize or deny below.
            </p>
          </div>

          {approvals.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '3rem 1rem',
              color: 'var(--ks-text-4)',
              background: 'var(--ks-surface-sunken)',
              borderRadius: 'var(--radius-sm)',
              border: '1px dashed var(--ks-border-subtle)',
            }}>
              <CheckCircle2 size={28} color="var(--ks-emerald)" style={{ marginBottom: '8px' }} />
              <div style={{ color: 'var(--ks-text-1)', fontSize: '0.9rem', fontWeight: 600 }}>All Caught Up</div>
              <div style={{ fontSize: '0.78rem', marginTop: '2px' }}>No actions currently require supervisor authorization.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {approvals.map(req => (
                <div
                  key={req.id}
                  style={{
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-strong)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '12px 14px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="ks-badge ks-badge-amber">
                        {req.action_type}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--ks-text-4)', fontFamily: 'var(--font-mono)' }}>
                        req-{req.id} • ticket-{req.ticket_id}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--ks-text-4)', fontFamily: 'var(--font-mono)' }}>
                      {req.created_at ? new Date(req.created_at).toLocaleTimeString() : 'Recent'}
                    </span>
                  </div>

                  <div style={{
                    background: '#0a0c10',
                    borderRadius: 'var(--radius-xs)',
                    padding: '8px 10px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    color: 'var(--ks-text-2)',
                    marginBottom: '10px',
                    border: '1px solid var(--ks-border-subtle)',
                  }}>
                    {req.action_payload}
                  </div>

                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="text"
                      placeholder="Optional notes..."
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      style={{
                        flex: 1,
                        background: 'var(--ks-surface-2)',
                        border: '1px solid var(--ks-border-subtle)',
                        color: 'var(--ks-text-1)',
                        padding: '6px 10px',
                        borderRadius: 'var(--radius-xs)',
                        fontSize: '0.78rem',
                        fontFamily: 'var(--font-sans)',
                      }}
                    />
                    <button
                      onClick={() => handleReviewApproval(req.id, 'approved')}
                      className="ks-btn ks-btn-success"
                      style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                    >
                      <CheckCircle2 size={13} />
                      <span>Approve & Execute</span>
                    </button>
                    <button
                      onClick={() => handleReviewApproval(req.id, 'rejected')}
                      className="ks-btn ks-btn-danger"
                      style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                    >
                      <XCircle size={13} />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: ORDERS & INVENTORY */}
      {activeTab === 'orders' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.25rem' }}>
          {/* Orders */}
          <div className="impeccable-card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.85rem 0', fontWeight: 700 }}>
              Customer Orders ({orders.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '640px', overflowY: 'auto' }}>
              {orders.map(order => (
                <div
                  key={order.id}
                  style={{
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.825rem', fontFamily: 'var(--font-mono)' }}>
                      #{order.id} (Cust #{order.customer_id})
                    </span>
                    <span className="ks-badge ks-badge-cyan">{order.status}</span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--ks-text-3)' }}>
                    Total: <strong style={{ color: 'var(--ks-text-1)' }}>${order.total_amount.toFixed(2)}</strong>
                    {order.tracking_number && (
                      <span style={{ display: 'block', color: 'var(--ks-text-4)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                        {order.tracking_number}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Products */}
          <div className="impeccable-card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.85rem 0', fontWeight: 700 }}>
              Product Inventory ({products.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '640px', overflowY: 'auto' }}>
              {products.map(p => (
                <div
                  key={p.id}
                  style={{
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.825rem', color: 'var(--ks-text-1)' }}>{p.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--ks-text-4)' }}>
                      ${p.price.toFixed(2)}
                    </div>
                  </div>
                  <span className={`ks-badge ${p.inventory < 20 ? 'ks-badge-rose' : 'ks-badge-emerald'}`}>
                    {p.inventory} in stock
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: KNOWLEDGE BASE */}
      {activeTab === 'knowledge' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.25rem' }}>
          {/* Document list */}
          <div className="impeccable-card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.85rem 0', fontWeight: 700 }}>
              Indexed RAG Documents ({knowledgeDocs.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '640px', overflowY: 'auto' }}>
              {knowledgeDocs.map(doc => (
                <div
                  key={doc.id}
                  style={{
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.825rem', color: 'var(--ks-text-1)' }}>
                      {doc.title || doc.filename}
                    </span>
                    <span className="ks-badge ks-badge-slate">{doc.category || 'policy'}</span>
                  </div>
                  <p style={{
                    fontSize: '0.75rem',
                    color: 'var(--ks-text-3)',
                    lineHeight: 1.45,
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    margin: 0,
                  }}>
                    {doc.content}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Add Form */}
          <div className="impeccable-card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '0.95rem', margin: '0 0 0.85rem 0', fontWeight: 700 }}>
              Ingest Document to RAG
            </h3>
            <form onSubmit={handleAddKnowledge} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--ks-text-3)', display: 'block', marginBottom: '3px' }}>
                  Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Return Extensions"
                  value={newDocTitle}
                  onChange={(e) => setNewDocTitle(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-strong)',
                    color: 'var(--ks-text-1)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '0.8rem',
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--ks-text-3)', display: 'block', marginBottom: '3px' }}>
                  Filename
                </label>
                <input
                  type="text"
                  placeholder="e.g. extension_rules.md"
                  required
                  value={newDocFilename}
                  onChange={(e) => setNewDocFilename(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-strong)',
                    color: 'var(--ks-text-1)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '0.8rem',
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--ks-text-3)', display: 'block', marginBottom: '3px' }}>
                  Category
                </label>
                <select
                  value={newDocCategory}
                  onChange={(e) => setNewDocCategory(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-strong)',
                    color: 'var(--ks-text-1)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '0.8rem',
                  }}
                >
                  <option value="policy">Policy</option>
                  <option value="faq">FAQ</option>
                  <option value="terms">Terms</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--ks-text-3)', display: 'block', marginBottom: '3px' }}>
                  Content
                </label>
                <textarea
                  rows={5}
                  placeholder="Paste policy text..."
                  required
                  value={newDocContent}
                  onChange={(e) => setNewDocContent(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--ks-surface-sunken)',
                    border: '1px solid var(--ks-border-strong)',
                    color: 'var(--ks-text-1)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '0.8rem',
                    fontFamily: 'var(--font-sans)',
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={!newDocFilename || !newDocContent}
                className="ks-btn ks-btn-primary"
                style={{ padding: '8px', marginTop: '4px' }}
              >
                Index in RAG
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
