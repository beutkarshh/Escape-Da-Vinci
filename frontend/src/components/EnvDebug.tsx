import React from 'react';
import { config } from '@/config';

export default function EnvDebug() {
  const supabaseUrl = config.supabase.url;
  const publishableKey = !!config.supabase.publishableKey;
  const devAuth = config.devAuth;
  const supabaseConfigured = Boolean(supabaseUrl && publishableKey);

  return (
    <div style={{position: 'fixed', right: 8, bottom: 8, zIndex: 9999}}>
      <details style={{background: 'rgba(0,0,0,0.6)', color: '#fff', padding: 8, borderRadius: 6}}>
        <summary style={{cursor: 'pointer', fontSize: 12}}>Runtime Config (dev only)</summary>
        <div style={{fontSize: 12, whiteSpace: 'pre-wrap'}}>
          supabase.url: {String(supabaseUrl)}\n
          supabase.publishableKey: {publishableKey ? 'present' : 'missing'}\n
          devAuth: {String(devAuth)}\n
          supabaseConfigured: {String(supabaseConfigured)}
        </div>
      </details>
    </div>
  );
}
