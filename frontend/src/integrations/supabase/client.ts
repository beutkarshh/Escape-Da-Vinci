import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';
import { config } from '@/config';

const SUPABASE_URL = config.supabase.url;
const SUPABASE_PUBLISHABLE_KEY = config.supabase.publishableKey;

export const supabaseConfigured = Boolean(SUPABASE_URL && SUPABASE_PUBLISHABLE_KEY);
if (!supabaseConfigured) {
  const errorMsg = `[Supabase] Missing required configuration in src/config.ts:
  - supabase.url: ${SUPABASE_URL || 'MISSING'}
  - supabase.publishableKey: ${SUPABASE_PUBLISHABLE_KEY ? 'present' : 'MISSING'}`;
  console.error(errorMsg);
  throw new Error(errorMsg);
}

export const supabase = createClient<Database>(
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY,
  {
    auth: {
      storage: localStorage,
      persistSession: true,
      autoRefreshToken: true,
    }
  }
);