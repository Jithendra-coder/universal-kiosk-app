"use client";
import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../../lib/supabase';
import { 
  LayoutDashboard, Utensils, ClipboardList, Settings as SettingsIcon, 
  Plus, Package, AlertCircle, TrendingUp, Trash2, Edit3,
  Loader2, X, Monitor, Save, Store, Camera, ChevronRight,
  Clock, Rocket, ImageIcon, CalendarDays, Leaf, Drumstick, Banknote, Globe, Pizza, Coffee, CakeSlice
} from 'lucide-react';

// Common Currencies List
const CURRENCIES = [
  { code: 'INR', symbol: '₹', name: 'Indian Rupee' },
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'AED', symbol: 'د.إ', name: 'UAE Dirham' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [settings, setSettings] = useState<any>({ currency_symbol: '₹', store_name: 'Loading...' });

  const refreshSettings = useCallback(async () => {
    const { data } = await supabase.from('restaurant_settings').select('*').limit(1).single();
    if (data) setSettings(data);
  }, []);

  useEffect(() => { refreshSettings(); }, [refreshSettings]);

  return (
    <main className="flex h-screen bg-[#F8FAFC] font-sans text-slate-900 overflow-hidden">
      {/* --- SIDEBAR --- */}
      <aside className="w-80 bg-slate-950 text-white flex flex-col p-8 shadow-2xl">
        <div className="mb-12">
            <h1 className="text-3xl font-black tracking-tighter text-orange-500 italic uppercase">Core <span className="text-white">Pro</span></h1>
            <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.3em] mt-2 truncate text-center">{settings.store_name}</p>
        </div>
        <nav className="flex-1 space-y-3">
          <NavItem icon={<LayoutDashboard size={20}/>} label="Dashboard" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <NavItem icon={<ClipboardList size={20}/>} label="Orders" active={activeTab === 'orders'} onClick={() => setActiveTab('orders')} />
          <NavItem icon={<Utensils size={20}/>} label="Menu Vault" active={activeTab === 'menu'} onClick={() => setActiveTab('menu')} />
          <NavItem icon={<SettingsIcon size={20}/>} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
        </nav>
      </aside>

      <section className="flex-1 overflow-y-auto p-12">
        {activeTab === 'overview' && <OverviewTab settings={settings} />}
        {activeTab === 'orders' && <OrdersPage settings={settings} />}
        {activeTab === 'menu' && <MenuPage settings={settings} />}
        {activeTab === 'settings' && <SettingsPage onRefresh={refreshSettings} />}
      </section>
    </main>
  );
}

