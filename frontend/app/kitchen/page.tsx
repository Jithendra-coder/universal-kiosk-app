"use client";
import { useEffect, useState, useCallback } from 'react';
import { supabase } from '../../lib/supabase';
import { 
  Clock, CheckCircle2, Flame, Search, Filter, 
  AlertTriangle, Play, Check, ChevronRight, Package,
  Zap, Power, Loader2, Utensils
} from 'lucide-react';

export default function KitchenPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<'active' | 'completed' | 'inventory'>('active');

  // --- 1. DATA FETCHING ---
  const fetchData = useCallback(async () => {
    // Fetch Orders
    let orderQuery = supabase.from('orders').select('*, order_items(*)');
    if (activeTab === 'active') {
        orderQuery = orderQuery.in('status', ['pending', 'preparing', 'ready']);
    } else if (activeTab === 'completed') {
        orderQuery = orderQuery.eq('status', 'completed');
    }
    
    const { data: oData } = await orderQuery.order('created_at', { ascending: false });
    
    // Fetch Products (for Inventory Tab)
    const { data: pData } = await supabase.from('products').select('*').order('name');

    setOrders(oData || []);
    setProducts(pData || []);
    setLoading(false);
  }, [activeTab]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, [fetchData]);

  // --- 2. ACTIONS ---
  const updateStatus = async (orderId: string, newStatus: string) => {
    const updateData: any = { status: newStatus };
    if (newStatus === 'preparing') updateData.prep_started_at = new Date().toISOString();
    
    await supabase.from('orders').update(updateData).eq('id', orderId);
    fetchData();
  };

  const toggleProduct = async (id: string, currentStatus: boolean) => {
    await supabase.from('products').update({ is_available: !currentStatus }).eq('id', id);
    fetchData();
  };

  // Filtered Logic
  const filteredOrders = orders.filter(o => 
    o.order_number?.toString().includes(searchQuery) || 
    o.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <main className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      
      {/* --- SIDEBAR NAVIGATION --- */}
      <aside className="w-24 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-8 gap-8">
        <div className="w-12 h-12 bg-orange-600 rounded-2xl flex items-center justify-center shadow-lg shadow-orange-900/20">
            <Flame className="text-white" size={28} />
        </div>
        <nav className="flex flex-col gap-4">
            <NavBtn active={activeTab === 'active'} onClick={() => setActiveTab('active')} icon={<Zap size={24}/>} label="LIVE" />
            <NavBtn active={activeTab === 'completed'} onClick={() => setActiveTab('completed')} icon={<CheckCircle2 size={24}/>} label="DONE" />
            <NavBtn active={activeTab === 'inventory'} onClick={() => setActiveTab('inventory')} icon={<Package size={24}/>} label="STOCK" />
        </nav>
      </aside>

      {/* --- MAIN CONTENT --- */}
      <section className="flex-1 flex flex-col overflow-hidden">
        
        {/* TOP BAR */}
        <header className="p-6 bg-slate-900/50 border-b border-slate-800 flex justify-between items-center">
            <div className="flex items-center gap-6">
                <h1 className="text-3xl font-black italic tracking-tighter uppercase">
                    {activeTab === 'inventory' ? 'Inventory Control' : 'Kitchen Flow'}
                </h1>
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input 
                        placeholder="Search Ticket #" 
                        className="bg-slate-800 border-none rounded-xl py-3 pl-12 pr-6 w-64 text-sm font-bold focus:ring-2 focus:ring-orange-500 outline-none transition-all"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>
            <div className="flex items-center gap-3">
                <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center gap-2">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-emerald-500">System Live</span>
                </div>
            </div>
        </header>

        {/* WORKSPACE */}
        <div className="flex-1 overflow-y-auto p-8">
            {activeTab === 'inventory' ? (
                <InventoryView products={products} onToggle={toggleProduct} />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {filteredOrders.map(order => (
                        <OrderTicket 
                            key={order.id} 
                            order={order} 
                            onUpdate={updateStatus} 
                        />
                    ))}
                    {filteredOrders.length === 0 && !loading && <EmptyState />}
                </div>
            )}
        </div>
      </section>
    </main>
  );
}

