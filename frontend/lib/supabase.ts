import { createClient } from '@supabase/supabase-js';

// Get these from your Supabase Dashboard -> Settings -> API
const supabaseUrl = 'https://vsaqtwfmvnhmjvigctug.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZzYXF0d2Ztdm5obWp2aWdjdHVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUzNjU2NDgsImV4cCI6MjA5MDk0MTY0OH0.6Pxvi4ToSvM1NqTEjIlqXkwCg6AMhcgOjxf3h-jlzA8';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);