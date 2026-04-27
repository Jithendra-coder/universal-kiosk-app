"use client";
import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { LayoutDashboard, UtensilsCrossed, Monitor, Lock, LogIn, Loader2, UserPlus } from 'lucide-react';
import Link from 'next/link';

export default function MasterPortal() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [view, setView] = useState<'login' | 'signup'>('login');
  const [loading, setLoading] = useState(false);

  // Check if user is already logged in when the page loads
  useEffect(() => {
    const checkUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) setIsLoggedIn(true);
    };
    checkUser();
  }, []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const { error } = view === 'login' 
      ? await supabase.auth.signInWithPassword({ email, password })
      : await supabase.auth.signUp({ email, password });

    if (error) {
      alert(error.message);
    } else {
      if (view === 'signup') alert("Check your email for confirmation!");
      else setIsLoggedIn(true);
    }
    setLoading(false);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return (
      <main className="h-screen flex items-center justify-center bg-slate-50 font-sans p-6">
        <form onSubmit={handleAuth} className="max-w-md w-full bg-white rounded-[3rem] shadow-2xl p-12 border-t-8 border-orange-500">
          <h1 className="text-4xl font-black tracking-tighter mb-2 italic">WELCOME</h1>
          <p className="text-slate-400 font-bold mb-8 uppercase text-xs tracking-widest">Universal Food System</p>
          
          <div className="space-y-4">
            <input 
              required
              type="email"
              className="w-full p-5 bg-slate-50 rounded-2xl border-2 border-transparent focus:border-orange-500 outline-none font-bold transition-all" 
              placeholder="Email Address" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input 
              required
              type="password"
              className="w-full p-5 bg-slate-50 rounded-2xl border-2 border-transparent focus:border-orange-500 outline-none font-bold transition-all" 
              placeholder="Password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            
            <button 
              disabled={loading}
              type="submit"
              className="w-full bg-orange-600 text-white py-5 rounded-2xl font-black text-xl flex items-center justify-center gap-2 hover:bg-slate-900 disabled:bg-slate-400 transition-all shadow-lg"
            >
              {loading ? <Loader2 className="animate-spin" /> : <LogIn size={24} />}
              {view === 'login' ? 'SIGN IN' : 'CREATE ACCOUNT'}
            </button>
            
            <button 
              type="button"
              onClick={() => setView(view === 'login' ? 'signup' : 'login')}
              className="w-full text-slate-400 font-bold py-2 hover:text-orange-600 transition-colors text-sm"
            >
              {view === 'login' ? "Don't have an account? Sign Up" : "Already have an account? Login"}
            </button>
          </div>
        </form>
      </main>
    );
  }

  return (
    <main className="h-screen bg-slate-900 flex flex-col items-center justify-center p-10 font-sans text-white">
      <div className="text-center mb-16">
        <h1 className="text-6xl font-black tracking-tighter italic text-orange-500">SELECT MODULE</h1>
        <p className="text-slate-500 font-bold tracking-[0.3em] uppercase mt-2 italic">Authorized Session Active</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full">
        {/* KIOSK CARD */}
        <Link href="/kiosk" className="group h-full">
          <ModuleCard 
            icon={<Monitor size={64} />} 
            title="KIOSK APP" 
            desc="Customer-facing ordering interface" 
            color="group-hover:border-orange-500" 
            iconColor="text-orange-500"
            bg="bg-orange-500/10"
          />
        </Link>

        {/* KITCHEN CARD */}
        <Link href="/kitchen" className="group h-full">
          <ModuleCard 
            icon={<UtensilsCrossed size={64} />} 
            title="KITCHEN KDS" 
            desc="Live order queue for chefs" 
            color="group-hover:border-emerald-500" 
            iconColor="text-emerald-500"
            bg="bg-emerald-500/10"
          />
        </Link>

        {/* ADMIN CARD */}
        <Link href="/admin" className="group h-full">
          <ModuleCard 
            icon={<LayoutDashboard size={64} />} 
            title="ADMIN PANEL" 
            desc="Manage menu, prices, and users" 
            color="group-hover:border-blue-500" 
            iconColor="text-blue-500"
            bg="bg-blue-500/10"
          />
        </Link>
      </div>

      <button onClick={handleLogout} className="mt-16 text-slate-500 hover:text-white font-bold flex items-center gap-2 underline underline-offset-8 transition-colors">
        <Lock size={16} /> LOGOUT SECURELY
      </button>
    </main>
  );
}

// Sub-component for cleaner code
function ModuleCard({ icon, title, desc, color, iconColor, bg }: any) {
  return (
    <div className={`bg-slate-800 p-10 rounded-[3rem] border-4 border-transparent ${color} group-hover:bg-slate-800/50 transition-all h-full flex flex-col items-center text-center shadow-2xl`}>
      <div className={`${bg} p-6 rounded-3xl mb-6 ${iconColor} group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <h2 className="text-3xl font-black mb-2 italic tracking-tight">{title}</h2>
      <p className="text-slate-400 font-medium leading-tight">{desc}</p>
    </div>
  );
}