// --- 🎫 COMPONENT: ORDER TICKET ---
function OrderTicket({ order, onUpdate }: { order: any, onUpdate: any }) {
    const timeAgo = (date: string) => {
        const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000);
        if (seconds < 60) return `${seconds}s`;
        return `${Math.floor(seconds/60)}m`;
    };

    const getStatusColor = () => {
        if (order.status === 'pending') return 'border-rose-500/50 bg-rose-500/5';
        if (order.status === 'preparing') return 'border-orange-500/50 bg-orange-500/5';
        return 'border-emerald-500/50 bg-emerald-500/5';
    };

    return (
        <div className={`rounded-4xl border-2 flex flex-col overflow-hidden shadow-2xl transition-all ${getStatusColor()}`}>
            {/* Header */}
            <div className="p-5 border-b border-white/5 flex justify-between items-center bg-white/5">
                <div>
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest block">Ticket</span>
                    <span className="text-2xl font-black text-white">#{order.order_number}</span>
                </div>
                <div className="text-right">
                    <div className="flex items-center gap-1.5 text-orange-400 font-black">
                        <Clock size={14} />
                        <span className="text-sm">{timeAgo(order.created_at)}</span>
                    </div>
                    {order.prep_started_at && (
                        <span className="text-[10px] font-bold text-slate-500 uppercase">Prep: {timeAgo(order.prep_started_at)}</span>
                    )}
                </div>
            </div>

            {/* Items List */}
            <div className="p-6 flex-1 space-y-4">
                {order.order_items?.map((item: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-3">
                        <div className="bg-slate-800 text-orange-500 w-8 h-8 rounded-lg flex items-center justify-center font-black text-sm shrink-0">
                            {item.quantity}
                        </div>
                        <div className="flex-1">
                            <p className="text-lg font-bold leading-tight">{item.product_name || 'Menu Item'}</p>
                            {/* Special Instructions Placeholder */}
                            {idx === 0 && <p className="text-[10px] text-rose-400 font-bold uppercase mt-1 flex items-center gap-1"><AlertTriangle size={10}/> No Onion / Extra Spicy</p>}
                        </div>
                    </div>
                ))}
            </div>

            {/* Bottom Actions */}
            <div className="p-4 bg-black/20 mt-auto">
                {order.status === 'pending' && (
                    <button onClick={() => onUpdate(order.id, 'preparing')} className="w-full bg-orange-600 hover:bg-orange-500 py-4 rounded-2xl font-black flex items-center justify-center gap-2 transition-all active:scale-95">
                        <Play size={18} fill="currentColor"/> START PREP
                    </button>
                )}
                {order.status === 'preparing' && (
                    <button onClick={() => onUpdate(order.id, 'ready')} className="w-full bg-blue-600 hover:bg-blue-500 py-4 rounded-2xl font-black flex items-center justify-center gap-2 transition-all active:scale-95">
                        <Check size={20}/> MARK READY
                    </button>
                )}
                {order.status === 'ready' && (
                    <button onClick={() => onUpdate(order.id, 'completed')} className="w-full bg-emerald-600 hover:bg-emerald-500 py-4 rounded-2xl font-black flex items-center justify-center gap-2 transition-all active:scale-95">
                        <CheckCircle2 size={20}/> BUMP ORDER
                    </button>
                )}
                {order.status === 'completed' && (
                    <div className="text-center py-2 font-black text-slate-500 text-xs uppercase italic">Archived Order</div>
                )}
            </div>
        </div>
    );
}

// --- 📦 COMPONENT: INVENTORY VIEW ---
function InventoryView({ products, onToggle }: { products: any[], onToggle: any }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 animate-in fade-in slide-in-from-bottom-4">
            {products.map(p => (
                <div key={p.id} className="bg-slate-900 p-6 rounded-4xl border border-slate-800 flex items-center justify-between group">
                    <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black ${p.is_available ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'}`}>
                            {p.is_available ? <Utensils size={20}/> : <Power size={20}/>}
                        </div>
                        <div>
                            <p className="font-black uppercase tracking-tight">{p.name}</p>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{p.category}</p>
                        </div>
                    </div>
                    <button 
                        onClick={() => onToggle(p.id, p.is_available)}
                        className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase transition-all ${p.is_available ? 'bg-slate-800 text-slate-400 hover:bg-rose-600 hover:text-white' : 'bg-emerald-600 text-white'}`}
                    >
                        {p.is_available ? 'Disable' : 'Enable'}
                    </button>
                </div>
            ))}
        </div>
    );
}

// --- UI HELPERS ---
function NavBtn({ active, icon, label, onClick }: any) {
    return (
        <button onClick={onClick} className={`flex flex-col items-center gap-1 p-4 rounded-2xl transition-all ${active ? 'bg-orange-600 text-white shadow-lg' : 'text-slate-500 hover:bg-slate-800'}`}>
            {icon}
            <span className="text-[10px] font-black">{label}</span>
        </button>
    );
}

function EmptyState() {
    return (
        <div className="col-span-full py-40 flex flex-col items-center justify-center opacity-20">
            <Utensils size={80} className="mb-6" />
            <h2 className="text-4xl font-black uppercase italic italic">Kitchen Quiet...</h2>
        </div>
    );
}