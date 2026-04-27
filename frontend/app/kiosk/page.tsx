"use client";
import { useState, useEffect, useMemo } from 'react';
import { supabase } from '../../lib/supabase';
import { 
  ShoppingBag, Plus, Minus, X, ArrowRight, Leaf, 
  Drumstick, Utensils, MessageSquare, CheckCircle2, Loader2, 
  Search, Coffee, Pizza, CakeSlice, Package
} from 'lucide-react';

// --- TYPES ---
interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
  item_type: 'Veg' | 'Non-Veg';
  image_path: string | null;
  is_available: boolean;
}

interface CartItem extends Product {
  quantity: number;
  note: string;
}

// --- HELPER: CATEGORY FALLBACK ---
const CategoryFallback = ({ category }: { category: string }) => {
  const styles: any = {
    'Drinks': { bg: 'bg-blue-500', icon: <Coffee size={40} />, label: 'DRINK' },
    'Starter': { bg: 'bg-orange-500', icon: <Pizza size={40} />, label: 'STARTER' },
    'Main': { bg: 'bg-emerald-500', icon: <Utensils size={40} />, label: 'MAIN' },
    'Dessert': { bg: 'bg-pink-500', icon: <CakeSlice size={40} />, label: 'SWEET' },
    'default': { bg: 'bg-slate-400', icon: <Package size={40} />, label: 'ITEM' }
  };
  const config = styles[category] || styles['default'];
  return (
    <div className={`w-full h-full ${config.bg} flex flex-col items-center justify-center text-white gap-2`}>
      {config.icon}
      <span className="text-[10px] font-black tracking-widest">{config.label}</span>
    </div>
  );
};

