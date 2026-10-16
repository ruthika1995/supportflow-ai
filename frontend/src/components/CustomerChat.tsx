import React, { useState, useEffect, useRef } from 'react';
import { type Customer, type Order, aiApi, customersApi } from '../api';
import { 
  Send, 
  Bot, 
  Package, 
  ChevronRight, 
  RotateCcw, 
  Wrench, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface CustomerChatProps {
  customer: Customer;
  onTicketCreated?: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'customer' | 'ai_agent' | 'human_agent';
  text: string;
  timestamp: string;
  toolCalls?: Array<{
    tool: string;
    args: Record<string, unknown>;
    result: Record<string, unknown>;
  }>;
  requiresApproval?: boolean;
}

export const CustomerChat: React.FC<CustomerChatProps> = ({ customer, onTicketCreated }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>(undefined);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load customer orders
  useEffect(() => {
    if (!customer) return;
    setLoadingOrders(true);
    customersApi.getOrders(customer.id)
      .then(data => setOrders(data))
      .catch(err => console.error('Failed to load orders', err))
      .finally(() => setLoadingOrders(false));

    setMessages([
      {
        id: 'welcome',
        sender: 'ai_agent',
        text: `Hello ${customer.name}. How can I assist you with your orders or policies today?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
    ]);
    setConversationId(undefined);
  }, [customer]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const toggleToolExpand = (msgId: string, idx: number) => {
    const key = `${msgId}-${idx}`;
    setExpandedTools(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSendMessage = async (textToSend?: string) => {
    const msg = (textToSend || inputText).trim();
    if (!msg || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'customer',
      text: msg,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const res = await aiApi.chat(msg, customer.id, conversationId);
      if (res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai_agent',
        text: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        toolCalls: res.tool_calls_made,
        requiresApproval: res.requires_approval,
      };

      setMessages(prev => [...prev, aiMsg]);
      if (onTicketCreated) onTicketCreated();

      customersApi.getOrders(customer.id).then(setOrders).catch(() => {});
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'ai_agent',
          text: "I encountered an error communicating with the server. Please try again.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    { label: "Track Order #2", prompt: "Where is my order #2 and when will it arrive?" },
    { label: "Cancel Order #3", prompt: "I would like to cancel order #3 please." },
    { label: "Return Policy", prompt: "What is your 30-day return policy and how do refunds work?" },
    { label: "Warranty Rules", prompt: "What does the warranty cover for headphones?" },
    { label: "Request Human", prompt: "I am unsatisfied and want to speak with a human supervisor." },
  ];

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'delivered':
        return <span className="ks-badge ks-badge-emerald"><CheckCircle2 size={11} /> Delivered</span>;
      case 'shipped':
        return <span className="ks-badge ks-badge-cyan"><Package size={11} /> Shipped</span>;
      case 'processing':
        return <span className="ks-badge ks-badge-amber"><Clock size={11} /> Processing</span>;
      case 'cancelled':
        return <span className="ks-badge ks-badge-rose">Cancelled</span>;
      case 'refunded':
        return <span className="ks-badge ks-badge-slate">Refunded</span>;
      default:
        return <span className="ks-badge ks-badge-slate">{status}</span>;
    }
  };

  return (
    <div style={{
      maxWidth: '1440px',
      margin: '1.5rem auto',
      padding: '0 1.75rem',
      display: 'grid',
      gridTemplateColumns: '340px 1fr',
      gap: '1.5rem',
      alignItems: 'start',
    }}>
      {/* Left Column: Customer Profile & Order Inspector */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* Customer Context Card */}
        <div className="impeccable-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--ks-surface-2)',
              border: '1px solid var(--ks-border-strong)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              color: 'var(--ks-text-1)',
              fontSize: '0.95rem',
            }}>
              {customer.name.charAt(0)}
            </div>
            <div>
              <h3 style={{ fontSize: '0.95rem', margin: 0 }}>{customer.name}</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--ks-text-3)', margin: 0 }}>{customer.email}</p>
            </div>
          </div>

          <div style={{
            fontSize: '0.78rem',
            background: 'var(--ks-surface-sunken)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 12px',
            border: '1px solid var(--ks-border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}>
            <div>
              <span style={{ color: 'var(--ks-text-4)' }}>Phone: </span>
              <span style={{ color: 'var(--ks-text-2)' }}>{customer.phone || 'N/A'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--ks-text-4)' }}>Shipping: </span>
              <span style={{ color: 'var(--ks-text-2)' }}>{customer.address || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Orders Card */}
        <div className="impeccable-card" style={{ padding: '1.25rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.85rem',
          }}>
            <h4 style={{ fontSize: '0.875rem', margin: 0, color: 'var(--ks-text-1)' }}>
              Orders ({orders.length})
            </h4>
            <button 
              onClick={() => customersApi.getOrders(customer.id).then(setOrders)}
              title="Refresh Orders"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--ks-text-3)',
                cursor: 'pointer',
                padding: '4px',
              }}
            >
              <RotateCcw size={13} />
            </button>
          </div>

          {loadingOrders ? (
            <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--ks-text-4)', fontSize: '0.8rem' }}>
              Loading orders...
            </div>
          ) : orders.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--ks-text-4)', fontSize: '0.8rem' }}>
              No orders found.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
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
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.825rem', color: 'var(--ks-text-1)', fontFamily: 'var(--font-mono)' }}>
                      #{order.id}
                    </span>
                    {getStatusBadge(order.status)}
                  </div>

                  <div style={{ fontSize: '0.78rem', color: 'var(--ks-text-3)', marginBottom: '8px' }}>
                    <div>Total: <span style={{ color: 'var(--ks-text-1)', fontWeight: 600 }}>${order.total_amount.toFixed(2)}</span></div>
                    {order.tracking_number && (
                      <div style={{ marginTop: '2px', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--ks-text-4)' }}>
                        {order.tracking_number}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleSendMessage(`What is the status of my order #${order.id}?`)}
                    className="ks-btn ks-btn-secondary"
                    style={{
                      width: '100%',
                      padding: '4px 8px',
                      fontSize: '0.75rem',
                      justifyContent: 'space-between',
                    }}
                  >
                    <span>Check with AI</span>
                    <ChevronRight size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Column: Live Chat Interface */}
      <div className="impeccable-card" style={{
        display: 'flex',
        flexDirection: 'column',
        height: '760px',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '0.85rem 1.5rem',
          borderBottom: '1px solid var(--ks-border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--ks-surface-1)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--ks-text-1)' }}>
              Support Session
            </span>
            <span className="ks-badge ks-badge-emerald">Active</span>
          </div>

          {conversationId && (
            <span style={{ fontSize: '0.72rem', color: 'var(--ks-text-4)', fontFamily: 'var(--font-mono)' }}>
              conv-{conversationId}
            </span>
          )}
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}>
          {messages.map((msg) => {
            const isUser = msg.sender === 'customer';
            return (
              <div
                key={msg.id}
                className="fade-in"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isUser ? 'flex-end' : 'flex-start',
                  maxWidth: '82%',
                  alignSelf: isUser ? 'flex-end' : 'flex-start',
                }}
              >
                {/* Sender label */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  marginBottom: '4px',
                  fontSize: '0.72rem',
                  color: 'var(--ks-text-4)',
                }}>
                  <span>{isUser ? customer.name : 'SupportFlow AI'}</span>
                  <span>• {msg.timestamp}</span>
                </div>

                {/* Message Bubble */}
                <div style={{
                  padding: '12px 16px',
                  borderRadius: isUser ? '8px 8px 2px 8px' : '8px 8px 8px 2px',
                  background: isUser ? 'var(--ks-surface-3)' : 'var(--ks-surface-2)',
                  border: '1px solid',
                  borderColor: isUser ? 'var(--ks-border-strong)' : 'var(--ks-border-subtle)',
                  color: 'var(--ks-text-1)',
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}>
                  {msg.text}
                </div>

                {/* Human in the loop Alert */}
                {msg.requiresApproval && (
                  <div style={{
                    marginTop: '8px',
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    color: '#fbbf24',
                    fontSize: '0.8rem',
                  }}>
                    <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <div style={{ fontWeight: 600 }}>Supervisor Review Required</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--ks-text-3)', marginTop: '2px' }}>
                        This high-risk action was intercepted by automated guardrails and queued for supervisor authorization.
                      </div>
                    </div>
                  </div>
                )}

                {/* Tool Execution Disclosure */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div style={{
                    marginTop: '8px',
                    width: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}>
                    {msg.toolCalls.map((tc, idx) => {
                      const expandedKey = `${msg.id}-${idx}`;
                      const isExpanded = !!expandedTools[expandedKey];
                      return (
                        <div
                          key={idx}
                          style={{
                            background: 'var(--ks-surface-sunken)',
                            border: '1px solid var(--ks-border-subtle)',
                            borderRadius: 'var(--radius-sm)',
                            overflow: 'hidden',
                            fontSize: '0.75rem',
                          }}
                        >
                          <div
                            onClick={() => toggleToolExpand(msg.id, idx)}
                            style={{
                              padding: '6px 10px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              cursor: 'pointer',
                              userSelect: 'none',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <Wrench size={12} color="var(--ks-cyan)" />
                              <span style={{ color: 'var(--ks-text-2)', fontFamily: 'var(--font-mono)' }}>
                                {tc.tool}
                              </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--ks-text-4)' }}>
                              <span>{isExpanded ? 'Hide' : 'Inspect'}</span>
                              {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                            </div>
                          </div>

                          {isExpanded && (
                            <div style={{
                              padding: '8px 10px',
                              borderTop: '1px solid var(--ks-border-subtle)',
                              fontFamily: 'var(--font-mono)',
                              fontSize: '0.72rem',
                              background: '#090a0f',
                            }}>
                              <div style={{ marginBottom: '4px', color: 'var(--ks-text-3)' }}>
                                <span style={{ color: 'var(--ks-text-4)' }}>args: </span>{JSON.stringify(tc.args)}
                              </div>
                              <div style={{ color: 'var(--ks-emerald)' }}>
                                <span style={{ color: 'var(--ks-text-4)' }}>result: </span>{JSON.stringify(tc.result)}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}

          {isLoading && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--ks-surface-2)',
              border: '1px solid var(--ks-border-subtle)',
              alignSelf: 'flex-start',
              color: 'var(--ks-text-3)',
              fontSize: '0.825rem',
            }}>
              <Bot size={15} color="var(--ks-cyan)" />
              <span>Reasoning & executing tools...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        <div style={{
          padding: '8px 1.5rem',
          display: 'flex',
          gap: '6px',
          overflowX: 'auto',
          background: 'var(--ks-surface-sunken)',
          borderTop: '1px solid var(--ks-border-subtle)',
        }}>
          {quickPrompts.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(p.prompt)}
              disabled={isLoading}
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.75rem',
                fontWeight: 500,
                color: 'var(--ks-text-3)',
                background: 'var(--ks-surface-2)',
                border: '1px solid var(--ks-border-subtle)',
                borderRadius: 'var(--radius-xs)',
                padding: '4px 10px',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div style={{
          padding: '0.85rem 1.5rem',
          borderTop: '1px solid var(--ks-border-subtle)',
          background: 'var(--ks-surface-1)',
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
        }}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder={`Message SupportFlow as ${customer.name}...`}
            disabled={isLoading}
            style={{
              flex: 1,
              background: 'var(--ks-surface-sunken)',
              border: '1px solid var(--ks-border-strong)',
              color: 'var(--ks-text-1)',
              padding: '8px 12px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
              outline: 'none',
              fontFamily: 'var(--font-sans)',
            }}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={isLoading || !inputText.trim()}
            className="ks-btn ks-btn-primary"
            style={{
              padding: '8px 16px',
              opacity: (isLoading || !inputText.trim()) ? 0.5 : 1,
            }}
          >
            <Send size={14} />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};
