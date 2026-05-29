import { useState, useEffect } from 'react';
import axios from 'axios';

const API = 'http://127.0.0.1:8000/api';

const COLORS = {
  PENDING: '#f59e0b',
  APPROVED: '#10b981',
  FLAGGED: '#ef4444',
  REJECTED: '#6b7280',
};

export default function App() {
  const [tab, setTab] = useState('dashboard');
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [newClientName, setNewClientName] = useState('');
  const [uploadSource, setUploadSource] = useState('SAP');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadMsg, setUploadMsg] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API}/clients/`).then(r => setClients(r.data));
  }, []);

  useEffect(() => {
    if (!selectedClient) return;
    setLoading(true);
    axios.get(`${API}/dashboard/?client_id=${selectedClient}`)
      .then(r => { setRecords(r.data.records); setSummary(r.data.summary); })
      .finally(() => setLoading(false));
  }, [selectedClient]);

  const createClient = async () => {
    if (!newClientName.trim()) return;
    const r = await axios.post(`${API}/clients/`, { name: newClientName });
    setClients(prev => [...prev, r.data]);
    setNewClientName('');
  };

  const uploadData = async () => {
    if (!uploadFile || !selectedClient) { setUploadMsg('Select a client and file first.'); return; }
    const fd = new FormData();
    fd.append('source_type', uploadSource);
    fd.append('client_id', selectedClient);
    fd.append('file', uploadFile);
    setLoading(true);
    try {
      const r = await axios.post(`${API}/ingest/`, fd);
      setUploadMsg(`✅ Ingested ${r.data.rows_ingested} rows. Errors: ${r.data.errors}`);
      // Refresh dashboard
      const dash = await axios.get(`${API}/dashboard/?client_id=${selectedClient}`);
      setRecords(dash.data.records); setSummary(dash.data.summary);
    } catch (e) {
      setUploadMsg('❌ Upload failed: ' + (e.response?.data?.error || e.message));
    } finally { setLoading(false); }
  };

  const reviewRecord = async (id, status) => {
    const note = status === 'FLAGGED' ? prompt('Add a note (optional):') || '' : '';
    await axios.patch(`${API}/records/${id}/review/`, { status, analyst_note: note, reviewed_by: 'analyst' });
    setRecords(prev => prev.map(r => r.id === id ? { ...r, status, analyst_note: note } : r));
  };

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <h1 style={{ color: '#1e293b' }}>🌿 Breathe ESG — Emissions Ingestion Platform</h1>

      {/* Client Selector */}
      <div style={{ background: '#f8fafc', padding: 16, borderRadius: 8, marginBottom: 20, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={selectedClient} onChange={e => setSelectedClient(e.target.value)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 14 }}>
          <option value=''>— Select Client —</option>
          {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input value={newClientName} onChange={e => setNewClientName(e.target.value)}
          placeholder='New client name...'
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 14 }} />
        <button onClick={createClient}
          style={{ padding: '8px 16px', background: '#0ea5e9', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
          + Create Client
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['dashboard', 'upload', 'sample_data'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ padding: '8px 18px', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 600,
              background: tab === t ? '#1e293b' : '#e2e8f0', color: tab === t ? '#fff' : '#475569' }}>
            {t === 'dashboard' ? '📊 Dashboard' : t === 'upload' ? '⬆️ Upload' : '📄 Sample Data'}
          </button>
        ))}
      </div>

      {/* DASHBOARD TAB */}
      {tab === 'dashboard' && (
        <div>
          {summary && (
            <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
              {[
                { label: 'Total CO₂e (kg)', value: summary.total_co2e_kg.toLocaleString(), color: '#7c3aed' },
                { label: 'Scope 1', value: (summary.by_scope['1'] || 0).toFixed(1) + ' kg', color: '#ef4444' },
                { label: 'Scope 2', value: (summary.by_scope['2'] || 0).toFixed(1) + ' kg', color: '#f97316' },
                { label: 'Scope 3', value: (summary.by_scope['3'] || 0).toFixed(1) + ' kg', color: '#8b5cf6' },
                { label: 'Pending', value: summary.by_status['PENDING'] || 0, color: '#f59e0b' },
                { label: 'Approved', value: summary.by_status['APPROVED'] || 0, color: '#10b981' },
              ].map(card => (
                <div key={card.label} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '14px 20px', minWidth: 140 }}>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>{card.label}</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: card.color }}>{card.value}</div>
                </div>
              ))}
            </div>
          )}

          {loading && <p>Loading...</p>}

          {records.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f1f5f9' }}>
                  {['Category', 'Scope', 'Quantity', 'Unit', 'CO₂e (kg)', 'Period', 'Location', 'Status', 'Actions'].map(h => (
                    <th key={h} style={{ padding: '10px 8px', textAlign: 'left', borderBottom: '2px solid #e2e8f0' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #f1f5f9', background: r.status === 'FLAGGED' ? '#fff7ed' : '#fff' }}>
                    <td style={{ padding: '8px' }}>{r.category}</td>
                    <td style={{ padding: '8px' }}><span style={{ background: ['','#fee2e2','#fef3c7','#ede9fe'][r.scope], padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>Scope {r.scope}</span></td>
                    <td style={{ padding: '8px' }}>{r.activity_value?.toFixed(2)}</td>
                    <td style={{ padding: '8px', color: '#64748b' }}>{r.activity_unit}</td>
                    <td style={{ padding: '8px', fontWeight: 600 }}>{r.co2e_kg?.toFixed(2)}</td>
                    <td style={{ padding: '8px', fontSize: 11, color: '#64748b' }}>{r.period_start}</td>
                    <td style={{ padding: '8px', fontSize: 11 }}>{r.location?.slice(0, 20)}</td>
                    <td style={{ padding: '8px' }}>
                      <span style={{ background: COLORS[r.status] + '22', color: COLORS[r.status], padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>{r.status}</span>
                    </td>
                    <td style={{ padding: '8px' }}>
                      {r.status !== 'APPROVED' && (
                        <button onClick={() => reviewRecord(r.id, 'APPROVED')}
                          style={{ background: '#10b981', color: '#fff', border: 'none', padding: '3px 8px', borderRadius: 4, cursor: 'pointer', marginRight: 4, fontSize: 11 }}>✓</button>
                      )}
                      {r.status !== 'FLAGGED' && (
                        <button onClick={() => reviewRecord(r.id, 'FLAGGED')}
                          style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '3px 8px', borderRadius: 4, cursor: 'pointer', fontSize: 11 }}>⚑</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            !loading && <p style={{ color: '#94a3b8' }}>No records yet. Select a client and upload data.</p>
          )}
        </div>
      )}

      {/* UPLOAD TAB */}
      {tab === 'upload' && (
        <div style={{ maxWidth: 500 }}>
          <h3>Upload Emissions Data</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <label>Source Type:
              <select value={uploadSource} onChange={e => setUploadSource(e.target.value)}
                style={{ marginLeft: 12, padding: '6px 10px', borderRadius: 6, border: '1px solid #cbd5e1' }}>
                <option value='SAP'>SAP — Fuel & Procurement</option>
                <option value='UTILITY'>Utility — Electricity</option>
                <option value='TRAVEL'>Travel — Flights/Hotels/Car</option>
              </select>
            </label>
            <label>CSV File:
              <input type='file' accept='.csv' onChange={e => setUploadFile(e.target.files[0])}
                style={{ marginLeft: 12 }} />
            </label>
            <button onClick={uploadData} disabled={loading}
              style={{ padding: '10px 20px', background: '#7c3aed', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>
              {loading ? 'Uploading...' : 'Upload & Ingest'}
            </button>
            {uploadMsg && <p style={{ color: uploadMsg.startsWith('✅') ? '#10b981' : '#ef4444' }}>{uploadMsg}</p>}
          </div>
        </div>
      )}

      {/* SAMPLE DATA TAB */}
      {tab === 'sample_data' && (
        <div>
          <h3>Sample CSV Templates</h3>
          <p style={{ color: '#64748b' }}>Copy these into a .csv file and upload them to test the system.</p>

          {[{
            title: 'SAP — Fuel & Procurement',
            data: `MANDT,WERKS,MATNR,MENGE,MEINS,BUDAT,BELNR\n100,PUNE,DIESEL_FUEL,500,L,20240115,5000012301\n100,MUMBAI,PETROL_FUEL,300,L,20.01.2024,5000012302\n100,DELHI,LPG_GAS,200,KG,20240201,5000012303\n100,CHENNAI,DIESEL_FUEL,750,GAL,20240210,5000012304`
          }, {
            title: 'Utility — Electricity',
            data: `meter_id,facility,billing_period_start,billing_period_end,kwh,tariff\nMTR-001,Pune HQ,2024-01-01,2024-01-31,12500,commercial\nMTR-002,Mumbai Office,2024-01-01,2024-01-31,8700,commercial\nMTR-003,Delhi Plant,01/01/2024,31/01/2024,45000,industrial\nMTR-004,Bangalore,2024-01-15,2024-02-14,6200,commercial`
          }, {
            title: 'Travel — Flights, Hotels, Car',
            data: `trip_id,employee_id,travel_type,origin,destination,departure_date,return_date,class,distance_km,nights,city\nTRP001,EMP101,flight,BOM,DEL,2024-01-10,2024-01-12,economy,,\nTRP002,EMP102,flight,LHR,JFK,2024-01-15,2024-01-22,business,,\nTRP003,EMP103,hotel,,,2024-01-10,2024-01-12,,,2,New York\nTRP004,EMP101,car_rental,BOM,PUNE,2024-01-10,2024-01-10,,,,,\nTRP005,EMP104,train,DEL,AGR,2024-02-01,2024-02-01,economy,200,`
          }].map(s => (
            <div key={s.title} style={{ marginBottom: 24, background: '#f8fafc', borderRadius: 8, padding: 16, border: '1px solid #e2e8f0' }}>
              <h4 style={{ margin: '0 0 8px' }}>{s.title}</h4>
              <pre style={{ fontSize: 11, overflowX: 'auto', background: '#1e293b', color: '#e2e8f0', padding: 12, borderRadius: 6 }}>{s.data}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