export default function KioskPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [settings, setSettings] = useState<any>({ currency_symbol: '₹', store_name: 'Our Kitchen' });
  const [cart, setCart] = useState<CartItem[]>([]);
  const [activeCategory, setActiveCategory] = useState('All');
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [orderStatus, setOrderStatus] = useState<'idle' | 'loading' | 'success'>('idle');
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      const { data: p } = await supabase.from('products').select('*');
      const { data: s } = await supabase.from('restaurant_settings').select('*').limit(1).single();
      if (p) setProducts(p);
      if (s) setSettings(s);
    };
    fetchData();
  }, []);

  const categories = useMemo(() => ['All', ...new Set(products.map(p => p.category))], [products]);
  
  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      const matchesCategory = activeCategory === 'All' || p.category === activeCategory;
      const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [activeCategory, products, searchTerm]);

  const addToCart = (product: Product) => {
    if (!product.is_available) return; // Prevent adding unavailable items
    setCart(prev => {
      const exists = prev.find(item => item.id === product.id);
      if (exists) return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
      return [...prev, { ...product, quantity: 1, note: '' }];
    });
    if (cart.length === 0) setIsCartOpen(true);
  };

  const updateCartQuantity = (id: string, delta: number) => {
    setCart(prev => prev.map(item => item.id === id ? { ...item, quantity: Math.max(0, item.quantity + delta) } : item).filter(item => item.quantity > 0));
  };

  const updateItemNote = (id: string, note: string) => {
    setCart(prev => prev.map(item => item.id === id ? { ...item, note } : item));
  };

  const cartTotal = cart.reduce((sum, item) => sum + (Number(item.price || 0) * item.quantity), 0);

  const checkout = async () => {
    if (cart.length === 0) return;
    setOrderStatus('loading');
    const { data: order } = await supabase.from('orders').insert([{ total_amount: cartTotal, status: 'pending' }]).select().single();
    if (order) {
      const itemsToInsert = cart.map(item => ({
        order_id: order.id,
        product_id: item.id,
        quantity: item.quantity,
        price_at_sale: item.price,
      }));
      await supabase.from('order_items').insert(itemsToInsert);
      setOrderStatus('success');
      setCart([]);
      setTimeout(() => { setOrderStatus('idle'); setIsCartOpen(false); }, 4000);
    } else {
      setOrderStatus('idle');
    }
  };

  return (
    <main className="flex h-screen bg-[#FDFDFD] font-sans text-slate-900 overflow-hidden">
      
      {/* CATEGORY BAR */}
      <aside className="w-32 bg-white border-r border-slate-100 flex flex-col items-center py-10 gap-6">
        <div className="w-16 h-16 bg-orange-500 rounded-3xl flex items-center justify-center text-white shadow-lg mb-6">
          <Utensils size={32} />
        </div>
        <div className="flex-1 flex flex-col gap-4 overflow-y-auto">
          {categories.map(cat => (
            <button 
              key={cat} 
              onClick={() => setActiveCategory(cat)}
              className={`w-20 h-20 rounded-2xl flex flex-col items-center justify-center text-[10px] font-black uppercase transition-all ${activeCategory === cat ? 'bg-slate-900 text-white shadow-xl scale-105' : 'text-slate-400 hover:bg-slate-50'}`}
            >
              {cat}
            </button>
          ))}
        </div>
      </aside>

      {/* MENU GRID */}
      <section className="flex-1 overflow-y-auto p-12 pb-32">
        <header className="mb-10 flex justify-between items-center">
          <div>
            <h1 className="text-5xl font-black tracking-tighter uppercase italic">{settings.store_name}</h1>
            <p className="text-slate-400 font-bold uppercase text-[10px] tracking-widest">Select your items</p>
          </div>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
            <input 
              type="text" placeholder="Search..." value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-100 rounded-xl py-3 pl-12 pr-4 w-64 font-bold outline-none focus:ring-2 focus:ring-orange-500"
            />
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-8">
          {filteredProducts.map(p => (
            <ProductCard 
                key={p.id} 
                product={p} 
                symbol={settings.currency_symbol} 
                onAdd={() => addToCart(p)} 
            />
          ))}
        </div>
      </section>

      {/* CART DRAWER */}
      <aside className={`fixed inset-y-0 right-0 w-[450px] bg-white shadow-2xl border-l flex flex-col transition-transform duration-300 z-50 ${isCartOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="p-8 border-b flex justify-between items-center">
            <h2 className="text-2xl font-black uppercase italic">Your Order</h2>
            <button onClick={() => setIsCartOpen(false)} className="p-2 bg-slate-100 rounded-full hover:text-orange-500"><X size={20}/></button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {cart.map(item => (
                <div key={item.id} className="bg-slate-50 p-4 rounded-3xl border">
                    <div className="flex gap-4 mb-3">
                        <div className="w-16 h-16 rounded-xl overflow-hidden shrink-0">
                            {item.image_path ? <img src={item.image_path} className="w-full h-full object-cover" /> : <div className="w-full h-full bg-slate-200" />}
                        </div>
                        <div className="flex-1">
                            <p className="font-black text-sm uppercase">{item.name}</p>
                            <p className="text-orange-600 font-bold text-sm">{settings.currency_symbol}{item.price}</p>
                        </div>
                        <div className="flex items-center gap-2 bg-white rounded-xl p-1 border">
                            <button onClick={() => updateCartQuantity(item.id, -1)} className="p-1"><Minus size={14}/></button>
                            <span className="font-black text-sm">{item.quantity}</span>
                            <button onClick={() => updateCartQuantity(item.id, 1)} className="p-1"><Plus size={14}/></button>
                        </div>
                    </div>
                    <textarea 
                        placeholder="Add a note..." value={item.note}
                        onChange={(e) => updateItemNote(item.id, e.target.value)}
                        className="w-full bg-white border rounded-xl p-2 text-[10px] font-bold outline-none focus:border-orange-500 resize-none h-12"
                    />
                </div>
            ))}
        </div>

        <div className="p-8 bg-slate-950 text-white rounded-t-[3rem]">
            <div className="flex justify-between items-end mb-6">
                <span className="text-slate-500 font-black uppercase text-xs">Total</span>
                <span className="text-4xl font-black tracking-tighter">{settings.currency_symbol}{cartTotal.toFixed(2)}</span>
            </div>
            <button 
                onClick={checkout} disabled={cart.length === 0 || orderStatus !== 'idle'}
                className="w-full bg-orange-600 py-5 rounded-2xl font-black text-xl flex items-center justify-center gap-3 hover:bg-orange-500 active:scale-95 disabled:opacity-50"
            >
                {orderStatus === 'loading' ? <Loader2 className="animate-spin" /> : 'PLACE ORDER'}
            </button>
        </div>
      </aside>

      {/* FLOATING CART BUTTON */}
      <button onClick={() => setIsCartOpen(true)} className="fixed bottom-8 right-8 bg-slate-950 text-white px-8 py-5 rounded-3xl shadow-2xl flex items-center gap-4 hover:bg-orange-600 transition-all z-40">
        <ShoppingBag size={24} />
        <div className="text-left border-l border-white/20 pl-4">
            <p className="text-[10px] font-bold text-slate-500 uppercase leading-none mb-1">Items: {cart.length}</p>
            <p className="text-xl font-black leading-none">{settings.currency_symbol}{cartTotal.toFixed(2)}</p>
        </div>
      </button>

      {/* SUCCESS OVERLAY */}
      {orderStatus === 'success' && (
        <div className="fixed inset-0 bg-slate-950/95 z-[100] flex flex-col items-center justify-center text-white animate-in zoom-in">
            <CheckCircle2 size={100} className="text-emerald-500 mb-6" />
            <h2 className="text-6xl font-black uppercase italic">Done!</h2>
            <p className="text-slate-400 font-bold uppercase mt-2 tracking-widest">Wait for your number</p>
        </div>
      )}
    </main>
  );
}

// --- PRODUCT CARD SUB-COMPONENT ---
function ProductCard({ product, symbol, onAdd }: { product: Product, symbol: string, onAdd: any }) {
  const isOut = !product.is_available;

  return (
    <div className={`bg-white rounded-[2.5rem] p-4 border transition-all relative flex flex-col ${isOut ? 'opacity-60' : 'hover:shadow-xl'}`}>
      
      {/* IMAGE / FALLBACK AREA */}
      <div className="w-full h-48 rounded-3xl overflow-hidden mb-4 relative border shadow-inner">
        {isOut && (
          <div className="absolute inset-0 bg-slate-900/60 z-10 flex items-center justify-center">
            <span className="bg-white text-slate-900 px-4 py-1 rounded-full font-black uppercase text-[10px] tracking-tighter">Sold Out</span>
          </div>
        )}
        
        {product.image_path ? (
          <img src={product.image_path} className={`w-full h-full object-cover ${isOut ? 'grayscale' : ''}`} />
        ) : (
          <CategoryFallback category={product.category} />
        )}
        
        <div className="absolute top-3 left-3 px-2 py-1 rounded-lg bg-white/90 text-[8px] font-black uppercase shadow-sm flex items-center gap-1 z-20">
          {product.item_type === 'Veg' ? <Leaf size={10} className="text-emerald-600"/> : <Drumstick size={10} className="text-rose-600"/>}
          {product.item_type}
        </div>
      </div>
      
      {/* DETAILS */}
      <div className="px-1 flex-1 flex flex-col">
        <h3 className="font-black text-lg uppercase italic leading-tight mb-1 truncate">{product.name}</h3>
        <p className="text-slate-400 font-bold text-[9px] uppercase tracking-widest mb-4">{product.category}</p>
        
        <div className="mt-auto flex justify-between items-center">
          <p className="text-2xl font-black tracking-tighter">{symbol}{product.price}</p>
          <button 
            onClick={onAdd}
            disabled={isOut}
            className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all ${isOut ? 'bg-slate-100 text-slate-300 cursor-not-allowed' : 'bg-slate-950 text-white hover:bg-orange-600 active:scale-90 shadow-md'}`}
          >
            <Plus size={20} strokeWidth={3} />
          </button>
        </div>
      </div>
    </div>
  );
}