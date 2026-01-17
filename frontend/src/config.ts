// Runtime configuration
// This file is used instead of import.meta.env due to Vite env loading issues on Windows
// TODO: Move back to .env once Vite env loading is fixed

export const config = {
  supabase: {
    url: 'https://xswdrzlnvxqzgqfrdhxs.supabase.co',
    publishableKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhzd2RyemxudnhxemdxZnJkaHhzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0MjkwOTIsImV4cCI6MjA3NTAwNTA5Mn0.ecpaTpTD_2sKSE7WxzBnZ6UsXYqj0wuGcpsroYO6jsk',
  },
  devAuth: true, // Set to true to enable dev-only bypass auth
};