// --- 🏠 1. DASHBOARD ---
function OverviewTab({ settings }: { settings: any }) {
  const [stats, setStats] = useState({ revenue: 0, orders: 0, avg: 0 });
  const [weekly, setWeekly] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const { data: s } = await supabase.from('admin_overview_stats').select('*').single();
      const { data: w } = await supabase.from('weekly_order_summary').select('*');
      if (s) setStats({ 
        revenue: s.revenue_today || 0, 
        orders: s.orders_today || 0,
        avg: s.orders_today > 0 ? (s.revenue_today / s.orders_today) : 0
      });
      if (w) setWeekly(w);
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-10 animate-in fade-in">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <StatCard title="Revenue Today" value={`${settings.currency_symbol}${stats.revenue}`} icon={<TrendingUp size={24}/>} />
        <StatCard title="Total Orders" value={stats.orders} icon={<Package size={24}/>} />
        <StatCard title="Avg. Order Value" value={`${settings.currency_symbol}${stats.avg.toFixed(2)}`} icon={<Banknote size={24}/>} />
      </div>

      <div className="bg-white p-10 rounded-[3rem] shadow-xl border border-slate-100">
        <div className="flex items-center gap-3 mb-8 text-slate-400 font-black uppercase text-xs tracking-widest">
            <CalendarDays size={18} /> 7-Day Performance
        </div>
        <div className="overflow-hidden rounded-3xl border border-slate-50">
            <table className="w-full text-left">
                <thead className="bg-slate-900 text-white text-[10px] font-black uppercase tracking-widest">
                    <tr><th className="p-6">Date</th><th className="p-6 text-center">Orders</th><th className="p-6 text-right">Revenue</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-50 font-bold">
                    {weekly.map((day, i) => (
                        <tr key={i} className="hover:bg-slate-50 transition-colors">
                            <td className="p-6 text-slate-600">{day.date_label}</td>
                            <td className="p-6 text-center font-black">{day.total_orders}</td>
                            <td className="p-6 text-right font-black text-orange-600">{settings.currency_symbol}{day.total_revenue}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
      </div>
    </div>
  );
}

// --- 🧾 2. ORDERS PAGE ---
function OrdersPage({ settings }: { settings: any }) {
    const [orders, setOrders] = useState<any[]>([]);
    const [filter, setFilter] = useState('active');
    const [selectedOrder, setSelectedOrder] = useState<any>(null);

    const fetchOrders = useCallback(async () => {
        let query = supabase.from('orders').select('*');
        if (filter === 'active') query = query.in('status', ['pending', 'preparing', 'ready']);
        else query = query.eq('status', 'completed');
        const { data } = await query.order('created_at', { ascending: false });
        setOrders(data || []);
    }, [filter]);

    useEffect(() => { fetchOrders(); }, [fetchOrders]);

    return (
        <div className="space-y-8 animate-in fade-in">
            <div className="flex justify-between items-center">
                <h2 className="text-4xl font-black italic tracking-tighter uppercase">Orders</h2>
                <div className="flex bg-slate-200 p-1.5 rounded-2xl gap-2 font-black text-[10px] uppercase">
                    <button onClick={() => setFilter('active')} className={`px-6 py-3 rounded-xl transition-all ${filter === 'active' ? 'bg-slate-950 text-white shadow-lg' : 'text-slate-500'}`}>Active</button>
                    <button onClick={() => setFilter('completed')} className={`px-6 py-3 rounded-xl transition-all ${filter === 'completed' ? 'bg-slate-950 text-white shadow-lg' : 'text-slate-500'}`}>Completed</button>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {orders.map(o => (
                    <div key={o.id} onClick={() => setSelectedOrder(o)} className="bg-white p-6 rounded-[2.5rem] border border-slate-100 shadow-sm flex items-center justify-between hover:border-orange-500 transition-all cursor-pointer group">
                        <div className="flex items-center gap-6">
                            <div className="bg-slate-900 text-white w-14 h-14 rounded-2xl flex items-center justify-center font-black italic">#{o.order_number}</div>
                            <div>
                                <p className="font-black text-xl text-slate-900">{settings.currency_symbol}{o.total_amount}</p>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{new Date(o.created_at).toLocaleTimeString()}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className={`px-5 py-2 rounded-full font-black text-[10px] uppercase ${o.status === 'pending' ? 'bg-orange-100 text-orange-600' : 'bg-emerald-100 text-emerald-600'}`}>{o.status}</span>
                            <ChevronRight className="text-slate-200 group-hover:text-orange-500" />
                        </div>
                    </div>
                ))}
            </div>

            {selectedOrder && (
                <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6">
                    <div className="bg-white w-full max-w-md rounded-[3rem] p-10 shadow-2xl relative animate-in zoom-in">
                        <button onClick={() => setSelectedOrder(null)} className="absolute top-8 right-8 text-slate-400 hover:text-rose-500"><X/></button>
                        <div className="text-center mb-8">
                            <div className="bg-slate-900 text-white w-20 h-20 rounded-4xl flex items-center justify-center font-black italic text-3xl mx-auto mb-4">#{selectedOrder.order_number}</div>
                            <h3 className="text-2xl font-black italic uppercase">Order Ticket</h3>
                            <p className="text-[10px] font-black text-slate-400 uppercase">{new Date(selectedOrder.created_at).toLocaleString()}</p>
                        </div>
                        <div className="flex justify-between items-center font-black pt-6 border-t border-slate-100">
                            <span className="text-slate-400 text-xs uppercase">Grand Total</span>
                            <span className="text-4xl text-slate-950">{settings.currency_symbol}{selectedOrder.total_amount}</span>
                        </div>
                        <button onClick={() => setSelectedOrder(null)} className="w-full mt-8 bg-slate-950 text-white py-5 rounded-2xl font-black uppercase italic hover:bg-orange-600 transition-all">Close</button>
                    </div>
                </div>
            )}
        </div>
    );
}

// --- 🍔 3. MENU PAGE (WITH CATEGORY ICONS & EDITING) ---
function MenuPage({ settings }: { settings: any }) {
    const [products, setProducts] = useState<any[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [formData, setFormData] = useState({ name: '', price: '', category: 'Main', item_type: 'Veg', image_path: '' });

    const fetchProducts = useCallback(async () => {
        const { data } = await supabase.from('products').select('*').order('created_at', { ascending: false });
        setProducts(data || []);
    }, []);

    useEffect(() => { fetchProducts(); }, [fetchProducts]);

    const getPlaceholderIcon = (category: string) => {
        switch (category) {
            case 'Drinks': return <Coffee size={32} className="text-blue-400" />;
            case 'Starter': return <Pizza size={32} className="text-orange-400" />;
            case 'Dessert': return <CakeSlice size={32} className="text-pink-400" />;
            default: return <Utensils size={32} className="text-slate-300" />;
        }
    };

    const handleUpload = async (e: any) => {
        const file = e.target.files[0];
        if (!file || !file.type.startsWith('image/')) {
            alert("Images only, please.");
            return;
        }
        setUploading(true);
        const fileName = `${Date.now()}-${file.name}`;
        const { data } = await supabase.storage.from('product-images').upload(fileName, file);
        if (data) {
            const { data: { publicUrl } } = supabase.storage.from('product-images').getPublicUrl(data.path);
            setFormData(prev => ({ ...prev, image_path: publicUrl }));
        }
        setUploading(false);
    };

    const handleSave = async (e: any) => {
        e.preventDefault();
        const payload = { 
            ...formData, 
            price: parseFloat(formData.price),
            image_path: formData.image_path === "" ? null : formData.image_path 
        };
        if (editingId) {
            await supabase.from('products').update(payload).eq('id', editingId);
        } else {
            await supabase.from('products').insert([payload]);
        }
        setIsModalOpen(false);
        setEditingId(null);
        setFormData({ name: '', price: '', category: 'Main', item_type: 'Veg', image_path: '' });
        fetchProducts();
    };

    const openEdit = (p: any) => {
        setEditingId(p.id);
        setFormData({ name: p.name, price: p.price.toString(), category: p.category, item_type: p.item_type, image_path: p.image_path || '' });
        setIsModalOpen(true);
    };

    return (
        <div className="space-y-8 animate-in fade-in">
            <div className="flex justify-between items-end">
                <h2 className="text-4xl font-black italic tracking-tighter uppercase text-slate-900">Menu Vault</h2>
                <button onClick={() => {setEditingId(null); setIsModalOpen(true);}} className="bg-orange-600 text-white px-8 py-4 rounded-2xl font-black flex items-center gap-2 hover:bg-slate-900 shadow-lg transition-all"><Plus size={20}/> ADD ITEM</button>
            </div>

            {isModalOpen && (
                <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6">
                    <form onSubmit={handleSave} className="bg-white w-full max-w-lg rounded-[3rem] p-10 shadow-2xl relative grid grid-cols-2 gap-4 animate-in zoom-in">
                        <h3 className="col-span-2 text-2xl font-black mb-4 italic uppercase">{editingId ? 'Edit Item' : 'New Item'}</h3>
                        <input required className="col-span-2 p-5 bg-slate-50 rounded-2xl font-bold border-none outline-none" placeholder="Item Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                        <input required type="number" step="0.01" className="p-5 bg-slate-50 rounded-2xl font-bold border-none outline-none" placeholder={`Price (${settings.currency_symbol})`} value={formData.price} onChange={e => setFormData({...formData, price: e.target.value})} />
                        <select className="p-5 bg-slate-50 rounded-2xl font-bold border-none outline-none cursor-pointer" value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})}>
                            <option value="Starter">Starter</option><option value="Main">Main Course</option><option value="Dessert">Dessert</option><option value="Drinks">Drinks</option>
                        </select>
                        <div className="col-span-2 flex gap-2 bg-slate-50 p-2 rounded-2xl">
                            <button type="button" onClick={() => setFormData({...formData, item_type: 'Veg'})} className={`flex-1 py-3 rounded-xl font-black text-xs transition-all ${formData.item_type === 'Veg' ? 'bg-emerald-500 text-white shadow-md' : 'text-slate-400'}`}><Leaf size={14} className="inline mr-1"/> VEG</button>
                            <button type="button" onClick={() => setFormData({...formData, item_type: 'Non-Veg'})} className={`flex-1 py-3 rounded-xl font-black text-xs transition-all ${formData.item_type === 'Non-Veg' ? 'bg-rose-500 text-white shadow-md' : 'text-slate-400'}`}><Drumstick size={14} className="inline mr-1"/> NON-VEG</button>
                        </div>
                        <div className="col-span-2 border-4 border-dashed border-slate-100 rounded-4xl p-6 text-center relative group overflow-hidden">
                            <input type="file" accept="image/*" className="absolute inset-0 opacity-0 cursor-pointer z-10" onChange={handleUpload} />
                            {uploading ? <Loader2 className="animate-spin mx-auto text-orange-500" /> : 
                              formData.image_path ? <img src={formData.image_path} className="h-24 mx-auto rounded-xl object-cover shadow-lg" /> : 
                              <div className="text-slate-400 font-black text-xs uppercase flex flex-col items-center gap-2"><Camera size={32}/> Upload Photo</div>
                            }
                        </div>
                        <button type="submit" className="col-span-2 bg-slate-950 text-white py-5 rounded-2xl font-black text-xl hover:bg-orange-600 transition-all uppercase italic">Save</button>
                        <button type="button" onClick={() => setIsModalOpen(false)} className="col-span-2 text-slate-400 font-bold uppercase text-[10px] tracking-widest mt-2">Close</button>
                    </form>
                </div>
            )}

            <div className="bg-white rounded-[3rem] shadow-xl overflow-hidden border border-slate-100">
                <table className="w-full text-left">
                    <thead className="bg-slate-50 border-b border-slate-100 font-black uppercase text-[10px] text-slate-400 tracking-widest">
                        <tr><th className="p-8">Image</th><th className="p-8">Details</th><th className="p-8">Price</th><th className="p-8 text-right">Actions</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50 font-black">
                        {products.map(p => (
                            <tr key={p.id} className="hover:bg-slate-50 transition-colors group">
                                <td className="p-8"><div className="w-20 h-20 bg-slate-100 rounded-3xl overflow-hidden shadow-inner border-2 border-white flex items-center justify-center">
                                    {p.image_path ? <img src={p.image_path} className="w-full h-full object-cover" /> : getPlaceholderIcon(p.category)}
                                </div></td>
                                <td className="p-8"><p className="text-xl text-slate-900 italic tracking-tighter uppercase leading-none">{p.name}</p>
                                    <div className="flex gap-2 mt-3">
                                        <span className="text-[9px] uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-400 border border-slate-200">{p.category}</span>
                                        <span className={`text-[9px] uppercase px-2 py-0.5 rounded-full ${p.item_type === 'Veg' ? 'bg-emerald-100 text-emerald-600 border border-emerald-100' : 'bg-rose-100 text-rose-600 border border-rose-100'}`}>{p.item_type}</span>
                                    </div>
                                </td>
                                <td className="p-8 text-orange-600 text-2xl tracking-tighter">{settings.currency_symbol}{p.price}</td>
                                <td className="p-8 text-right">
                                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button onClick={() => openEdit(p)} className="p-3 text-slate-300 hover:text-slate-950 transition-colors"><Edit3 size={18}/></button>
                                        <button onClick={async () => { if(confirm('Delete?')) { await supabase.from('products').delete().eq('id', p.id); fetchProducts(); } }} className="p-3 text-slate-300 hover:text-rose-600 transition-colors"><Trash2 size={18}/></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// --- ⚙️ 4. SETTINGS PAGE ---
function SettingsPage({ onRefresh }: { onRefresh: () => void }) {
    const [config, setConfig] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        supabase.from('restaurant_settings').select('*').limit(1).single().then(({data}) => { if (data) setConfig(data); });
    }, []);

    const handleCurrencyChange = (e: any) => {
        const selected = CURRENCIES.find(c => c.code === e.target.value);
        if (selected) setConfig({...config, currency_symbol: selected.symbol});
    };

    const save = async () => {
        if (!config?.id) return;
        setLoading(true);
        const { error } = await supabase.from('restaurant_settings').update(config).eq('id', config.id);
        if (error) alert(error.message);
        else { alert("✅ Settings Saved!"); onRefresh(); }
        setLoading(false);
    };

    if (!config) return <div className="p-20 text-center font-black animate-pulse text-slate-300 uppercase italic">Loading...</div>;

    return (
        <div className="space-y-12 max-w-5xl animate-in slide-in-from-bottom-6">
            <div className="flex justify-between items-center border-b pb-8">
                <h2 className="text-4xl font-black italic tracking-tighter uppercase text-slate-950">System Config</h2>
                <button onClick={save} disabled={loading} className="bg-slate-950 text-white px-10 py-5 rounded-3xl font-black flex items-center gap-2 hover:bg-orange-600 transition-all shadow-xl active:scale-95 uppercase italic">
                    {loading ? <Loader2 className="animate-spin"/> : <Save size={20}/>} Save
                </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <section className="bg-white p-10 rounded-[3.5rem] shadow-xl border border-slate-100 space-y-6">
                    <div className="flex items-center gap-3 text-orange-500 font-black text-xs uppercase tracking-widest"><Store size={20}/> Identity</div>
                    <input className="w-full p-5 bg-slate-50 rounded-2xl font-black border-none" value={config.store_name || ''} onChange={e => setConfig({...config, store_name: e.target.value})} />
                    <input className="w-full p-5 bg-slate-50 rounded-2xl font-black border-none" value={config.branch_name || ''} onChange={e => setConfig({...config, branch_name: e.target.value})} />
                </section>
                <section className="bg-white p-10 rounded-[3.5rem] shadow-xl border border-slate-100 space-y-6">
                    <div className="flex items-center gap-3 text-emerald-500 font-black text-xs uppercase tracking-widest"><Globe size={20}/> Localization</div>
                    <select onChange={handleCurrencyChange} className="w-full p-5 bg-slate-50 rounded-2xl font-black border-none cursor-pointer">
                        <option value="">Select Currency</option>
                        {CURRENCIES.map(c => <option key={c.code} value={c.code}>{c.code} - {c.symbol}</option>)}
                    </select>
                    <div className="p-6 bg-slate-950 text-white rounded-3xl text-center">
                        <p className="text-[10px] uppercase text-slate-500 mb-1">Active Symbol</p>
                        <p className="text-5xl font-black">{config.currency_symbol}</p>
                    </div>
                </section>
                <section className="bg-white p-10 rounded-[3.5rem] shadow-xl border border-slate-100 col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="flex items-center gap-3 text-blue-500 font-black text-xs uppercase tracking-widest col-span-2"><Clock size={20}/> Business Hours</div>
                    <input type="time" className="w-full p-5 bg-slate-50 rounded-2xl font-black border-none" value={config.opening_time || ''} onChange={e => setConfig({...config, opening_time: e.target.value})} />
                    <input type="time" className="w-full p-5 bg-slate-50 rounded-2xl font-black border-none" value={config.closing_time || ''} onChange={e => setConfig({...config, closing_time: e.target.value})} />
                </section>
                <section className="bg-white p-10 rounded-[3.5rem] shadow-xl border border-slate-100 col-span-1 md:col-span-2 space-y-4">
                    <div className="flex items-center gap-3 text-rose-500 font-black text-xs uppercase tracking-widest"><TrendingUp size={20}/> Bill Settings</div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-[10px] uppercase font-black text-slate-400 ml-4">Tax %</label>
                            <input type="number" step="0.1" className="w-full p-5 bg-slate-50 rounded-2xl font-black border-none" value={config.tax_percent || 0} onChange={e => setConfig({...config, tax_percent: parseFloat(e.target.value)})} />
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}

// --- SHARED UI ---
function NavItem({ icon, label, active, onClick }: any) {
  return (
    <button onClick={onClick} className={`w-full flex items-center gap-5 px-8 py-5 rounded-[2rem] font-bold transition-all ${active ? 'bg-orange-600 text-white shadow-2xl scale-105' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}>
      {icon} <span className="uppercase text-[11px] font-black tracking-widest">{label}</span>
    </button>
  );
}

function StatCard({ title, value, icon, pulse }: any) {
  return (
    <div className="bg-white p-10 rounded-[3.5rem] border border-slate-100 shadow-xl group hover:-translate-y-2 transition-all">
      <div className="flex justify-between items-start mb-6">
        <div className="p-4 bg-slate-50 rounded-2xl text-slate-900 group-hover:bg-orange-500 group-hover:text-white transition-all">{icon}</div>
        <div className={`w-3 h-3 rounded-full ${pulse ? 'bg-rose-500 animate-ping' : 'bg-emerald-500'}`} />
      </div>
      <p className="text-slate-400 font-bold text-[10px] uppercase tracking-widest">{title}</p>
      <h3 className="text-5xl font-black mt-2 text-slate-950 italic tracking-tighter">{value}</h3>
    </div>
  );
}