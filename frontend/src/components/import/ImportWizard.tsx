import { useState, useRef, useEffect } from 'react';
import { Upload, CheckCircle, Loader2, X, ChevronRight } from 'lucide-react';
import { importsApi } from '../../api/imports';
import type { ImportJob, ParserInfo } from '../../types';
import { getSourceColor } from '../ui/sourceColors';

interface Props {
  onClose: () => void;
  onImportDone: () => void;
}

type Step = 'select' | 'upload' | 'progress' | 'done';

export function ImportWizard({ onClose, onImportDone }: Props) {
  const [step, setStep] = useState<Step>('select');
  const [parsers, setParsers] = useState<ParserInfo[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [_job, setJob] = useState<ImportJob | null>(null);
  const [progress, setProgress] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    importsApi.parsers().then(setParsers);
    return () => esRef.current?.close();
  }, []);

  const handleFile = async (file: File) => {
    if (!selectedSource) return;
    setStep('progress');
    setError(null);
    try {
      const newJob = await importsApi.upload(file, selectedSource);
      setJob(newJob);
      streamProgress(newJob.id);
    } catch (e: any) {
      setError(e.message);
      setStep('upload');
    }
  };

  const streamProgress = (jobId: string) => {
    const es = importsApi.streamProgress(jobId);
    esRef.current = es;
    es.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'progress') {
        setProgress(msg.imported);
        if (msg.total) setTotal(msg.total);
      } else if (msg.type === 'done') {
        setProgress(msg.imported);
        setStep('done');
        es.close();
        onImportDone();
      } else if (msg.type === 'error') {
        setError(msg.message);
        setStep('upload');
        es.close();
      }
    };
    es.onerror = () => {
      // SSE closed normally after done/error
      es.close();
    };
  };

  const selectParser = (source: string) => {
    setSelectedSource(source);
    setStep('upload');
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 16,
          width: 520,
          maxWidth: '95vw',
          maxHeight: '85vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>Daten importieren</h2>
            <p style={{ margin: '4px 0 0', fontSize: 13, color: '#888' }}>
              {step === 'select' && 'Wähle eine Datenquelle'}
              {step === 'upload' && `Datei hochladen – ${parsers.find(p => p.source_name === selectedSource)?.display_name}`}
              {step === 'progress' && 'Import läuft…'}
              {step === 'done' && 'Import abgeschlossen!'}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
          {step === 'select' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {parsers.map(p => (
                <button
                  key={p.source_name}
                  onClick={() => selectParser(p.source_name)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '14px 16px',
                    borderRadius: 10,
                    border: '1.5px solid #e5e7eb',
                    background: '#fff',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'border-color 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.borderColor = getSourceColor(p.source_name))}
                  onMouseLeave={e => (e.currentTarget.style.borderColor = '#e5e7eb')}
                >
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 10,
                      background: `${getSourceColor(p.source_name)}22`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 20,
                      flexShrink: 0,
                    }}
                  >
                    {p.source_name === 'whatsapp' ? '💬' : p.source_name === 'calendar' ? '📅' : p.source_name === 'photos' ? '📷' : p.source_name === 'spotify' ? '🎵' : '📁'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 15, color: '#111' }}>{p.display_name}</div>
                    <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>{p.description}</div>
                    <div style={{ fontSize: 11, color: '#aaa', marginTop: 4 }}>
                      {p.supported_extensions.join(', ')}
                    </div>
                  </div>
                  <ChevronRight size={18} style={{ color: '#ccc' }} />
                </button>
              ))}
            </div>
          )}

          {step === 'upload' && (
            <div>
              {error && (
                <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: '#dc2626' }}>
                  {error}
                </div>
              )}
              <div
                onDragOver={e => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={e => {
                  e.preventDefault();
                  setDragging(false);
                  const f = e.dataTransfer.files[0];
                  if (f) handleFile(f);
                }}
                onClick={() => fileRef.current?.click()}
                style={{
                  border: `2px dashed ${dragging ? getSourceColor(selectedSource) : '#d1d5db'}`,
                  borderRadius: 12,
                  padding: '40px 24px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: dragging ? `${getSourceColor(selectedSource)}08` : '#fafafa',
                  transition: 'all 0.15s',
                }}
              >
                <Upload size={36} style={{ color: '#9ca3af', margin: '0 auto 12px', display: 'block' }} />
                <p style={{ margin: 0, fontWeight: 600, fontSize: 15, color: '#374151' }}>
                  Datei hier ablegen oder klicken
                </p>
                <p style={{ margin: '8px 0 0', fontSize: 13, color: '#9ca3af' }}>
                  {parsers.find(p => p.source_name === selectedSource)?.supported_extensions.join(', ')}
                </p>
              </div>
              <input
                ref={fileRef}
                type="file"
                style={{ display: 'none' }}
                onChange={e => {
                  const f = e.target.files?.[0];
                  if (f) handleFile(f);
                }}
              />
              <button
                onClick={() => setStep('select')}
                style={{ marginTop: 16, background: 'none', border: 'none', color: '#6366f1', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}
              >
                ← Andere Quelle wählen
              </button>
            </div>
          )}

          {step === 'progress' && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <Loader2 size={40} style={{ color: '#6366f1', margin: '0 auto 16px', display: 'block', animation: 'spin 1s linear infinite' }} />
              <p style={{ fontWeight: 600, fontSize: 16, margin: '0 0 8px' }}>Import läuft…</p>
              <p style={{ color: '#888', fontSize: 14, margin: 0 }}>
                {progress > 0 ? `${progress.toLocaleString('de')} Events importiert` : 'Verarbeite Datei…'}
              </p>
              {total > 0 && (
                <div style={{ marginTop: 16, background: '#f3f4f6', borderRadius: 8, height: 8, overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      background: '#6366f1',
                      width: `${Math.min(100, (progress / total) * 100)}%`,
                      transition: 'width 0.3s',
                      borderRadius: 8,
                    }}
                  />
                </div>
              )}
            </div>
          )}

          {step === 'done' && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <CheckCircle size={48} style={{ color: '#22c55e', margin: '0 auto 16px', display: 'block' }} />
              <p style={{ fontWeight: 700, fontSize: 18, margin: '0 0 8px' }}>Fertig!</p>
              <p style={{ color: '#666', fontSize: 14, margin: 0 }}>
                {progress.toLocaleString('de')} Events wurden in deine Timeline importiert.
              </p>
              <button
                onClick={onClose}
                style={{
                  marginTop: 24,
                  background: '#6366f1',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  padding: '10px 24px',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Timeline anzeigen
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
